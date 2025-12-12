from app import app, db, Base, db_session
from app.model_types import GUID
from sqlalchemy import (
    Column,
    String,
    Boolean,
    Integer,
    DateTime,
    LargeBinary,
    ForeignKey,
    event,
    text,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm.attributes import InstrumentedAttribute
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import binascii
import uuid
import frontmatter
import re
import datetime
import logging

logger = logging.getLogger(__name__)

# AES block size and IV size
AES_BLOCK_SIZE = 16
IV_SIZE = 16

# Magic bytes to identify new encryption format (random IV prepended)
# Using bytes that are unlikely to appear in old CFB-encrypted data
ENCRYPTION_V2_MARKER = b"\x00\x01\x02\x03"
MARKER_SIZE = len(ENCRYPTION_V2_MARKER)

_encryption_key = app.config["DB_ENCRYPTION_KEY"]

# Ensure key is bytes
if isinstance(_encryption_key, str):
    _encryption_key = _encryption_key.encode("utf-8")

# Pad or truncate key to 32 bytes for AES-256
_encryption_key = (_encryption_key + b"\0" * 32)[:32]

# Legacy IV derived from key (for backwards compatibility with old data)
_legacy_iv = _encryption_key[:16]


def aes_encrypt(data):
    """
    Encrypt data using AES-256-CFB with a random IV.

    Format: MARKER (4 bytes) + IV (16 bytes) + ciphertext

    This provides semantic security - encrypting the same plaintext
    twice produces different ciphertexts.
    """
    # Ensure data is bytes
    if isinstance(data, str):
        data = data.encode("utf-8")

    # Generate a random IV for each encryption
    iv = get_random_bytes(IV_SIZE)
    cipher = AES.new(_encryption_key, AES.MODE_CFB, iv)
    ciphertext = cipher.encrypt(data)

    # Prepend marker and IV to ciphertext for later extraction during decryption
    return ENCRYPTION_V2_MARKER + iv + ciphertext


def aes_encrypt_legacy_cfb(data):
    """
    Legacy CFB encryption with static IV - ONLY used for querying existing data.

    This produces deterministic ciphertext (same input = same output) which is
    needed to look up records by encrypted field values in the database.

    DO NOT use for storing new sensitive data - use aes_encrypt() instead.
    """
    # Ensure data is bytes
    if isinstance(data, str):
        data = data.encode("utf-8")

    cipher = AES.new(_encryption_key, AES.MODE_CFB, _legacy_iv)
    return cipher.encrypt(data)


def aes_encrypt_old(data):
    """
    Legacy ECB encryption - ONLY used for querying old encrypted data.
    DO NOT use for new encryptions. ECB mode is insecure.
    """
    # Ensure data is bytes
    if isinstance(data, str):
        data = data.encode("utf-8")

    cipher = AES.new(_encryption_key, AES.MODE_ECB)
    # Pad to block size
    padding_len = AES_BLOCK_SIZE - (len(data) % AES_BLOCK_SIZE)
    data = data + (b" " * padding_len)
    return binascii.hexlify(cipher.encrypt(data))


def _decrypt_v2(data):
    """
    Decrypt data encrypted with the new format (random IV).

    Expected format: MARKER (4 bytes) + IV (16 bytes) + ciphertext
    """
    # Extract IV and ciphertext (skip marker)
    iv = data[MARKER_SIZE : MARKER_SIZE + IV_SIZE]
    ciphertext = data[MARKER_SIZE + IV_SIZE :]

    cipher = AES.new(_encryption_key, AES.MODE_CFB, iv)
    return cipher.decrypt(ciphertext).decode("utf-8")


def _decrypt_legacy_cfb(data):
    """
    Decrypt data encrypted with legacy CFB mode (static IV derived from key).
    """
    cipher = AES.new(_encryption_key, AES.MODE_CFB, _legacy_iv)
    return cipher.decrypt(data).decode("utf-8")


def _decrypt_legacy_ecb(data):
    """
    Decrypt data encrypted with legacy ECB mode.
    """
    # Ensure data is bytes for unhexlify
    if isinstance(data, str):
        data = data.encode("utf-8")

    cipher = AES.new(_encryption_key, AES.MODE_ECB)
    return cipher.decrypt(binascii.unhexlify(data)).rstrip().decode("ascii")


def aes_decrypt(data):
    """
    Decrypt data, automatically detecting the encryption format.

    Supports three formats for backwards compatibility:
    1. New format (v2): MARKER + random IV + ciphertext
    2. Legacy CFB: ciphertext with static IV derived from key
    3. Legacy ECB: hex-encoded ciphertext with padding
    4. Unencrypted: plain text (returned as-is)
    """
    # From a new object (SQLAlchemy instrumented attribute)
    if type(data) is InstrumentedAttribute:
        return ""

    # Handle None or empty data
    if not data:
        return "" if data is None else data

    # Ensure data is bytes
    if isinstance(data, str):
        data = data.encode("utf-8")

    # Try new format first (check for marker)
    if data.startswith(ENCRYPTION_V2_MARKER) and len(data) > MARKER_SIZE + IV_SIZE:
        try:
            return _decrypt_v2(data)
        except (ValueError, UnicodeDecodeError) as e:
            logger.debug(f"V2 decryption failed, trying legacy formats: {e}")

    # Try legacy CFB format (static IV)
    try:
        decrypted = _decrypt_legacy_cfb(data)
        return decrypted
    except (ValueError, UnicodeDecodeError) as e:
        logger.debug(f"Legacy CFB decryption failed: {e}")

    # Try legacy ECB format
    try:
        return _decrypt_legacy_ecb(data)
    except (ValueError, UnicodeDecodeError, binascii.Error) as e:
        logger.debug(f"Legacy ECB decryption failed: {e}")

    # Data might be unencrypted - try to return as string
    if isinstance(data, bytes):
        try:
            return data.decode("utf-8")
        except UnicodeDecodeError as e:
            logger.warning(f"Could not decode data as UTF-8: {e}")

    return data


def aes_decrypt_old(data):
    """
    Legacy decryption function - tries ECB first, then falls back to raw data.
    Kept for backwards compatibility with code that might call this directly.
    """
    try:
        return _decrypt_legacy_ecb(data)
    except (ValueError, UnicodeDecodeError, binascii.Error) as e:
        logger.debug(f"ECB decryption failed in aes_decrypt_old: {e}")
        # If data is not encrypted, just return it
        if isinstance(data, bytes):
            try:
                return data.decode("utf-8")
            except UnicodeDecodeError:
                pass
        return data


class User(Base):
    __tablename__ = "user"

    uuid = Column(
        GUID, primary_key=True, index=True, unique=True, default=lambda: uuid.uuid4()
    )
    username = Column(String(64), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    auto_save = Column(Boolean, nullable=True)
    vim_mode = Column(Boolean, nullable=True, default=False)
    calendar_token = Column(String(64), unique=True, nullable=True)
    kanban_enabled = Column(Boolean, nullable=True, default=False)
    kanban_columns = Column(String(512), nullable=True, default='["todo", "done"]')
    notes = relationship("Note", lazy="dynamic", cascade="all, delete, delete-orphan")
    meta = relationship("Meta", lazy="dynamic", cascade="all, delete, delete-orphan")
    external_calendars = relationship(
        "ExternalCalendar", lazy="dynamic", cascade="all, delete, delete-orphan"
    )

    def __repr__(self):
        return "<User {}>".format(self.uuid)


class Meta(Base):
    __tablename__ = "meta"

    uuid = Column(
        GUID, primary_key=True, index=True, unique=True, default=lambda: uuid.uuid4()
    )
    user_id = Column(GUID, ForeignKey("user.uuid"), nullable=False)
    note_id = Column(GUID, ForeignKey("note.uuid"), nullable=False)
    name_encrypted = Column("name", LargeBinary)
    name_compare = Column(LargeBinary)
    kind = Column(String)
    task_column = Column(String(64), nullable=True)  # Kanban column for tasks

    @hybrid_property
    def name(self):
        return aes_decrypt(self.name_encrypted)

    @name.setter
    def name(self, value):
        self.name_encrypted = aes_encrypt(value)

    def __repr__(self):
        return "<Meta {}>".format(self.uuid)

    @property
    def serialize(self):
        result = {
            "uuid": self.uuid,
            "name": self.name,
            "kind": self.kind,
            "note_id": self.note_id,
        }
        if self.kind == "task":
            result["task_column"] = self.task_column
        return result


class Upload(Base):
    __tablename__ = "upload"

    uuid = Column(
        GUID, primary_key=True, index=True, unique=True, default=lambda: uuid.uuid4()
    )
    user_id = Column(GUID, ForeignKey("user.uuid"), nullable=False)
    filename = Column(String(255), nullable=False)
    path = Column(String(512), nullable=False, unique=True)
    size = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_seen_at = Column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return "<Upload {}>".format(self.uuid)

    @property
    def serialize(self):
        return {
            "uuid": self.uuid,
            "filename": self.filename,
            "path": self.path,
            "size": self.size,
            "created_at": self.created_at,
            "last_seen_at": self.last_seen_at,
        }


class Note(Base):
    __tablename__ = "note"

    uuid = Column(
        GUID, primary_key=True, index=True, unique=True, default=lambda: uuid.uuid4()
    )
    user_id = Column(GUID, ForeignKey("user.uuid"), nullable=False)
    data = Column(LargeBinary)
    title = Column(LargeBinary, nullable=False)
    date = Column(DateTime(timezone=True), server_default=func.now())
    is_date = Column(Boolean, default=False)
    meta = relationship("Meta", lazy="dynamic", cascade="all, delete, delete-orphan")

    @hybrid_property
    def text(self):
        return aes_decrypt(self.data)

    @text.setter
    def text(self, value):
        self.data = aes_encrypt(value)

    @hybrid_property
    def name(self):
        return aes_decrypt(self.title)

    @name.setter
    def name(self, value):
        # Use legacy CFB encryption for titles to allow database queries
        # (titles need deterministic encryption for lookups by encrypted value)
        self.title = aes_encrypt_legacy_cfb(value)

    def __repr__(self):
        return "<Note {}>".format(self.uuid)

    @property
    def serialize(self):
        return {
            "uuid": self.uuid,
            "data": self.text,
            "title": self.name,
            "date": self.date,
            "is_date": self.is_date,
        }

    def get_kanban_columns(self, user_default_columns=None):
        """
        Get effective kanban columns for this note.

        Priority:
        1. Frontmatter 'kanban:' array (per-note override)
        2. User's default columns
        3. System default: ["todo", "done"]
        """
        import json

        # Try to get from frontmatter
        data = frontmatter.loads(self.text)
        frontmatter_columns = data.get("kanban")

        if isinstance(frontmatter_columns, list) and len(frontmatter_columns) > 0:
            return frontmatter_columns

        # Use user default or system default
        if user_default_columns:
            if isinstance(user_default_columns, str):
                try:
                    return json.loads(user_default_columns)
                except (json.JSONDecodeError, TypeError):
                    pass
            elif isinstance(user_default_columns, list):
                return user_default_columns

        return ["todo", "done"]


# Update title automatically
def before_change_note(mapper, connection, target):
    title = None

    data = frontmatter.loads(target.text)

    if isinstance(data.get("title"), str) and len(data.get("title")) > 0:
        title = data.get("title")

    if not target.is_date:
        # If no title found in frontmatter, generate a default title
        if not title:
            # Try to extract first line of content as title
            content_lines = data.content.strip().split("\n")
            first_line = ""
            for line in content_lines:
                if line.strip():
                    first_line = line.strip()
                    break

            if first_line:
                # Remove markdown formatting from first line
                title = first_line.lstrip("#").strip()
                # Limit title length
                if len(title) > 100:
                    title = title[:100] + "..."

            # If still no title, use default
            if not title:
                title = "Untitled Note"

        target.name = title


# Task regex pattern: captures checkbox state, task text, and optional >>column
# Examples:
#   "- [ ] Buy groceries" -> (' ', 'Buy groceries', None)
#   "- [x] Done task >>done" -> ('x', 'Done task', 'done')
#   "- [ ] In review >>review" -> (' ', 'In review', 'review')
# Note: Use [ \t]* instead of \s* to avoid capturing newlines (which \s includes)
TASK_PATTERN = re.compile(
    r"^- \[([x ])\] (.+?)(?:[ \t]*>>([a-zA-Z0-9-]+))?[ \t]*$", re.MULTILINE
)


def parse_tasks_with_columns(content):
    """
    Parse tasks from markdown content, extracting column info.

    Returns list of tuples: (full_match, is_completed, task_text, column)
    - full_match: the entire task line (for storage/comparison)
    - is_completed: True if checkbox is [x]
    - task_text: the task text without column suffix
    - column: the kanban column name or None
    """
    tasks = []
    for match in TASK_PATTERN.finditer(content):
        checkbox = match.group(1)
        task_text = match.group(2).strip()
        column = match.group(3)  # None if no :column: present

        # Full match includes the column syntax for proper storage
        full_match = match.group(0)

        is_completed = checkbox == "x"
        tasks.append((full_match, is_completed, task_text, column))

    return tasks


def get_task_column(is_completed, explicit_column):
    """
    Determine the effective column for a task.

    - If explicit column provided, use it
    - Otherwise, default based on checkbox state
    """
    if explicit_column:
        return explicit_column
    return "done" if is_completed else "todo"


# Handle changes to tasks, projects, and tags
def after_change_note(mapper, connection, target):
    tags = []
    projects = []

    data = frontmatter.loads(target.text)

    if isinstance(data.get("tags"), list):
        tags = list(set([x.replace(",", "\,") for x in data.get("tags")]))
    elif isinstance(data.get("tags"), str):
        tags = list(set(map(str.strip, data["tags"].split(","))))
    tags = [x for x in tags if x]

    if isinstance(data.get("projects"), list):
        projects = list(set([x.replace(",", "\,") for x in data.get("projects")]))
    elif isinstance(data.get("projects"), str):
        projects = list(set(map(str.strip, data["projects"].split(","))))
    projects = [x for x in projects if x]

    # Parse tasks with column info: list of (full_match, is_completed, task_text, column)
    parsed_tasks = parse_tasks_with_columns(data.content)
    # Build dict mapping full task line to column for easy lookup
    task_columns = {}
    for full_match, is_completed, task_text, explicit_column in parsed_tasks:
        column = get_task_column(is_completed, explicit_column)
        task_columns[full_match] = column

    # List of task full matches (for compatibility with existing logic)
    tasks = list(task_columns.keys())

    existing_tags = []
    existing_projects = []
    existing_tasks = []

    metas = Meta.query.filter_by(note_id=target.uuid).all()

    for meta in metas:
        if meta.kind == "tag":
            existing_tags.append(meta)
        elif meta.kind == "project":
            existing_projects.append(meta)
        elif meta.kind == "task":
            existing_tasks.append(meta)

    for tag in existing_tags:
        if tag.name not in tags:
            connection.execute(
                text("DELETE FROM meta WHERE uuid = :uuid"),
                {"uuid": "{}".format(tag.uuid).replace("-", "")},
            )
        else:
            tags.remove(tag.name)

    for tag in tags:
        connection.execute(
            text(
                "INSERT INTO meta (uuid, user_id, note_id, name, kind) VALUES (:uuid, :user_id, :note_id, :name, :kind)"
            ),
            {
                "uuid": "{}".format(uuid.uuid4()).replace("-", ""),
                "user_id": "{}".format(target.user_id).replace("-", ""),
                "note_id": "{}".format(target.uuid).replace("-", ""),
                "name": aes_encrypt(tag),
                "kind": "tag",
            },
        )

    for project in existing_projects:
        if project.name not in projects:
            connection.execute(
                text("DELETE FROM meta WHERE uuid = :uuid"),
                {"uuid": "{}".format(project.uuid).replace("-", "")},
            )
        else:
            projects.remove(project.name)

    for project in projects:
        connection.execute(
            text(
                "INSERT INTO meta (uuid, user_id, note_id, name, kind) VALUES (:uuid, :user_id, :note_id, :name, :kind)"
            ),
            {
                "uuid": "{}".format(uuid.uuid4()).replace("-", ""),
                "user_id": "{}".format(target.user_id).replace("-", ""),
                "note_id": "{}".format(target.uuid).replace("-", ""),
                "name": aes_encrypt(project),
                "kind": "project",
            },
        )

    for task in existing_tasks:
        if task.name not in tasks:
            connection.execute(
                text("DELETE FROM meta WHERE uuid = :uuid"),
                {"uuid": "{}".format(task.uuid).replace("-", "")},
            )
        else:
            # Task still exists - check if column needs update
            new_column = task_columns.get(task.name)
            if new_column and new_column != task.task_column:
                connection.execute(
                    text("UPDATE meta SET task_column = :column WHERE uuid = :uuid"),
                    {
                        "column": new_column,
                        "uuid": "{}".format(task.uuid).replace("-", ""),
                    },
                )
            tasks.remove(task.name)

    for task in tasks:
        encrypted_task = aes_encrypt(task)
        task_column = task_columns.get(task)

        connection.execute(
            text(
                "INSERT INTO meta (uuid, user_id, note_id, name, name_compare, kind, task_column) VALUES (:uuid, :user_id, :note_id, :name, :name_compare, :kind, :task_column)"
            ),
            {
                "uuid": "{}".format(uuid.uuid4()).replace("-", ""),
                "user_id": "{}".format(target.user_id).replace("-", ""),
                "note_id": "{}".format(target.uuid).replace("-", ""),
                "name": encrypted_task,
                "name_compare": encrypted_task,
                "kind": "task",
                "task_column": task_column,
            },
        )


def before_update_task(mapper, connection, target):
    if target.kind != "task":
        return

    if target.name_encrypted == target.name_compare:
        return

    note = Note.query.get(target.note_id)

    if not note:
        return

    note_data = aes_encrypt(
        note.text.replace(aes_decrypt(target.name_compare), target.name)
    )

    connection.execute(
        text("UPDATE note SET data = :data WHERE uuid = :uuid"),
        {"data": note_data, "uuid": "{}".format(note.uuid).replace("-", "")},
    )

    target.name_compare = target.name_encrypted


event.listen(Note, "before_insert", before_change_note)
event.listen(Note, "before_update", before_change_note)
event.listen(Note, "after_insert", after_change_note)
event.listen(Note, "after_update", after_change_note)
event.listen(Meta, "before_update", before_update_task)


class ExternalCalendar(Base):
    __tablename__ = "external_calendar"

    uuid = Column(
        GUID, primary_key=True, index=True, unique=True, default=lambda: uuid.uuid4()
    )
    user_id = Column(GUID, ForeignKey("user.uuid"), nullable=False)
    name = Column(String(128), nullable=False)
    url = Column(String(512), nullable=False)
    color = Column(String(16), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return "<ExternalCalendar {}>".format(self.uuid)

    @property
    def serialize(self):
        return {
            "uuid": self.uuid,
            "name": self.name,
            "url": self.url,
            "color": self.color,
        }
