# DailyNotes Architecture Guide

## Project Overview

DailyNotes is a self-hosted daily task and note-taking application that combines the experience of a physical planner with modern web technology. It supports markdown with GitHub Flavored Markdown (GFM) task lists, making it ideal for daily journaling, task tracking, and note management.

**Version Format:** `YYYY.MM.DD-##` (date-based with daily build number, managed by CI)

## Technology Stack

### Backend

- **Framework:** Flask (Python microframework)
- **Database ORM:** SQLAlchemy with Flask-SQLAlchemy
- **Authentication:** JWT (JSON Web Tokens) via flask-jwt-extended
- **Password Hashing:** Argon2 via flask-argon2
- **Database Migrations:** Flask-Migrate (Alembic)
- **Production Server:** Gunicorn
- **Data Encryption:** PyCrypto (AES encryption for sensitive data at rest)
- **Markdown Processing:** python-frontmatter (for parsing YAML frontmatter)

**Python Version:** Python 3.8+ (also supports Python 2)

### Frontend

- **Framework:** Vue.js 2.6
- **Language:** TypeScript 3.5
- **UI Library:** Buefy (Vue wrapper for Bulma CSS)
- **CSS Framework:** Bulma with Bulmaswatch theme (Minty)
- **Editor:** CodeMirror 5 (for markdown editing with syntax highlighting)
- **Markdown Rendering:** Marked (for HTML preview with GFM support)
- **Routing:** Vue Router 3
- **HTTP Client:** Axios with JWT interceptors
- **Utilities:** date-fns, Lodash, Vue Masonry CSS
- **Icons:** FontAwesome Free
- **Fonts:** Fira Code (with ligatures), Montserrat

**Node Version:** 12+

## Project Structure

```
DailyNotes/
├── app/                          # Backend Python application
│   ├── __init__.py              # Flask app initialization
│   ├── routes.py                # API endpoints
│   ├── models.py                # Database models (User, Note, Meta)
│   └── model_types.py           # Custom SQLAlchemy types (GUID)
├── client/                       # Frontend Vue.js application
│   ├── src/
│   │   ├── main.ts              # Vue app entry point
│   │   ├── App.vue              # Root Vue component
│   │   ├── interfaces.ts        # TypeScript interfaces (INote, IHeaderOptions, IMeta)
│   │   ├── router/
│   │   │   └── index.ts         # Vue Router configuration & auth guards
│   │   ├── services/            # API service layer
│   │   │   ├── requests.ts      # Axios configuration with JWT interceptors
│   │   │   ├── notes.ts         # Note/day API service methods
│   │   │   ├── user.ts          # User auth service
│   │   │   ├── sidebar.ts       # Sidebar state management
│   │   │   ├── localstorage.ts  # Local storage utilities
│   │   │   ├── consts.ts        # Template constants
│   │   │   ├── eventHub.ts      # Vue event bus
│   │   │   └── sharedBuefy.ts   # Shared Buefy notification/dialog
│   │   ├── components/          # Reusable Vue components
│   │   │   ├── Editor.vue       # CodeMirror markdown editor
│   │   │   ├── MarkdownPreview.vue # HTML preview for markdown content
│   │   │   ├── Header.vue       # Page header with nav & controls
│   │   │   ├── Calendar.vue     # Date picker calendar
│   │   │   ├── NoteCard.vue     # Note display card
│   │   │   ├── Tasks.vue        # Task list component
│   │   │   ├── Tags.vue         # Tag display component
│   │   │   ├── SimpleTask.vue   # Individual task item
│   │   │   ├── TaskItem.vue     # Task in list format
│   │   │   └── UnsavedForm.vue  # Unsaved changes dialog
│   │   └── views/               # Page-level Vue components (routed)
│   │       ├── Home.vue         # Main layout with sidebar
│   │       ├── Day.vue          # Daily note editor
│   │       ├── Note.vue         # Note detail page
│   │       ├── NewNote.vue      # Create new note
│   │       ├── Search.vue       # Search page
│   │       ├── Auth.vue         # Auth layout
│   │       ├── Login.vue        # Login form
│   │       ├── Signup.vue       # Registration form
│   │       └── Error pages      # 404, 401, error pages
│   ├── package.json             # Frontend dependencies & scripts
│   └── tsconfig.json            # TypeScript configuration
├── config/                       # Configuration directory
│   ├── app.db                   # SQLite database (default)
│   ├── .env                     # Environment variables (generated)
│   └── export.zip               # Export storage location
├── migrations/                   # Database migration files (Alembic)
├── config.py                    # Flask configuration
├── server.py                    # Flask app entry point
├── requirements.txt             # Python dependencies
├── run.sh                       # Production startup script
├── Dockerfile                   # Docker image definition
├── docker-compose.yml           # Docker compose configuration
└── README.md                    # Project documentation
```

## Core Architecture

### Data Flow

1. **Frontend (Vue.js)**

   - User interacts with Vue components
   - Components dispatch API calls via service layer (NoteService, user service)
   - Requests module adds JWT token to Authorization header
   - Responses are parsed and component state is updated

2. **API Layer (requests.ts)**

   - Axios HTTP client with interceptors
   - Automatically adds JWT Bearer token from localStorage
   - Handles 401/403/422 responses by logging user out and redirecting to login
   - Provides wrapper methods: `post()`, `get()`, `put()`, `delete()`, `download()`

3. **Backend (Flask)**

   - Routes receive requests at `/api/*` endpoints
   - `@jwt_required()` decorator validates JWT token
   - Extract user identity from JWT with `get_jwt_identity()`
   - Query database for user and related data
   - Return JSON responses

4. **Database**
   - SQLAlchemy ORM for data access
   - All sensitive text fields encrypted with AES before storage
   - Automatic title extraction from markdown frontmatter
   - Automatic meta extraction (tags, projects, tasks) on note save

### Database Models

**User**

- `uuid` - Primary key
- `username` - Unique login identifier
- `password_hash` - Argon2 hashed password
- `auto_save` - Boolean for auto-save preference
- Relationships: `notes`, `meta` (cascading delete)

**Note**

- `uuid` - Primary key
- `user_id` - Foreign key to User
- `data` - Encrypted markdown content
- `title` - Encrypted title (extracted from frontmatter or derived)
- `date` - Created timestamp
- `is_date` - Boolean (True for daily notes)
- Relationships: `meta` (tags, projects, tasks)

**Meta** (Tags, Projects, Tasks)

- `uuid` - Primary key
- `user_id` - Foreign key to User
- `note_id` - Foreign key to Note
- `name_encrypted` - Encrypted name/text
- `name_compare` - For task update tracking
- `kind` - "tag", "project", or "task"

### Encryption Strategy

- Uses AES encryption (PyCrypto library)
- Encryption key from `DB_ENCRYPTION_KEY` environment variable
- All user data encrypted at rest in database
- Two encryption methods: new (CFB mode) and old (legacy compatibility)
- Decryption happens transparently via SQLAlchemy `@hybrid_property`

### Markdown Processing

Files use YAML frontmatter format:

```markdown
---
title: Daily Notes
tags: personal, productivity
projects: life
---

## Main content

- [ ] Task item
- [x] Completed task
```

Frontmatter is parsed with `python-frontmatter`:

- `title` field auto-updates note title
- `tags` field populates tag metadata
- `projects` field populates project metadata
- Tasks extracted from markdown checkbox pattern `- [ ] ` or `- [x] `

## API Endpoints

### Authentication

- `POST /api/sign-up` - Register new user
- `POST /api/login` - Login and get JWT token
- `GET /api/refresh_jwt` - Refresh JWT token

### Notes

- `GET /api/date?date=MM-dd-yyyy` - Get daily note for date
- `GET /api/note?uuid=...` - Get specific note by UUID
- `PUT /api/save_day` - Save daily note
- `POST /api/create_note` - Create new note
- `PUT /api/save_note` - Update note content
- `DELETE /api/delete_note/{uuid}` - Delete note

### Search & Metadata

- `GET /api/sidebar` - Get all notes, tags, projects, tasks
- `GET /api/events` - Get list of dates with notes (for calendar)
- `POST /api/search` - Search notes by project, tag, or text content

### Settings

- `POST /api/toggle_auto_save` - Toggle auto-save setting
- `GET /api/export` - Download all notes as ZIP file

### Frontend Fallback

- `GET /` and `/<path>` - Serves Vue.js SPA (index.html)

## Build & Run Commands

### Frontend Scripts (client/package.json)

```bash
npm run serve        # Development server with hot reload
npm run build        # Production build
npm run test:unit    # Run unit tests
npm run lint         # Run ESLint
```

### Backend Scripts

```bash
./verify_env.py              # Generate/verify environment variables
./verify_data_migrations.py  # Migrate encryption keys if needed
flask db upgrade             # Run pending migrations
gunicorn server:app -b 0.0.0.0:5000  # Start production server
```

### Development

```bash
# Terminal 1: Start backend
./run.sh  # Runs Flask development server

# Terminal 2: Start frontend
cd client && npm run serve
```

### Production

```bash
# Using Docker
docker-compose up

# Or with Docker run
docker run -p 5000:5000 -v /config_dir:/app/config m0ngr31/dailynotes
```

## Configuration

### Environment Variables

| Variable            | Purpose                      | Default                   |
| ------------------- | ---------------------------- | ------------------------- |
| `API_SECRET_KEY`    | Signs JWT tokens             | Generated automatically   |
| `DB_ENCRYPTION_KEY` | Encrypts data at rest        | Generated automatically   |
| `DATABASE_URI`      | Database connection string   | SQLite in /config/app.db  |
| `PREVENT_SIGNUPS`   | Disable signup endpoint      | Not set (signups enabled) |
| `BASE_URL`          | URL prefix for reverse proxy | None                      |
| `PUID` / `PGID`     | Docker user/group IDs        | None                      |
| `VUE_APP_BASE_URL`  | Frontend API base URL        | /api                      |

### Key Files

- **config.py** - Flask configuration management
- **requirements.txt** - Python package versions
- **client/package.json** - Node package versions and scripts
- **client/tsconfig.json** - TypeScript compiler settings
- **Dockerfile** - Multi-stage: Python + Node build → Gunicorn
- **.env** - Generated at runtime with encryption keys (DO NOT commit)

## Development Workflow

### Setting Up

1. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   cd client && npm ci
   ```

2. **Initialize environment:**

   ```bash
   ./verify_env.py
   # Creates /config/.env with generated keys
   ```

3. **Run both servers:**
   - Terminal 1: `./run.sh` (Flask on http://localhost:5000)
   - Terminal 2: `cd client && npm run serve` (Webpack on http://localhost:8080)

### Database Migrations

- Migrations stored in `/migrations/` directory
- Add schema change with: `flask db migrate -m "description"`
- Apply migration with: `flask db upgrade`
- Uses SQLAlchemy declarative ORM

### Authentication Flow

1. User submits credentials to `/api/sign-up` or `/api/login`
2. Backend generates JWT token with username as identity
3. Frontend stores token in localStorage
4. Axios interceptor adds `Authorization: Bearer <token>` to all requests
5. On auth failure (401/403), token cleared, user redirected to login
6. Token auto-refreshed via `/api/refresh_jwt` on demand

### Frontend Routing

- **Protected routes** require valid JWT (checked in router guards)
- Login/signup pages accessible only without token
- Dashboard and note pages require authentication
- Route transitions handled by Vue Router with auth guards

## Key Design Patterns

1. **JWT Authentication** - Stateless token-based auth
2. **Encrypted At Rest** - AES encryption for all user data
3. **Event Hooks** - SQLAlchemy event listeners auto-update metadata
4. **Service Layer** - Centralized API calls in `/client/src/services/`
5. **Component Composition** - Reusable Vue components (Editor, Header, etc.)
6. **Markdown-First** - All content in markdown with frontmatter metadata
7. **Single Page App** - Vue Router client-side navigation
8. **Auto-Save** - Optional auto-save toggle per user
9. **Full-Text Search** - Simple string matching across notes
10. **Export** - Download all notes as ZIP with markdown files
11. **HTML Preview** - Real-time markdown preview with VS Code-style hotkeys

## HTML Preview Feature

The HTML Preview feature allows users to view their markdown content rendered as HTML in real-time, with two display modes and VS Code-style keyboard shortcuts.

### Preview Modes

1. **Side-by-Side Preview** (`Cmd+K` then `V`)
   - Editor and preview displayed side-by-side
   - 50/50 split view with synchronized scrolling
   - Ideal for writing while seeing the formatted output
   - Available in both Day.vue and Note.vue views

2. **Preview Only** (`Shift+Cmd+V`)
   - Full-screen preview with editor hidden
   - Clean reading view of formatted markdown
   - Useful for reviewing final output
   - Toggle again to return to editor

3. **Close Preview**
   - Click the preview icon dropdown and select "Close Preview"
   - Or toggle the current mode again to close

### Implementation Details

**Components:**

- `MarkdownPreview.vue` - Main preview component
  - Uses the `marked` library for markdown-to-HTML conversion
  - Configured for GitHub Flavored Markdown (GFM)
  - Supports task lists, tables, code blocks, and all standard markdown features
  - Dark theme styling to match the CodeMirror editor

**Keyboard Shortcuts:**

- `Cmd+K V` (macOS) or `Ctrl+K V` (Windows/Linux) - Toggle side-by-side preview
- `Shift+Cmd+V` (macOS) or `Shift+Ctrl+V` (Windows/Linux) - Toggle preview-only mode
- Sequential key detection with 1-second timeout for `Cmd+K` then `V` pattern

**UI Controls:**

- Eye icon in header (right side, before save button)
- Dropdown menu with three options:
  - Preview Side-by-Side
  - Preview Only
  - Close Preview (when active)
- Icon changes color when preview is active

**Styling:**

- Dark background (`#263238`) matching CodeMirror theme
- Syntax-highlighted code blocks
- Styled tables, blockquotes, and task lists
- Typography optimized for readability
- Responsive layout with proper spacing

**State Management:**

- Preview mode stored in component state (`previewMode: 'none' | 'side' | 'replace'`)
- Synced with `headerOptions.previewMode` for UI updates
- Live updates as user types in editor
- Preview renders `modifiedText` (unsaved changes) or `text` (saved content)

### Usage in Views

Both `Day.vue` and `Note.vue` support the preview feature:

```typescript
// State
public previewMode: 'none' | 'side' | 'replace' = 'none';

// Header options
public headerOptions: IHeaderOptions = {
  showPreview: true,
  previewMode: 'none',
  togglePreviewFn: (mode) => this.togglePreview(mode),
  // ... other options
}

// Toggle method
public togglePreview(mode: 'side' | 'replace') {
  if (this.previewMode === mode) {
    this.previewMode = 'none';
  } else {
    this.previewMode = mode;
  }
  this.headerOptions.previewMode = this.previewMode;
}
```

### Supported Markdown Features

The preview renders all GitHub Flavored Markdown (GFM) features:

- Headers (H1-H6)
- Bold, italic, strikethrough
- Links and images
- Ordered and unordered lists
- Task lists with checkboxes
- Code blocks with syntax highlighting
- Inline code
- Blockquotes
- Tables
- Horizontal rules
- Line breaks (GFM mode)

## Notes for Contributors

- **Python version:** Works with Python 2.7+ and Python 3.3+ (though dated)
- **Node version:** Requires Node 12+, TypeScript strict mode enabled
- **Database:** Default SQLite but supports PostgreSQL/MySQL via DATABASE_URI
- **Encryption:** Critical - do not change DB_ENCRYPTION_KEY without migration
- **Frontend Build:** Built with Vue CLI 4, outputs to `/dist/` served by Flask
- **Linting:** Pre-commit hooks run ESLint on Vue/TypeScript files
- **Tests:** Jest unit tests available in client (minimal coverage currently)
- **Docker:** Multi-stage build, final image ~400MB

## Important Implementation Details

1. **Date Format:** Frontend uses `MM-dd-yyyy` format for daily notes
2. **Title Extraction:** Automatic from `title:` field in markdown frontmatter
3. **Task Parsing:** Uses regex `- \[[x| ]\]` to find checkbox tasks
4. **Sidebar State:** Managed in `sidebar.ts` service (not Vuex)
5. **Error Handling:** Buefy toast notifications for user feedback
6. **CodeMirror Config:** Line numbers, syntax highlighting, code folding
7. **JWT Expiration:** 7 days default (set in config.py)
8. **Cascading Deletes:** User deletion cascades to all notes and metadata
9. **Preview Hotkeys:** `Cmd+K` then `V` for side-by-side, `Shift+Cmd+V` for preview-only mode

## Security Considerations

- Passwords hashed with Argon2 (memory-hard algorithm)
- All user data encrypted at rest with AES
- JWT tokens expire after 7 days
- No CSRF tokens (stateless JWT design)
- Session validation on every request via JWT
- Logout clears token from localStorage
- Consider HTTPS for production deployment
- Environment variables for all secrets (not hardcoded)

---

_Refer to README.md and source code for latest information._
