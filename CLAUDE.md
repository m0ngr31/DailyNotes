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
│   │   │   ├── theme.ts         # Theme service (light/dark/system)
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
9. **Syntax-Based Search** - Query parser with tag/project filters and text search
10. **Export** - Download all notes as ZIP with markdown files
11. **HTML Preview** - Real-time markdown preview with VS Code-style hotkeys
12. **Theming** - Light/Dark/System theme support via CSS variables

## Search Feature

The Search feature provides a unified syntax-based search interface with autocomplete and result highlighting.

### Search Syntax

The search supports the following syntax:

- `tag:value` or `t:value` - Filter by tag
- `project:value` or `p:value` - Filter by project
- `tag:"multi word"` - Quoted values for spaces
- Plain text - Full-text search across note content
- Combined: `tag:meeting project:work budget` - Multiple filters together

### Search Logic

- **Multiple tags** = AND (note must have all specified tags)
- **Multiple projects** = OR (note can be in any specified project)
- **Multiple text terms** = AND (note must contain all words)

### Implementation Details

**Backend (`app/routes.py`):**

- `parse_search_query(query_string)` - Parses search syntax into structured filters
  - Returns `{tags: [], projects: [], text_terms: []}`
  - Supports shorthand `t:` and `p:` prefixes
  - Handles quoted values for multi-word tags/projects

- `get_text_snippet(text, search_terms, context_chars=50)` - Extracts snippet around matches
  - Returns `{snippet: str, highlights: [matched_terms]}`
  - Shows context around first match

- `/api/search` endpoint accepts:
  - New format: `{query: "tag:meeting budget"}`
  - Legacy format: `{selected: "tag", search: "meeting"}` (backward compatible)

**Frontend (`client/src/views/Search.vue`):**

- Single text input with autocomplete dropdown
- Autocomplete triggers on `tag:`, `t:`, `project:`, `p:` prefixes
- Keyboard navigation: Arrow keys, Tab/Enter to select, Escape to close
- Clear button (X) to reset search and results
- Syntax help tooltip (?) with quick reference
- Results persist when navigating away and returning

**State Management (`client/src/services/sidebar.ts`):**

- `searchQuery` - Stores the current query string
- `filteredNotes` - Stores search results with snippets/highlights
- Results include `snippet` and `highlights` fields for display

**NoteCard Component (`client/src/components/NoteCard.vue`):**

- Displays search snippets with highlighted matching terms
- Uses `<mark>` tags for highlighting
- Escapes HTML to prevent XSS

### URL Parameters

- New: `/search?q=tag:meeting+budget`
- Legacy: `/search?tag=meeting`, `/search?project=work`, `/search?search=text`

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

## Theme System

The application supports Light, Dark, and System themes with automatic detection of system color scheme preferences.

### Theme Modes

1. **Light Theme** - Clean, bright interface with light backgrounds
2. **Dark Theme** - Default dark interface optimized for low-light environments
3. **System Theme** - Automatically follows the operating system's color scheme preference

### Implementation Details

**Theme Service (`client/src/services/theme.ts`):**

- Singleton service managing theme state
- Persists preference to localStorage (`dn-theme-preference`)
- Listens for system `prefers-color-scheme` changes
- Applies theme class (`theme-light` or `theme-dark`) to `<html>` and `<body>`
- Exports `ThemePreference` type: `'light' | 'dark' | 'system'`

**CSS Variables (`App.vue`):**

All colors are defined as CSS custom properties:

```css
/* Key CSS Variables */
--main-bg-color: /* Primary background */
--text-primary: /* Main text color */
--text-secondary: /* Secondary text */
--text-link: /* Link color */
--border-color: /* Border color */
--editor-bg: /* Editor background */
--code-bg: /* Code block background */
--syntax-keyword: /* Syntax highlighting */
/* ... and more */
```

**Theme Switcher (`Settings.vue`):**

- Located in Settings modal under "Appearance" section
- Three-button selector for Light/Dark/System
- Visual icons: sun, moon, laptop
- Instant theme switching with toast notification

### Usage in Components

Components should use CSS variables instead of hardcoded colors:

```css
/* Good */
.my-component {
  background-color: var(--main-bg-color);
  color: var(--text-primary);
  border: 1px solid var(--border-color);
}

/* Avoid */
.my-component {
  background-color: #263238;
  color: #EEFFFF;
}
```

**CodeMirror Theme:**

The editor uses CSS variables where possible. For HighlightStyle (which doesn't support CSS variables), separate light and dark highlight styles are defined and swapped based on theme.

### Storage

- **Key:** `dn-theme-preference`
- **Values:** `"light"`, `"dark"`, `"system"`
- **Default:** `"system"` (falls back to dark if system preference unavailable)

## Kanban Board Feature

The Kanban feature provides an optional board view for organizing tasks across customizable columns with drag-and-drop support.

### Enabling Kanban

1. Go to Settings (gear icon in header menu)
2. Find the "Kanban" section
3. Toggle "Enable Kanban board"
4. When enabled, the Tasks icon in the header changes to a columns icon and opens the Kanban modal

### Task Syntax

Tasks use standard GFM checkbox syntax with an optional `>>column` suffix:

```markdown
- [ ] Plain task                    → defaults to "todo" column
- [x] Completed task                → defaults to "done" column
- [ ] Task in review >>review       → explicit "review" column
- [x] Done but still in review >>review  → stays in "review" (explicit wins)
```

**Column Assignment Rules:**
- Explicit `>>column` syntax always takes precedence over checkbox state
- Tasks without explicit column: unchecked → "todo", checked → "done"
- Column names support letters, numbers, and hyphens: `>>in-progress`, `>>stage2`

### Default Columns

- Default columns: `["todo", "done"]`
- Configure custom columns in Settings under the Kanban section
- Add/remove columns, reorder by editing in Settings

### Per-Note Column Override

Override default columns for a specific note using frontmatter:

```markdown
---
title: Sprint Planning
kanban:
  - backlog
  - in-progress
  - review
  - done
---

- [ ] Task one :backlog:
- [ ] Task two :in-progress:
```

### Auto-Column Creation

If a task uses a column that doesn't exist in the configuration:
- The column is automatically added before "done"
- Example: Using `:staging:` when columns are `[todo, done]` results in `[todo, staging, done]`
- To reorder, update the columns in Settings or note frontmatter

### Implementation Details

**Backend (`app/models.py`):**

- `User.kanban_enabled` - Boolean to enable/disable Kanban view
- `User.kanban_columns` - JSON string storing column array
- `Meta.task_column` - Stores the effective column for each task
- `TASK_PATTERN` regex captures: checkbox state, task text, optional column
- `parse_tasks_with_columns()` - Extracts task info including column
- `get_task_column()` - Determines effective column (explicit > checkbox default)
- `Note.get_kanban_columns()` - Returns effective columns (frontmatter > user > system default)

**Backend (`app/routes.py`):**

- `GET /api/settings` - Returns kanban settings
- `PUT /api/settings` - Updates kanban_enabled and kanban_columns
- `PUT /api/task_column` - Updates task's column by rewriting markdown
- `/api/sidebar` - Includes `kanban_enabled`, `kanban_columns`, and `task_column` on tasks

**Frontend (`client/src/services/sidebar.ts`):**

- `kanbanEnabled` - Reactive state for kanban toggle
- `kanbanColumns` - Reactive array of column names
- `toggleKanban()` - Enable/disable kanban
- `updateKanbanColumns()` - Save new column configuration
- `updateTaskColumn()` - Move task to different column via API

**Frontend (`client/src/components/Kanban.vue`):**

- Modal component with column layout
- Native HTML5 drag-and-drop between columns
- Props: `noteId` (filter to single note), `columns` (override columns)
- Parses task text to extract display text and completion state
- Shows note title on tasks when viewing all notes
- Responsive design (stacks on mobile)

**Frontend (`client/src/components/Tasks.vue`):**

- Conditionally renders dropdown (list) or opens Kanban modal
- Uses `sidebar.kanbanEnabled` to determine mode
- Shows columns icon when kanban is enabled

**Frontend (`client/src/components/Settings.vue`):**

- Kanban section with enable toggle
- Column management UI (add/remove/edit columns)
- Syntax hint for `>>column` usage

### Database Schema

```sql
-- User table additions
kanban_enabled BOOLEAN DEFAULT FALSE
kanban_columns VARCHAR(512) DEFAULT '["todo", "done"]'

-- Meta table addition
task_column VARCHAR(64)  -- Stores effective column for tasks
```

### CSS Styling

The Kanban board uses CSS variables for theme compatibility:
- `--card-bg` for column backgrounds
- `--border-color` for borders
- `--text-primary`, `--text-muted` for text
- `--accent-primary` for drag-over highlighting

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
