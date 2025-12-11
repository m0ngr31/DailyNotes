import os
import zipfile
import re
import time
import queue
import threading
from uuid import uuid4
import frontmatter
import datetime
import requests
from dateutil import rrule, tz
from urllib.parse import urlparse, parse_qs, quote

import json

from app import app, db, argon2
from app.models import (
    User,
    Note,
    Meta,
    Upload,
    ExternalCalendar,
    aes_encrypt,
    aes_encrypt_legacy_cfb,
    aes_encrypt_old,
    parse_tasks_with_columns,
    get_task_column,
)
from flask import (
    render_template,
    request,
    jsonify,
    abort,
    send_file,
    send_from_directory,
    Response,
    url_for,
    stream_with_context,
)
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from sqlalchemy import text
from werkzeug.utils import secure_filename


def _is_allowed_file(filename, mimetype):
    ext = os.path.splitext(filename)[1].lower().strip(".")
    allowed_extensions = app.config.get("ALLOWED_UPLOAD_EXTENSIONS", set())
    if ext not in allowed_extensions:
        return False

    if mimetype and mimetype.startswith("image/"):
        return True

    # Fallback to extension check if mimetype is missing/incorrect
    return ext in allowed_extensions


def parse_search_query(query_string):
    """
    Parse a search query string into structured filters.

    Supports syntax like:
        tag:work tag:meeting project:DN some text to search
        tag:"multi word tag" project:"my project" search terms

    Returns:
        dict with keys: tags (list), projects (list), text_terms (list)

    Logic:
        - Multiple tags = AND (note must have all specified tags)
        - Multiple projects = OR (note can be in any specified project)
        - Multiple text terms = AND (note must contain all words)
    """
    tags = []
    projects = []
    text_terms = []

    # Pattern to match tag:value, tag:"value with spaces", project:value, etc.
    # Also supports shorthand t: and p:
    pattern = r'(?:tag|t):"([^"]+)"|(?:tag|t):(\S+)|(?:project|p):"([^"]+)"|(?:project|p):(\S+)'

    # Find all tag/project matches and track their positions
    matches = list(re.finditer(pattern, query_string, re.IGNORECASE))

    for match in matches:
        # Groups: 1=tag quoted, 2=tag unquoted, 3=project quoted, 4=project unquoted
        if match.group(1):  # tag:"quoted value"
            tags.append(match.group(1))
        elif match.group(2):  # tag:value
            tags.append(match.group(2))
        elif match.group(3):  # project:"quoted value"
            projects.append(match.group(3))
        elif match.group(4):  # project:value
            projects.append(match.group(4))

    # Remove all matched patterns to get remaining text
    remaining = re.sub(pattern, "", query_string, flags=re.IGNORECASE)

    # Split remaining text into terms (handling multiple spaces)
    text_terms = [term.strip() for term in remaining.split() if term.strip()]

    return {"tags": tags, "projects": projects, "text_terms": text_terms}


def get_text_snippet(text, search_terms, context_chars=50):
    """
    Extract a snippet of text around the first matching search term.

    Args:
        text: The full text to search in
        search_terms: List of terms to find
        context_chars: Number of characters to show before/after match

    Returns:
        dict with 'snippet' (str) and 'highlights' (list of matched terms)
    """
    if not text or not search_terms:
        return {"snippet": "", "highlights": []}

    text_lower = text.lower()
    highlights = []
    first_match_pos = -1

    # Find all matching terms and the position of the first match
    for term in search_terms:
        term_lower = term.lower()
        pos = text_lower.find(term_lower)
        if pos != -1:
            highlights.append(term)
            if first_match_pos == -1 or pos < first_match_pos:
                first_match_pos = pos

    if first_match_pos == -1:
        # No match found, return beginning of text
        snippet = text[: context_chars * 2]
        if len(text) > context_chars * 2:
            snippet += "..."
        return {"snippet": snippet, "highlights": []}

    # Calculate snippet boundaries
    start = max(0, first_match_pos - context_chars)
    end = min(len(text), first_match_pos + context_chars + len(search_terms[0]))

    snippet = text[start:end]

    # Add ellipsis if we're not at the boundaries
    if start > 0:
        snippet = "..." + snippet
    if end < len(text):
        snippet = snippet + "..."

    return {"snippet": snippet, "highlights": highlights}


def _ensure_upload_table():
    try:
        Upload.__table__.create(db.engine, checkfirst=True)
    except Exception as e:
        # If migrations handle this, ignore failures (e.g., table already exists)
        import logging

        logging.getLogger(__name__).debug(f"Upload table creation skipped: {e}")


def _extract_upload_paths_from_text(text, username):
    """
    Returns a set of upload paths (/uploads/<username>/file.png) referenced in markdown.
    """
    if not text:
        return set()

    paths = set()
    # Markdown image or link pattern
    md_link_regex = re.compile(r"\[.*?\]\((.*?)\)")
    upload_prefix = f"/uploads/{username.lower()}/"

    for match in md_link_regex.finditer(text):
        url = match.group(1)
        if upload_prefix in url:
            # Normalize to just the /uploads/... portion
            idx = url.find(upload_prefix)
            if idx != -1:
                paths.add(url[idx:].split(")", 1)[0])

    # Bare URLs
    bare_regex = re.compile(rf"{re.escape(upload_prefix)}[^\s)]+")
    for match in bare_regex.finditer(text):
        paths.add(match.group(0))

    return paths


def _collect_referenced_uploads_for_user(user):
    """
    Scan all of a user's notes and return a set of upload paths referenced anywhere.
    Also updates last_seen_at for matched uploads.
    """
    referenced_paths = set()
    notes = Note.query.filter_by(user_id=user.uuid).all()
    for note in notes:
        referenced_paths.update(
            _extract_upload_paths_from_text(note.text, user.username)
        )

    if referenced_paths:
        now = datetime.datetime.utcnow()
        Upload.query.filter(
            Upload.user_id == user.uuid, Upload.path.in_(referenced_paths)
        ).update(
            {"last_seen_at": now},
            synchronize_session=False,
        )
        db.session.commit()

    return referenced_paths


_ICS_CACHE = {}
_ICS_CACHE_TTL_SECONDS = 300
_ICS_CACHE_MAX_SIZE = 100  # Limit cache size to prevent memory exhaustion

# SSE (Server-Sent Events) infrastructure for real-time sync
_SSE_CLIENTS = {}  # user_id -> list of queue.Queue
_SSE_CLIENTS_LOCK = threading.Lock()


def _sse_add_client(user_id, client_queue):
    """Register a new SSE client for a user."""
    with _SSE_CLIENTS_LOCK:
        if user_id not in _SSE_CLIENTS:
            _SSE_CLIENTS[user_id] = []
        _SSE_CLIENTS[user_id].append(client_queue)


def _sse_remove_client(user_id, client_queue):
    """Unregister an SSE client."""
    with _SSE_CLIENTS_LOCK:
        if user_id in _SSE_CLIENTS:
            try:
                _SSE_CLIENTS[user_id].remove(client_queue)
                if not _SSE_CLIENTS[user_id]:
                    del _SSE_CLIENTS[user_id]
            except ValueError:
                pass


def _sse_broadcast(user_id, event_type, data):
    """Broadcast an event to all connected clients for a user."""
    with _SSE_CLIENTS_LOCK:
        clients = _SSE_CLIENTS.get(user_id, [])
        for client_queue in clients:
            try:
                client_queue.put_nowait({"event": event_type, "data": data})
            except queue.Full:
                # Client queue is full, skip this message
                pass


def _normalize_calendar_url(raw_url):
    """
    Convert common Google Calendar embed URLs to ICS URLs.
    """
    if not raw_url:
        return raw_url

    parsed = urlparse(raw_url)
    if "google.com" in parsed.netloc and (
        "/calendar/embed" in parsed.path or "/calendar/r" in parsed.path
    ):
        qs = parse_qs(parsed.query)
        src = qs.get("src", [None])[0]
        if src:
            return f"https://calendar.google.com/calendar/ical/{quote(src)}/public/basic.ics"
    return raw_url


def _fetch_ics(url):
    now = time.time()
    cached = _ICS_CACHE.get(url)
    if cached and now - cached["ts"] < _ICS_CACHE_TTL_SECONDS:
        return cached["body"]

    try:
        # Basic SSRF protection: block localhost and private IPs
        parsed = urlparse(url)
        hostname = parsed.hostname
        if hostname:
            hostname_lower = hostname.lower()
            # Block localhost variants
            if hostname_lower in ("localhost", "127.0.0.1", "0.0.0.0", "::1"):
                return None
            # Block private IP ranges (basic check)
            if hostname_lower.startswith(
                (
                    "10.",
                    "172.16.",
                    "172.17.",
                    "172.18.",
                    "172.19.",
                    "172.20.",
                    "172.21.",
                    "172.22.",
                    "172.23.",
                    "172.24.",
                    "172.25.",
                    "172.26.",
                    "172.27.",
                    "172.28.",
                    "172.29.",
                    "172.30.",
                    "172.31.",
                    "192.168.",
                    "169.254.",
                )
            ):
                return None

        resp = requests.get(url, timeout=12, stream=True)
        if resp.status_code != 200:
            return None

        # Limit response size to 5MB to prevent memory exhaustion
        max_size = 5 * 1024 * 1024
        content_length = resp.headers.get("content-length")
        if content_length and int(content_length) > max_size:
            return None

        # Read response with size limit
        body = ""
        size = 0
        for chunk in resp.iter_content(chunk_size=8192, decode_unicode=True):
            size += len(chunk.encode("utf-8"))
            if size > max_size:
                return None
            body += chunk

        # Evict old entries if cache is too large
        if len(_ICS_CACHE) >= _ICS_CACHE_MAX_SIZE:
            # Remove oldest entries (simple FIFO)
            oldest_keys = sorted(_ICS_CACHE.keys(), key=lambda k: _ICS_CACHE[k]["ts"])[
                :10
            ]
            for key in oldest_keys:
                _ICS_CACHE.pop(key, None)

        _ICS_CACHE[url] = {"ts": now, "body": body}
        return body
    except (requests.RequestException, ValueError, OSError) as e:
        import logging

        logging.getLogger(__name__).debug(f"Failed to fetch ICS from {url}: {e}")
        return None


def _parse_ics_events(ics_text):
    if not ics_text:
        return []

    # Unfold lines (continuation lines start with space or tab)
    unfolded = []
    for line in ics_text.splitlines():
        if line.startswith((" ", "\t")) and unfolded:
            unfolded[-1] += line[1:]
        else:
            unfolded.append(line.strip())

    events = []
    current = {}
    collecting = False
    max_events = 1000  # Limit to prevent DoS

    for line in unfolded:
        if line.upper().startswith("BEGIN:VEVENT"):
            current = {}
            collecting = True
            continue
        if line.upper().startswith("END:VEVENT"):
            if collecting and current:
                events.append(current)
                # Limit number of events to prevent DoS
                if len(events) >= max_events:
                    break
            collecting = False
            current = {}
            continue

        if not collecting or ":" not in line:
            continue

        key_and_params, value = line.split(":", 1)
        key_parts = key_and_params.split(";")
        key = key_parts[0].upper()
        params = ";".join(key_parts[1:]) if len(key_parts) > 1 else ""
        current[key] = value
        if params:
            current[f"{key}_PARAMS"] = params

    return events


def _parse_ics_datetime(value, params):
    if not value:
        return None, False

    params_upper = params.upper() if params else ""
    if "VALUE=DATE" in params_upper:
        try:
            dt = datetime.datetime.strptime(value, "%Y%m%d")
            return dt, True
        except ValueError:
            return None, True

    for fmt in ("%Y%m%dT%H%M%SZ", "%Y%m%dT%H%M%S"):
        try:
            dt = datetime.datetime.strptime(value, fmt)
            return dt, False
        except ValueError:
            continue

    try:
        dt = datetime.datetime.fromisoformat(value)
        return dt, False
    except ValueError:
        return None, False


def _filter_events_for_date(events, target_date):
    target_start = datetime.datetime.combine(target_date, datetime.time.min)
    target_end = target_start + datetime.timedelta(days=1)
    matched = []

    for ev in events:
        raw_start = ev.get("DTSTART")
        raw_end = ev.get("DTEND")
        start_params = ev.get("DTSTART_PARAMS", "")
        end_params = ev.get("DTEND_PARAMS", "")
        rrule_str = ev.get("RRULE")

        start_dt, start_all_day = _parse_ics_datetime(raw_start, start_params)
        end_dt, end_all_day = _parse_ics_datetime(raw_end, end_params)

        if not start_dt:
            continue

        all_day = start_all_day or end_all_day

        if not end_dt:
            end_dt = start_dt + datetime.timedelta(days=1 if all_day else 1)

        duration = end_dt - start_dt

        # Handle recurrence with rrule
        if rrule_str:
            try:
                rule = rrule.rrulestr(rrule_str, dtstart=start_dt)
                # widen the window slightly to catch events starting just before the day and spanning into it
                occurrences = rule.between(
                    target_start - datetime.timedelta(days=1), target_end, inc=True
                )
            except (ValueError, TypeError) as e:
                import logging

                logging.getLogger(__name__).debug(
                    f"Failed to parse rrule '{rrule_str}': {e}"
                )
                occurrences = []

            for occ in occurrences:
                occ_start = occ
                occ_end = occ_start + duration
                range_start = (
                    datetime.datetime.combine(occ_start.date(), datetime.time.min)
                    if all_day
                    else occ_start
                )
                range_end = (
                    datetime.datetime.combine(occ_end.date(), datetime.time.min)
                    if all_day
                    else occ_end
                )
                overlaps = range_start < target_end and range_end > target_start
                if overlaps:
                    matched.append(
                        {
                            "summary": ev.get("SUMMARY", "(No title)"),
                            "description": ev.get("DESCRIPTION", ""),
                            "location": ev.get("LOCATION"),
                            "all_day": all_day,
                            "start": occ_start.isoformat(),
                            "end": occ_end.isoformat(),
                            "url": ev.get("URL") or None,
                        }
                    )
            continue

        range_start = (
            datetime.datetime.combine(start_dt.date(), datetime.time.min)
            if all_day
            else start_dt
        )
        range_end = (
            datetime.datetime.combine(end_dt.date(), datetime.time.min)
            if all_day
            else end_dt
        )

        overlaps = range_start < target_end and range_end > target_start
        if overlaps:
            matched.append(
                {
                    "summary": ev.get("SUMMARY", "(No title)"),
                    "description": ev.get("DESCRIPTION", ""),
                    "location": ev.get("LOCATION"),
                    "all_day": all_day,
                    "start": start_dt.isoformat(),
                    "end": end_dt.isoformat(),
                    "url": ev.get("URL") or None,
                }
            )

    return matched


def _ensure_calendar_token(user, regenerate=False):
    """
    Ensure the user has a calendar token; regenerate when requested.
    """
    if regenerate or not user.calendar_token:
        user.calendar_token = uuid4().hex
        db.session.add(user)
        db.session.commit()
    return user.calendar_token


def _escape_ics_text(value):
    """
    Escape characters per RFC5545 for ICS content.
    """
    if not value:
        return ""
    return (
        value.replace("\\", "\\\\")
        .replace(";", r"\;")
        .replace(",", r"\,")
        .replace("\n", r"\\n")
    )


def _markdown_to_plain(text, limit=800):
    """
    Convert markdown-ish text to a compact plain text summary for calendar clients.
    """
    if not text:
        return ""

    lines = []
    in_code_block = False

    for raw_line in text.splitlines():
        line = raw_line.rstrip()

        # Toggle fenced code blocks and skip the fence markers
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            continue

        if in_code_block:
            lines.append(line)
            continue

        stripped = line.strip()
        if not stripped:
            lines.append("")
            continue

        heading = re.match(r"^#{1,6}\s*(.+)", stripped)
        bullet = re.match(r"^[-*]\s+(.*)", stripped)
        numbered = re.match(r"^\d+\.\s+(.*)", stripped)

        if heading:
            lines.append(heading.group(1))
        elif bullet:
            lines.append(f"• {bullet.group(1)}")
        elif numbered:
            lines.append(f"• {numbered.group(1)}")
        else:
            lines.append(stripped)

    # Collapse excessive blank lines to max one consecutive empty line
    cleaned_lines = []
    empty_seen = False
    for l in lines:
        if l == "":
            if empty_seen:
                continue
            empty_seen = True
        else:
            empty_seen = False
        cleaned_lines.append(l)

    plain = "\n".join(cleaned_lines).strip()

    if limit and len(plain) > limit:
        cutoff = plain[: limit - 3]
        last_space = cutoff.rfind(" ")
        if last_space > 40:
            cutoff = cutoff[:last_space]
        plain = cutoff + "..."

    return plain


def _note_to_ics_event(note, base_url=None):
    """
    Convert a daily note into an all-day VEVENT block.
    """
    try:
        day = datetime.datetime.strptime(note.name, "%m-%d-%Y").date()
    except (ValueError, TypeError):
        return None

    dtstamp = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    start_str = day.strftime("%Y%m%d")
    end_str = (day + datetime.timedelta(days=1)).strftime("%Y%m%d")

    summary = _escape_ics_text(note.name or "Daily Note")

    description_source = ""
    try:
        parsed = frontmatter.loads(note.text or "")
        description_source = parsed.content.strip()
    except (ValueError, TypeError, AttributeError):
        description_source = (note.text or "").strip()

    description_plain = _markdown_to_plain(description_source, limit=800)

    footer = ""
    note_url = None
    if base_url:
        safe_base = base_url.rstrip("/")
        note_url = f"{safe_base}/date/{note.name}"
        footer = f"\n\nOpen in DailyNotes: {note_url}"

    description = _escape_ics_text(description_plain + footer)

    event_lines = [
        "BEGIN:VEVENT",
        f"UID:{note.uuid}@dailynotes",
        f"DTSTAMP:{dtstamp}",
        f"DTSTART;VALUE=DATE:{start_str}",
        f"DTEND;VALUE=DATE:{end_str}",
        f"SUMMARY:{summary}",
        f"DESCRIPTION:{description}",
    ]

    if note_url:
        event_lines.append(f"URL:{_escape_ics_text(note_url)}")

    event_lines.append("END:VEVENT")

    return "\r\n".join(event_lines)


@app.route("/health", methods=["GET"])
def health_check():
    """Simple health check endpoint for Docker healthcheck"""
    try:
        # Test database connection
        db.session.execute(text("SELECT 1"))
        return jsonify({"status": "healthy", "database": "ok"}), 200
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 503


@app.route("/api/sign-up", methods=["POST"])
def sign_up():
    if app.config["PREVENT_SIGNUPS"]:
        abort(400)

    req = request.get_json()
    username = req.get("username")
    password = req.get("password")

    if not username or not password:
        abort(400)

    password_hash = argon2.generate_password_hash(password)

    new_user = User(username=username.lower(), password_hash=password_hash)
    db.session.add(new_user)
    db.session.commit()

    access_token = create_access_token(identity=username)
    return jsonify(access_token=access_token), 200


@app.route("/api/login", methods=["POST"])
def login():
    req = request.get_json()
    username = req.get("username")
    password = req.get("password")

    if not username or not password:
        abort(400)

    user = User.query.filter_by(username=username.lower()).first()

    if not user:
        return jsonify({"msg": "Bad username or password"}), 401

    if not argon2.check_password_hash(user.password_hash, password):
        return jsonify({"msg": "Bad username or password"}), 401

    access_token = create_access_token(identity=username)
    return jsonify(access_token=access_token), 200


@app.route("/api/save_day", methods=["PUT"])
@jwt_required()
def save_day():
    req = request.get_json()
    title = req.get("title")
    data = req.get("data", "")

    if not title:
        abort(400)

    username = get_jwt_identity()

    if not username:
        abort(401)

    user = User.query.filter_by(username=username.lower()).first()

    if not user:
        abort(400)

    # Try to find existing note with legacy CFB encryption (most common for existing data)
    enc_date = aes_encrypt_legacy_cfb(title)
    note = user.notes.filter_by(title=enc_date).first()

    if not note:
        # Check legacy ECB encryption
        enc_date = aes_encrypt_old(title)
        note = user.notes.filter_by(title=enc_date).first()

    if not note:
        # Create new note (will be encrypted with new v2 format)
        note = Note(user_id=user.uuid, name=title, text=data, is_date=True)
    else:
        note.text = data

    db.session.add(note)
    db.session.flush()
    db.session.commit()

    # Update upload references for this user based on all notes
    _collect_referenced_uploads_for_user(user)

    # Broadcast SSE event for real-time sync
    _sse_broadcast(
        str(user.uuid),
        "note_updated",
        {
            "note_uuid": str(note.uuid),
            "is_date": True,
            "title": note.name,
        },
    )

    return jsonify(note=note.serialize), 200


@app.route("/api/create_note", methods=["POST"])
@jwt_required()
def create_note():
    req = request.get_json()
    data = req.get("data", "")

    if not data:
        abort(400)

    username = get_jwt_identity()

    if not username:
        abort(401)

    user = User.query.filter_by(username=username.lower()).first()

    if not user:
        abort(400)

    note = Note(user_id=user.uuid, text=data)

    db.session.add(note)
    db.session.flush()
    db.session.commit()

    # Update upload references for this user based on all notes
    _collect_referenced_uploads_for_user(user)

    # Broadcast SSE event for real-time sync
    _sse_broadcast(
        str(user.uuid),
        "note_updated",
        {
            "note_uuid": str(note.uuid),
            "is_date": False,
            "title": note.name,
        },
    )

    return jsonify(note=note.serialize), 200


@app.route("/api/save_task", methods=["PUT"])
@jwt_required()
def save_task():
    """
    Update a task's checkbox status by rewriting the markdown.

    Request body:
        - uuid: Task UUID
        - name: New task line (e.g., "- [x] Task text")

    This will update the task in the note markdown.
    """
    req = request.get_json()
    uuid = req.get("uuid")
    name = req.get("name")

    if not uuid or not name:
        abort(400)

    username = get_jwt_identity()

    if not username:
        abort(401)

    user = User.query.filter_by(username=username.lower()).first()

    if not user:
        abort(400)

    task = user.meta.filter_by(uuid=uuid).first()

    if not task:
        abort(400)

    # Get the note containing this task
    note = Note.query.get(task.note_id)

    if not note:
        abort(404)

    # Get the old task line from the note
    old_task_line = task.name

    # Update the note content
    if old_task_line not in note.text:
        # Task line not found in note - may have been modified externally
        abort(400)

    # Replace the old task line with the new one
    new_text = note.text.replace(old_task_line, name, 1)
    note.text = new_text

    # The task.name will be updated automatically by the after_change_note hook
    # when the note is committed, but we update it here too for consistency
    task.name = name

    # Capture values before commit (task may be expired after commit due to note hooks)
    user_uuid = str(user.uuid)
    note_uuid = str(note.uuid)
    task_uuid_str = str(task.uuid)

    db.session.add(note)
    db.session.add(task)
    db.session.flush()
    db.session.commit()

    # Broadcast SSE event for real-time sync
    _sse_broadcast(
        user_uuid,
        "task_updated",
        {
            "note_uuid": note_uuid,
            "task_uuid": task_uuid_str,
            "task_name": name,
        },
    )

    return jsonify(note_uuid=note_uuid), 200


@app.route("/api/save_note", methods=["PUT"])
@jwt_required()
def save_note():
    req = request.get_json()
    uuid = req.get("uuid")
    data = req.get("data", "")

    if not uuid:
        abort(400)

    username = get_jwt_identity()

    if not username:
        abort(401)

    user = User.query.filter_by(username=username.lower()).first()

    if not user:
        abort(400)

    note = user.notes.filter_by(uuid=uuid).first()

    if not note:
        abort(400)

    note.text = data

    db.session.add(note)
    db.session.flush()
    db.session.commit()

    # Broadcast SSE event for real-time sync
    _sse_broadcast(
        str(user.uuid),
        "note_updated",
        {
            "note_uuid": str(note.uuid),
            "is_date": note.is_date,
            "title": note.name,
        },
    )

    return jsonify(note=note.serialize), 200


@app.route("/api/delete_note/<uuid>", methods=["DELETE"])
@jwt_required()
def delete_note(uuid):
    if not uuid:
        abort(400)

    username = get_jwt_identity()

    if not username:
        abort(401)

    user = User.query.filter_by(username=username.lower()).first()

    if not user:
        abort(400)

    note = user.notes.filter_by(uuid=uuid).first()

    if not note:
        abort(400)

    db.session.delete(note)
    db.session.commit()

    return jsonify({}), 200


@app.route("/api/refresh_jwt", methods=["GET"])
@jwt_required()
def refresh_jwt():
    username = get_jwt_identity()

    if not username:
        abort(401)

    access_token = create_access_token(identity=username)
    return jsonify(token=access_token), 200


@app.route("/api/calendar_token", methods=["GET", "POST", "DELETE"])
@jwt_required()
def calendar_token():
    """
    Return, generate, rotate, or disable the per-user ICS feed token and URL.
    """
    username = get_jwt_identity()

    if not username:
        abort(401)

    user = User.query.filter_by(username=username.lower()).first()

    if not user:
        abort(400)

    if request.method == "DELETE":
        user.calendar_token = None
        db.session.add(user)
        db.session.commit()
        return jsonify({"token": None, "ics_url": None}), 200

    if request.method == "POST":
        token = _ensure_calendar_token(user, regenerate=True)
    else:
        token = user.calendar_token

    ics_url = url_for("calendar_feed", token=token, _external=True) if token else None

    return jsonify({"token": token, "ics_url": ics_url}), 200


@app.route("/api/external_calendars", methods=["GET", "POST"])
@jwt_required()
def external_calendars():
    """
    List or add external ICS calendars for the user.
    """
    username = get_jwt_identity()
    user = User.query.filter_by(username=username.lower()).first()

    if not user:
        abort(400)

    if request.method == "GET":
        calendars = [c.serialize for c in user.external_calendars.all()]
        return jsonify({"calendars": calendars}), 200

    req = request.get_json() or {}
    name = (req.get("name") or "").strip()
    url = (req.get("url") or "").strip()
    color = (req.get("color") or "").strip() or None

    if not name or not url:
        return jsonify({"error": "Name and URL are required"}), 400

    if not url.lower().startswith(("http://", "https://")):
        return jsonify({"error": "URL must start with http:// or https://"}), 400

    cal = ExternalCalendar(user_id=user.uuid, name=name, url=url, color=color)
    db.session.add(cal)
    db.session.commit()

    return jsonify({"calendar": cal.serialize}), 200


@app.route("/api/external_calendars/<uuid>", methods=["DELETE"])
@jwt_required()
def delete_external_calendar(uuid):
    username = get_jwt_identity()
    user = User.query.filter_by(username=username.lower()).first()

    if not user:
        abort(400)

    cal = user.external_calendars.filter_by(uuid=uuid).first()
    if not cal:
        abort(404)

    db.session.delete(cal)
    db.session.commit()
    return jsonify({}), 200


@app.route("/api/external_events", methods=["GET"])
@jwt_required()
def external_events():
    """
    Return events from all connected external calendars for a given date (MM-dd-yyyy).
    """
    date = request.args.get("date")
    if not date:
        abort(400)

    try:
        target_date = datetime.datetime.strptime(date, "%m-%d-%Y").date()
    except Exception:
        abort(400)

    username = get_jwt_identity()
    user = User.query.filter_by(username=username.lower()).first()

    if not user:
        abort(400)

    events = []
    statuses = []
    for cal in user.external_calendars.all():
        normalized_url = _normalize_calendar_url(cal.url)
        ics_body = _fetch_ics(normalized_url)
        if not ics_body:
            statuses.append({"name": cal.name, "url": cal.url, "error": "fetch_failed"})
            continue
        parsed = _parse_ics_events(ics_body)
        filtered = _filter_events_for_date(parsed, target_date)
        statuses.append({"name": cal.name, "url": cal.url, "events": len(filtered)})
        for ev in filtered:
            events.append(
                {
                    "title": ev.get("summary") or "(No title)",
                    "all_day": ev.get("all_day", False),
                    "start": ev.get("start"),
                    "end": ev.get("end"),
                    "source": cal.name,
                    "color": cal.color,
                    "location": ev.get("location"),
                    "url": ev.get("url") or cal.url,
                }
            )

    # Sort by start time, all-day first
    def sort_key(ev):
        allday_prefix = "0" if ev.get("all_day") else "1"
        return f"{allday_prefix}-{ev.get('start') or ''}"

    events = sorted(events, key=sort_key)

    return jsonify({"events": events, "status": statuses}), 200


@app.route("/api/calendar.ics", methods=["GET"])
def calendar_feed():
    """
    Public ICS feed for a user's daily notes. Access is gated by a token query param.
    """
    token = request.args.get("token")

    if not token:
        abort(404)

    user = User.query.filter_by(calendar_token=token).first()

    if not user:
        abort(404)

    base_url = request.url_root.rstrip("/")

    events = []
    for note in user.notes.filter_by(is_date=True).all():
        event_block = _note_to_ics_event(note, base_url=base_url)
        if event_block:
            events.append(event_block)

    calendar_lines = [
        "BEGIN:VCALENDAR",
        "PRODID:-//DailyNotes//Calendar Feed//EN",
        "VERSION:2.0",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:Daily Notes",
    ]

    if events:
        calendar_lines.extend(events)

    calendar_lines.append("END:VCALENDAR")

    payload = "\r\n".join(calendar_lines) + "\r\n"
    return Response(payload, mimetype="text/calendar")


@app.route("/api/note", methods=["GET"])
@jwt_required()
def get_note():
    uuid = request.args.get("uuid")

    if not uuid:
        abort(400)

    username = get_jwt_identity()
    user = User.query.filter_by(username=username.lower()).first()

    if not user:
        abort(400)

    note = user.notes.filter_by(uuid=uuid).first()

    if not note:
        abort(400)

    return jsonify(note=note.serialize), 200


@app.route("/api/date", methods=["GET"])
@jwt_required()
def get_date():
    date = request.args.get("date")

    if not date:
        abort(400)

    username = get_jwt_identity()
    user = User.query.filter_by(username=username.lower()).first()

    if not user:
        abort(400)

    ret_note = {
        "title": date,
        "data": "---\ntags: \nprojects: \n---\n\n",
        "is_date": True,
        "user_id": user.uuid,
    }

    # Try to find existing note with legacy CFB encryption (most common for existing data)
    date_enc = aes_encrypt_legacy_cfb(date)
    note = user.notes.filter_by(title=date_enc, is_date=True).first()

    if not note:
        # Check legacy ECB encryption
        date_enc = aes_encrypt_old(date)
        note = user.notes.filter_by(title=date_enc, is_date=True).first()

    if note:
        ret_note = note.serialize

    return jsonify(day=ret_note), 200


@app.route("/api/events", methods=["GET"])
@jwt_required()
def cal_events():
    username = get_jwt_identity()
    user = User.query.filter_by(username=username.lower()).first()

    if not user:
        abort(400)

    # TODO: Only do current month or something
    notes = user.notes.filter_by(is_date=True).all()

    return jsonify(events=[x.name for x in notes]), 200


@app.route("/api/sidebar", methods=["GET"])
@jwt_required()
def sidebar_data():
    username = get_jwt_identity()
    user = User.query.filter_by(username=username.lower()).first()

    if not user:
        abort(400)

    notes = sorted(
        [a.serialize for a in user.notes.filter_by(is_date=False).all()],
        key=lambda note: note["title"].lower(),
    )
    tags = sorted(
        set([a.name for a in user.meta.filter_by(kind="tag").all()]),
        key=lambda s: s.lower(),
    )
    projects = sorted(
        set([a.name for a in user.meta.filter_by(kind="project").all()]),
        key=lambda s: s.lower(),
    )
    tasks = sorted(
        [a.serialize for a in user.meta.filter_by(kind="task").all()],
        key=lambda task: task["note_id"],
    )
    auto_save = user.auto_save
    vim_mode = user.vim_mode
    kanban_enabled = user.kanban_enabled or False

    # Parse kanban_columns from JSON string
    try:
        kanban_columns = (
            json.loads(user.kanban_columns) if user.kanban_columns else ["todo", "done"]
        )
    except (json.JSONDecodeError, TypeError):
        kanban_columns = ["todo", "done"]

    return (
        jsonify(
            tags=tags,
            projects=projects,
            notes=notes,
            tasks=tasks,
            auto_save=auto_save,
            vim_mode=vim_mode,
            kanban_enabled=kanban_enabled,
            kanban_columns=kanban_columns,
        ),
        200,
    )


@app.route("/api/toggle_auto_save", methods=["POST"])
@jwt_required()
def toggle_auto_save():
    req = request.get_json()
    auto_save = req.get("auto_save", False)

    username = get_jwt_identity()

    if not username:
        abort(401)

    user = User.query.filter_by(username=username.lower()).first()

    if not user:
        abort(400)

    user.auto_save = auto_save

    db.session.add(user)
    db.session.flush()
    db.session.commit()

    return jsonify({}), 200


@app.route("/api/toggle_vim_mode", methods=["POST"])
@jwt_required()
def toggle_vim_mode():
    req = request.get_json()
    vim_mode = req.get("vim_mode", False)

    username = get_jwt_identity()

    if not username:
        abort(401)

    user = User.query.filter_by(username=username.lower()).first()

    if not user:
        abort(400)

    user.vim_mode = vim_mode

    db.session.add(user)
    db.session.flush()
    db.session.commit()

    return jsonify({}), 200


@app.route("/api/settings", methods=["GET"])
@jwt_required()
def get_settings():
    """Get all user settings including kanban configuration."""
    username = get_jwt_identity()

    if not username:
        abort(401)

    user = User.query.filter_by(username=username.lower()).first()

    if not user:
        abort(400)

    # Parse kanban_columns from JSON string
    try:
        kanban_columns = (
            json.loads(user.kanban_columns) if user.kanban_columns else ["todo", "done"]
        )
    except (json.JSONDecodeError, TypeError):
        kanban_columns = ["todo", "done"]

    return (
        jsonify(
            auto_save=user.auto_save or False,
            vim_mode=user.vim_mode or False,
            kanban_enabled=user.kanban_enabled or False,
            kanban_columns=kanban_columns,
        ),
        200,
    )


@app.route("/api/settings", methods=["PUT"])
@jwt_required()
def update_settings():
    """Update user settings. Only updates fields that are provided."""
    req = request.get_json()

    username = get_jwt_identity()

    if not username:
        abort(401)

    user = User.query.filter_by(username=username.lower()).first()

    if not user:
        abort(400)

    # Update only provided fields
    if "auto_save" in req:
        user.auto_save = req["auto_save"]

    if "vim_mode" in req:
        user.vim_mode = req["vim_mode"]

    if "kanban_enabled" in req:
        user.kanban_enabled = req["kanban_enabled"]

    if "kanban_columns" in req:
        columns = req["kanban_columns"]
        if isinstance(columns, list):
            # Validate columns - must be non-empty strings
            valid_columns = [
                c.strip() for c in columns if isinstance(c, str) and c.strip()
            ]
            if valid_columns:
                user.kanban_columns = json.dumps(valid_columns)

    db.session.add(user)
    db.session.flush()
    db.session.commit()

    # Return updated settings
    try:
        kanban_columns = (
            json.loads(user.kanban_columns) if user.kanban_columns else ["todo", "done"]
        )
    except (json.JSONDecodeError, TypeError):
        kanban_columns = ["todo", "done"]

    return (
        jsonify(
            auto_save=user.auto_save or False,
            vim_mode=user.vim_mode or False,
            kanban_enabled=user.kanban_enabled or False,
            kanban_columns=kanban_columns,
        ),
        200,
    )


@app.route("/api/task_column", methods=["PUT"])
@jwt_required()
def update_task_column():
    """
    Update a task's kanban column by rewriting the markdown.

    Request body:
        - uuid: Task UUID
        - column: New column name

    This will update the task's :column: syntax in the note markdown.
    """
    req = request.get_json()
    task_uuid = req.get("uuid")
    new_column = req.get("column")

    if not task_uuid or not new_column:
        abort(400)

    username = get_jwt_identity()

    if not username:
        abort(401)

    user = User.query.filter_by(username=username.lower()).first()

    if not user:
        abort(400)

    # Find the task
    task = user.meta.filter_by(uuid=task_uuid, kind="task").first()

    if not task:
        abort(404)

    # Get the note containing this task
    note = Note.query.get(task.note_id)

    if not note:
        abort(404)

    # Get the current task text (the full line like "- [ ] Task text :old_column:")
    # Strip to handle legacy data that may have captured trailing newlines
    old_task_line = task.name.rstrip("\n\r")

    # Parse the task to understand its structure
    parsed = parse_tasks_with_columns(old_task_line)

    if not parsed:
        # Task line doesn't match expected pattern, abort
        abort(400)

    full_match, is_completed, task_text, old_column = parsed[0]

    # Auto-update checkbox based on column:
    # - Moving to "todo" should uncheck the task
    # - Moving to "done" should check the task
    if new_column == "todo":
        is_completed = False
    elif new_column == "done":
        is_completed = True

    # Build the new task line
    checkbox = "[x]" if is_completed else "[ ]"

    # Determine if we need to add >>column syntax
    # If column is "todo" and unchecked, or "done" and checked, we can omit it
    if (new_column == "todo" and not is_completed) or (
        new_column == "done" and is_completed
    ):
        new_task_line = f"- {checkbox} {task_text}"
    else:
        new_task_line = f"- {checkbox} {task_text} >>{new_column}"

    # Update the note content
    if old_task_line not in note.text:
        # Task line not found in note - may have been modified
        abort(400)

    new_text = note.text.replace(
        old_task_line, new_task_line, 1
    )  # Replace only first occurrence

    # Update task name to match the new line BEFORE updating the note
    # This ensures the after_change_note hook sees the task as unchanged (same name)
    # and won't delete/recreate it with a new UUID
    task.name = new_task_line
    task.task_column = new_column
    db.session.add(task)
    db.session.flush()  # Flush task update first

    # Now update the note - the hook will see the matching task name
    note.text = new_text

    # Capture values before commit
    user_uuid = str(user.uuid)
    note_uuid = str(note.uuid)
    task_uuid_str = str(task_uuid)  # Use the input parameter, not task.uuid

    db.session.add(note)
    db.session.flush()
    db.session.commit()

    # Broadcast SSE event for real-time sync
    _sse_broadcast(
        user_uuid,
        "task_column_updated",
        {
            "note_uuid": note_uuid,
            "task_uuid": task_uuid_str,
            "old_task": old_task_line,
            "new_task": new_task_line,
            "column": new_column,
        },
    )

    return (
        jsonify(
            note_uuid=note_uuid,
            old_task=old_task_line,
            new_task=new_task_line,
        ),
        200,
    )


@app.route("/api/search", methods=["POST"])
@jwt_required()
def search():
    req = request.get_json()

    # Support both old format (selected + search) and new format (query)
    query_string = req.get("query", "")
    selected_search = req.get("selected", "")
    search_string = req.get("search", "")

    username = get_jwt_identity()

    if not username:
        abort(401)

    user = User.query.filter_by(username=username.lower()).first()

    if not user:
        abort(400)

    # Determine if using new syntax-based search or legacy dropdown search
    if query_string:
        # New syntax-based search
        parsed = parse_search_query(query_string)
        tags_filter = parsed["tags"]
        projects_filter = parsed["projects"]
        text_terms = parsed["text_terms"]
    elif selected_search and search_string:
        # Legacy dropdown-based search (backward compatibility)
        if selected_search not in ["project", "tag", "search"]:
            abort(400)

        tags_filter = [search_string] if selected_search == "tag" else []
        projects_filter = [search_string] if selected_search == "project" else []
        text_terms = [search_string] if selected_search == "search" else []
    else:
        abort(400)

    # Start with all notes
    all_notes = user.notes.all()
    matched_note_ids = set(note.uuid for note in all_notes)

    # Filter by tags (AND logic - must have ALL specified tags)
    # Supports nested tags: searching for "home" matches "home", "home/family", "home/tech", etc.
    if tags_filter:
        all_tags = user.meta.filter_by(kind="tag").all()
        for required_tag in tags_filter:
            tag_note_ids = set()
            required_tag_lower = required_tag.lower()
            for tag in all_tags:
                tag_name_lower = tag.name.lower()
                # Match exact tag or nested children (prefix match with /)
                if tag_name_lower == required_tag_lower or tag_name_lower.startswith(
                    required_tag_lower + "/"
                ):
                    tag_note_ids.add(tag.note_id)
            matched_note_ids &= tag_note_ids

    # Filter by projects (OR logic - can be in ANY specified project)
    if projects_filter:
        all_projects = user.meta.filter_by(kind="project").all()
        project_note_ids = set()
        for project in all_projects:
            for proj_filter in projects_filter:
                if proj_filter.lower() == project.name.lower():
                    project_note_ids.add(project.note_id)
        matched_note_ids &= project_note_ids

    # Filter by text terms (AND logic - must contain ALL terms)
    if text_terms:
        text_matched_ids = set()
        for note in all_notes:
            if note.uuid not in matched_note_ids:
                continue
            note_text_lower = note.text.lower()
            if all(term.lower() in note_text_lower for term in text_terms):
                text_matched_ids.add(note.uuid)
        matched_note_ids &= text_matched_ids

    # Fetch and serialize matched notes
    filtered_notes = Note.query.filter(Note.uuid.in_(matched_note_ids)).all()
    notes = []

    for note in filtered_notes:
        cleaned_note = note.serialize
        cleaned_note["tags"] = sorted(
            set([x.name for x in note.meta.filter_by(kind="tag").all()]),
            key=lambda s: s.lower(),
        )
        cleaned_note["projects"] = sorted(
            set([x.name for x in note.meta.filter_by(kind="project").all()]),
            key=lambda s: s.lower(),
        )

        # Add snippet with highlights if text search was performed
        if text_terms:
            snippet_data = get_text_snippet(note.text, text_terms)
            cleaned_note["snippet"] = snippet_data["snippet"]
            cleaned_note["highlights"] = snippet_data["highlights"]

        notes.append(cleaned_note)

    sorted_nodes = sorted(notes, key=lambda s: s["title"].lower())

    return jsonify(notes=sorted_nodes), 200


@app.route("/api/export")
@jwt_required()
def export():
    username = get_jwt_identity()
    user = User.query.filter_by(username=username.lower()).first()

    if not user:
        abort(400)

    zip_location = app.config["EXPORT_FILE"]
    zf = zipfile.ZipFile(zip_location, mode="w")
    os.chmod(zip_location, 0o755)
    notes = user.notes
    for note in notes:
        ret_note = note.serialize
        zf.writestr(ret_note["title"] + ".md", ret_note["data"], zipfile.ZIP_DEFLATED)
    zf.close()

    rval = send_file(zip_location, as_attachment=True)
    os.remove(zip_location)
    return rval


@app.route("/api/import", methods=["POST"])
@jwt_required()
def import_notes():
    import re
    import os
    from app.models import aes_encrypt

    username = get_jwt_identity()
    user = User.query.filter_by(username=username.lower()).first()

    if not user:
        abort(400)

    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    if not file.filename.endswith(".zip"):
        return jsonify({"error": "Only ZIP files are supported"}), 400

    import_location = None

    try:
        # Save uploaded file temporarily
        import_location = app.config["EXPORT_FILE"].replace("export.zip", "import.zip")
        file.save(import_location)

        # Open and process the ZIP file
        imported_count = 0
        skipped_count = 0
        error_count = 0

        with zipfile.ZipFile(import_location, "r") as zf:
            for file_info in zf.filelist:
                filename = file_info.filename

                # Skip directories and non-markdown files
                if file_info.is_dir() or not filename.endswith(".md"):
                    continue

                # Skip hidden files and system files
                if os.path.basename(filename).startswith("."):
                    continue

                try:
                    # Read markdown content
                    content = zf.read(filename).decode("utf-8")

                    # Extract just the filename without path and extension
                    base_filename = os.path.basename(filename)[:-3]

                    # Parse frontmatter to determine if it's a daily note
                    data = frontmatter.loads(content)
                    is_date = False
                    note_title = base_filename

                    # Check if this is a daily note by title format (MM-dd-yyyy)
                    date_pattern = r"^\d{2}-\d{2}-\d{4}$"
                    if re.match(date_pattern, base_filename):
                        is_date = True

                        # Check if daily note already exists for this date
                        # Query all daily notes for this user and check decrypted titles
                        existing_daily_notes = Note.query.filter_by(
                            user_id=user.uuid, is_date=True
                        ).all()
                        note_exists = False
                        for existing in existing_daily_notes:
                            if existing.name == base_filename:
                                note_exists = True
                                break

                        if note_exists:
                            skipped_count += 1
                            continue

                    # Extract title from frontmatter if available
                    if (
                        isinstance(data.get("title"), str)
                        and len(data.get("title")) > 0
                    ):
                        note_title = data.get("title")

                    # Create new note
                    note = Note()
                    note.user_id = user.uuid
                    note.text = content
                    note.name = note_title
                    note.is_date = is_date

                    db.session.add(note)
                    imported_count += 1

                except Exception as e:
                    print(f"Error importing {filename}: {str(e)}")
                    import traceback

                    traceback.print_exc()
                    error_count += 1
                    continue

        # Commit all changes
        db.session.commit()

        # Clean up temporary file
        if import_location and os.path.exists(import_location):
            os.remove(import_location)

        return (
            jsonify(
                {
                    "message": "Import completed",
                    "imported": imported_count,
                    "skipped": skipped_count,
                    "errors": error_count,
                }
            ),
            200,
        )

    except zipfile.BadZipFile:
        if import_location and os.path.exists(import_location):
            os.remove(import_location)
        return jsonify({"error": "Invalid ZIP file"}), 400
    except Exception as e:
        print(f"Import error: {str(e)}")
        import traceback

        traceback.print_exc()
        if import_location and os.path.exists(import_location):
            os.remove(import_location)
        return jsonify({"error": f"Import failed: {str(e)}"}), 500


@app.route("/api/upload", methods=["POST"])
@jwt_required()
def upload_file():
    username = get_jwt_identity()
    user = User.query.filter_by(username=username.lower()).first()

    if not user:
        abort(400)

    _ensure_upload_table()

    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    filename = secure_filename(file.filename)
    if not _is_allowed_file(filename, file.mimetype):
        return jsonify({"error": "Unsupported file type"}), 400

    max_size = app.config.get("MAX_UPLOAD_SIZE")
    try:
        file.stream.seek(0, os.SEEK_END)
        file_size = file.stream.tell()
        file.stream.seek(0)
    except (OSError, IOError) as e:
        import logging

        logging.getLogger(__name__).debug(f"Could not determine file size: {e}")
        file_size = 0

    if max_size and file_size and file_size > max_size:
        return jsonify({"error": "File too large"}), 413

    user_dir = os.path.join(app.config["UPLOAD_FOLDER"], username.lower())
    os.makedirs(user_dir, exist_ok=True)

    ext = os.path.splitext(filename)[1].lower()
    saved_name = f"{uuid4().hex}{ext}"
    file_path = os.path.join(user_dir, saved_name)

    file.save(file_path)

    relative_path = f"/uploads/{username.lower()}/{saved_name}"
    url_prefix = request.script_root or ""
    public_url = f"{url_prefix}{relative_path}"

    upload_row = Upload(
        user_id=user.uuid,
        filename=saved_name,
        path=relative_path,
        size=file_size if file_size else None,
        last_seen_at=datetime.datetime.utcnow(),
    )
    db.session.add(upload_row)
    db.session.commit()

    return (
        jsonify(
            {
                "url": public_url,
                "path": relative_path,
                "filename": saved_name,
                "uuid": str(upload_row.uuid),
            }
        ),
        200,
    )


@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


@app.route("/api/uploads/orphans", methods=["GET"])
@jwt_required()
def list_orphan_uploads():
    username = get_jwt_identity()
    user = User.query.filter_by(username=username.lower()).first()

    if not user:
        abort(400)

    _ensure_upload_table()
    referenced = _collect_referenced_uploads_for_user(user)
    uploads = Upload.query.filter_by(user_id=user.uuid).all()

    orphans = []
    for upload in uploads:
        if upload.path not in referenced:
            file_path = os.path.join(
                app.config["UPLOAD_FOLDER"], upload.path.replace("/uploads/", "")
            )
            size = upload.size
            if size is None and os.path.exists(file_path):
                size = os.path.getsize(file_path)
            orphans.append(
                {
                    "uuid": str(upload.uuid),
                    "filename": upload.filename,
                    "path": upload.path,
                    "size": size,
                    "created_at": upload.created_at,
                    "last_seen_at": upload.last_seen_at,
                }
            )

    return jsonify({"orphans": orphans, "count": len(orphans)}), 200


@app.route("/api/uploads/orphans/cleanup", methods=["POST"])
@jwt_required()
def cleanup_orphan_uploads():
    username = get_jwt_identity()
    user = User.query.filter_by(username=username.lower()).first()

    if not user:
        abort(400)

    _ensure_upload_table()
    referenced = _collect_referenced_uploads_for_user(user)
    uploads = Upload.query.filter_by(user_id=user.uuid).all()

    deleted = []
    for upload in uploads:
        if upload.path in referenced:
            continue

        file_path = os.path.join(
            app.config["UPLOAD_FOLDER"], upload.path.replace("/uploads/", "")
        )
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError as e:
                import logging

                logging.getLogger(__name__).warning(
                    f"Failed to delete orphan file {file_path}: {e}"
                )

        db.session.delete(upload)
        deleted.append(upload.path)

    db.session.commit()

    return jsonify({"deleted": deleted, "count": len(deleted)}), 200


@app.route("/api/events/stream", methods=["GET", "OPTIONS"])
def sse_stream():
    # Handle CORS preflight request
    if request.method == "OPTIONS":
        response = Response()
        response.headers["Access-Control-Allow-Origin"] = request.headers.get(
            "Origin", "*"
        )
        response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = (
            "Authorization, Content-Type, Accept"
        )
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Max-Age"] = "86400"
        return response

    # JWT validation for actual SSE request
    from flask_jwt_extended import verify_jwt_in_request

    try:
        verify_jwt_in_request()
    except Exception:
        abort(401)

    username = get_jwt_identity()

    if not username:
        abort(401)

    user = User.query.filter_by(username=username.lower()).first()

    if not user:
        abort(400)

    user_id = str(user.uuid)

    def generate():
        # Create a queue for this client
        client_queue = queue.Queue(maxsize=50)
        _sse_add_client(user_id, client_queue)

        try:
            # Send initial connection event
            yield f"event: connected\ndata: {json.dumps({'user': username})}\n\n"

            while True:
                try:
                    # Wait for messages with timeout to allow checking connection
                    message = client_queue.get(timeout=30)
                    event_type = message.get("event", "message")
                    data = message.get("data", {})
                    yield f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
                except queue.Empty:
                    # Send heartbeat to keep connection alive
                    yield f": heartbeat\n\n"
        except GeneratorExit:
            pass
        finally:
            _sse_remove_client(user_id, client_queue)

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
            "Connection": "keep-alive",
            # CORS headers for development (Vue dev server on different port)
            "Access-Control-Allow-Origin": request.headers.get("Origin", "*"),
            "Access-Control-Allow-Credentials": "true",
        },
    )


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def catch_all(path):
    return render_template("index.html")
