# DailyNotes: Daily tasks and notes in Markdown

<p align="center">
  <!-- Font-Awesome book-open -->
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 576 512" width="200px">
    <path style="fill:#6abfb0" d="M542.22 32.05c-54.8 3.11-163.72 14.43-230.96 55.59-4.64 2.84-7.27 7.89-7.27 13.17v363.87c0 11.55 12.63 18.85 23.28 13.49 69.18-34.82 169.23-44.32 218.7-46.92 16.89-.89 30.02-14.43 30.02-30.66V62.75c.01-17.71-15.35-31.74-33.77-30.7zM264.73 87.64C197.5 46.48 88.58 35.17 33.78 32.05 15.36 31.01 0 45.04 0 62.75V400.6c0 16.24 13.13 29.78 30.02 30.66 49.49 2.6 149.59 12.11 218.77 46.95 10.62 5.35 23.21-1.94 23.21-13.46V100.63c0-5.29-2.62-10.14-7.27-12.99z"/>
  </svg>
</p>

---

### In Loving Memory of [Joe Ipson](https://github.com/m0ngr31)

_This project is dedicated to [Joe Ipson](https://github.com/m0ngr31), the original creator of DailyNotes, who passed away in the summer of 2025 after a courageous battle with cancer._

Joe was a kindred spirit who believed in the simple power of writing things down. He built DailyNotes to bring the mindful experience of a physical planner into the digital world. His vision was to create something personal, self-hosted, and beautifully simple.

This project continues in his memory. Every commit, every feature, every bug fix is a small tribute to a dear friend whose spirit lives on in the code he wrote and the ideas he shared.

_Rest easy, Joe. We'll take it from here._

---

## About

The idea for this app came from using my Hobonichi Techo planner every morning to write down what I needed to accomplish that day & using it for scratching down random thoughts and notes as the day went on. The closest thing I've seen to an app for replacing this system is Noteplan, but I don't use a Mac or an iOS device, and it's not self-hostable, so I decided to write my own.

To check your current version, open **Settings** in the app and look in the **About** section.

Since I had the need for keeping track of to-dos throughout the day, regular Markdown didn't work for me since it doesn't natively support tasks. So as an alternative I'm using Github Flavored Markdown (GFM). I really wanted it to feel like an actual text editor and not just a textbox, so I decided to use CodeMirror to handle all the input. Fira Code is used to provide font ligatures. Some other nice features include code highlighting, text/code folding, and a task list where you can toggle the status of any task from any date or note.

## Roadmap

I'd like to try to include at least some of the following features to get to a final v1.0 release:

- ~~iCal support~~ ✅ Done! See [Calendar feed](#calendar-feed-ics) section
- ~~HTML preview~~ ✅ Done! Use `Cmd+K V` for side-by-side or `Shift+Cmd+V` for preview-only
- ~~Light/Dark themes~~ ✅ Done! See [Themes](#themes) section
- Kanban board for tasks (and new syntax to attach meta info like swimlane and project for each task)
- Nested tagging

## Themes

DailyNotes supports **Light**, **Dark**, and **System** themes to match your preferred working environment.

### Theme Options

| Theme     | Description                                                        |
| --------- | ------------------------------------------------------------------ |
| 🌙 Dark   | Default dark interface, optimized for low-light environments       |
| ☀️ Light  | Clean, bright interface with light backgrounds                     |
| 💻 System | Automatically follows your operating system's color scheme setting |

### How to Change Themes

1. Click the **menu icon** (⋮) in the header
2. Select **Settings**
3. In the **Appearance** section, click your preferred theme
4. The theme changes instantly and is saved for future sessions

The **System** option automatically switches between light and dark themes based on your OS settings (e.g., macOS Dark Mode, Windows Dark Theme). This is perfect if you prefer dark mode at night and light mode during the day.

## Calendar feed (ICS)

- Generate or rotate a private read-only ICS URL with `GET/POST /api/calendar_token` (requires auth).
- Subscribe in Google Calendar via **Settings -> Add calendar -> From URL** using `/api/calendar.ics?token=<your_token>`.
- Each daily note becomes an all-day event; the feed updates when notes change (Google polls periodically).
- Rotate the token to immediately revoke previous subscriptions or disable sharing with `DELETE /api/calendar_token`.
- You can now subscribe to external ICS feeds (e.g., Google private links) in Settings; DailyNotes shows those events on the matching day.

## Search

DailyNotes features a powerful syntax-based search that lets you quickly find notes using text queries.

### Search Syntax

| Syntax             | Description              | Example             |
| ------------------ | ------------------------ | ------------------- |
| `tag:value`        | Filter by tag            | `tag:meeting`       |
| `project:value`    | Filter by project        | `project:work`      |
| `t:value`          | Shorthand for tag        | `t:1on1`            |
| `p:value`          | Shorthand for project    | `p:DN`              |
| `tag:"multi word"` | Quoted values for spaces | `tag:"code review"` |
| Plain text         | Search note content      | `budget report`     |

### Example Searches

| Query                         | What it finds                                    |
| ----------------------------- | ------------------------------------------------ |
| `budget`                      | All notes containing "budget"                    |
| `tag:meeting`                 | All notes tagged "meeting"                       |
| `project:work tag:Q4`         | Notes in "work" project with "Q4" tag            |
| `tag:1on1 tag:feedback`       | Notes with both tags (AND)                       |
| `project:DN project:personal` | Notes in either project (OR)                     |
| `tag:meeting notes agenda`    | Tagged "meeting" containing "notes" AND "agenda" |

### Search Logic

- **Multiple tags** = AND (note must have all specified tags)
- **Multiple projects** = OR (note can be in any specified project)
- **Multiple text terms** = AND (note must contain all words)

### Features

- **Autocomplete**: Type `tag:` or `project:` to see suggestions from your existing tags/projects
- **Keyboard navigation**: Use arrow keys to select, Tab/Enter to confirm
- **Result highlighting**: Matching text is highlighted in search results with context snippets
- **Syntax help**: Click the `?` button for a quick reference

## In Action

Here are some screenshots of what it looks like:

Main editor:

![](https://i.imgur.com/WEZff9a.png)

Search page:

![](https://i.imgur.com/JKqHlhT.png)

Task list:

![](https://i.imgur.com/TSHboCT.png)

## Running

The recommended way of running is to pull the image from [Docker Hub](https://hub.docker.com/r/xhenxhe/dailynotes).

### Docker Setup

#### Environment Variables

| Environment Variable | Description                                                                                                                          | Default                                           |
| -------------------- | ------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------- |
| API_SECRET_KEY       | Used to sign API tokens.                                                                                                             | Will be generated automatically if not passed in. |
| DATABASE_URI         | Connection string for DB.                                                                                                            | Will create and use a SQLite DB if not passed in. |
| DB_ENCRYPTION_KEY    | Secret key for encrypting data. Length must be a multiple of 16.<br><br>_Warning_: If changed data will not be able to be decrypted! | Will be generated automatically if not passed in. |
| PREVENT_SIGNUPS      | Disable signup form? Anything in this variable will prevent signups.                                                                 | False                                             |
| BASE_URL             | Used when using a subfolder on a reverse proxy                                                                                       | None                                              |
| PUID                 | User ID (for folder permissions)                                                                                                     | None                                              |
| PGID                 | Group ID (for folder permissions)                                                                                                    | None                                              |
| DEFAULT_TIMEZONE     | Optional TZ name (e.g., `America/Denver`) for external ICS events; falls back to server local time                                   | None                                              |

#### Volumes

| Volume Name | Description                                                                                                           |
| ----------- | --------------------------------------------------------------------------------------------------------------------- |
| /app/config | Used to store DB and environment variables. This is not needed if you pass in all of the above environment variables. |

#### Docker Run

By default, the easiest way to get running is:

```bash
docker run -p 8000:8000 -v /config_dir:/app/config xhenxhe/dailynotes
```

#### Docker Compose

Here is a complete docker-compose example with all configuration options:

```yaml
services:
  dailynotes:
    image: xhenxhe/dailynotes:latest
    container_name: DailyNotes
    ports:
      - '8000:8000'
    volumes:
      # Persistent storage for database and config
      - ./dailynotes-data:/app/config
    environment:
      # Required: Secret key for signing JWT tokens
      # Generate with: openssl rand -hex 32
      API_SECRET_KEY: 'your-secure-api-secret-key-here'

      # Required: Encryption key for data at rest (must be multiple of 16)
      # Generate with: openssl rand -hex 32
      # WARNING: Changing this will make existing data unreadable!
      DB_ENCRYPTION_KEY: 'your-secure-db-encryption-key-here'

      # Optional: Database connection string
      # Default: SQLite database in /app/config/app.db
      # Examples:
      #   PostgreSQL: postgresql://user:password@host:5432/dailynotes
      #   MySQL:      mysql+pymysql://user:password@host:3306/dailynotes?charset=utf8mb4
      # DATABASE_URI: "sqlite:////app/config/app.db"

      # Optional: Prevent new user signups (set to any value to disable)
      # PREVENT_SIGNUPS: "true"

      # Optional: Base URL when using a reverse proxy subfolder
      # Example: If accessing via https://example.com/notes, set to "/notes"
      # BASE_URL: ""

      # Optional: Set user/group ID for file permissions
      # Useful for matching host user permissions
      # PUID: "1000"
      # PGID: "1000"
    restart: unless-stopped

    # Optional: Health check
    healthcheck:
      test: ['CMD', 'curl', '-f', 'http://localhost:8000/health']
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
# Optional: Use with PostgreSQL
#  postgres:
#    image: postgres:15-alpine
#    container_name: dailynotes-db
#    environment:
#      POSTGRES_DB: dailynotes
#      POSTGRES_USER: dailynotes
#      POSTGRES_PASSWORD: your-secure-db-password
#    volumes:
#      - ./postgres-data:/var/lib/postgresql/data
#    restart: unless-stopped
```

**Quick Start with Docker Compose:**

1. Save the above as `docker-compose.yml`
2. Generate secure keys:

   ```bash
   # Generate API secret key
   openssl rand -hex 32

   # Generate DB encryption key
   openssl rand -hex 32
   ```

3. Update the `API_SECRET_KEY` and `DB_ENCRYPTION_KEY` values
4. Start the application:
   ```bash
   docker-compose up -d
   ```
5. Access at `http://localhost:8000`

**Important Notes:**

- The `DB_ENCRYPTION_KEY` encrypts all your notes. **Never change it** after initial setup or your data will be unreadable!
- The `./dailynotes-data` directory will store your database and configuration
- The default port is now `8000` for better compatibility

### Reverse Proxy

If you're running DailyNotes behind a reverse proxy, here are example configurations for popular web servers.

<details>
<summary><strong>Caddy</strong></summary>

Caddy automatically handles HTTPS certificates. Add to your `Caddyfile`:

```caddyfile
dailynotes.example.com {
    reverse_proxy localhost:8000
}
```

For a subfolder setup:

```caddyfile
example.com {
    handle_path /notes/* {
        reverse_proxy localhost:8000
    }
}
```

Set `BASE_URL=/notes` in your DailyNotes environment when using a subfolder.

</details>

<details>
<summary><strong>Nginx</strong></summary>

```nginx
server {
    listen 80;
    server_name dailynotes.example.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

For a subfolder setup:

```nginx
location /notes/ {
    proxy_pass http://localhost:8000/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

Set `BASE_URL=/notes` in your DailyNotes environment when using a subfolder.

For HTTPS, add SSL configuration or use Certbot: `sudo certbot --nginx -d dailynotes.example.com`

</details>

<details>
<summary><strong>Apache</strong></summary>

Enable required modules:

```bash
sudo a2enmod proxy proxy_http headers
```

Virtual host configuration:

```apache
<VirtualHost *:80>
    ServerName dailynotes.example.com

    ProxyPreserveHost On
    ProxyPass / http://localhost:8000/
    ProxyPassReverse / http://localhost:8000/

    RequestHeader set X-Forwarded-Proto "http"
</VirtualHost>
```

For a subfolder setup:

```apache
<Location /notes>
    ProxyPass http://localhost:8000
    ProxyPassReverse http://localhost:8000
    RequestHeader set X-Forwarded-Proto "http"
</Location>
```

Set `BASE_URL=/notes` in your DailyNotes environment when using a subfolder.

For HTTPS, use Certbot: `sudo certbot --apache -d dailynotes.example.com`

</details>

## Development setup

### Option 1: Docker Development Environment (Recommended)

The easiest way to get started with development is using Docker. This approach provides:

- ✅ Consistent environment across all platforms (macOS, Linux, Windows)
- ✅ No need to install Python, Node.js, or manage versions
- ✅ Hot-reloading for both frontend and backend code
- ✅ Automatic database setup and migrations
- ✅ Isolated environment that won't affect your system

**Quick Start:**

```bash
# Start the development environment (builds, starts, and opens browser)
./dev
```

That's it! The script will:

1. Build the development Docker image
2. Start both Flask (port 5001) and Vue.js (port 8080) servers
3. Set up the database and run migrations
4. Open your browser to http://localhost:8080

**Development Workflow:**

All your code changes will be automatically detected:

- **Python/Flask changes**: Flask server auto-reloads
- **Vue.js changes**: Hot module replacement (HMR) updates the browser instantly
- **Database**: Persisted in `./config/app.db` on your host machine

**Useful Commands:**

```bash
# View live logs from both servers
docker compose -f docker-compose.dev.yml logs -f

# Stop the development environment
docker compose -f docker-compose.dev.yml down

# Restart services
docker compose -f docker-compose.dev.yml restart

# Access the container shell (for debugging)
docker exec -it dailynotes-dev bash

# Rebuild after dependency changes
docker compose -f docker-compose.dev.yml build
```

**Testing with PostgreSQL or MySQL:**

DailyNotes supports PostgreSQL and MySQL in addition to SQLite. To test with these databases:

```bash
# Start with PostgreSQL
./dev --postgres

# Start with MySQL
./dev --mysql

# Stop any database environment
./dev --down
```

These use production-like Docker Compose configurations (`docker-compose-postgres.yml` and `docker-compose-mysql.yml`) that include the database servers. The database data is persisted in Docker volumes.

**File Structure:**

- `Dockerfile.dev` - Development Docker image with both Python and Node.js
- `docker-compose.dev.yml` - Development compose config with volume mounts
- `docker-compose-postgres.yml` - PostgreSQL testing configuration
- `docker-compose-mysql.yml` - MySQL testing configuration
- `docker-entrypoint-dev.sh` - Startup script that runs both servers

**What's Mounted:**

The following directories are mounted from your host to enable hot-reloading:

- `./app/` - Python backend code
- `./client/src/` - Vue.js source code
- `./client/public/` - Static assets
- `./config/` - Database and environment variables (persisted)
- `./migrations/` - Database migrations

**Environment Variables:**

By default, the development environment will auto-generate secure keys in `./config/.env`. To customize:

```yaml
# Edit docker-compose.dev.yml
environment:
  API_SECRET_KEY: 'your-dev-key'
  DB_ENCRYPTION_KEY: 'your-16-char-multiple-key'
  PREVENT_SIGNUPS: 'true' # Optional: disable signups
```

---

### Option 2: Local Development Setup

If you prefer to run services directly on your host machine:

#### Automated Setup (macOS/Linux)

The easiest way to set up your development environment is to use the automated setup script:

```bash
./dev-setup.sh
```

This script will:

- Check for Python 3 and Node.js
- Automatically use Node.js 16 via nvm (if available)
- Create a Python virtual environment
- Install all Python dependencies
- Install all Node.js dependencies
- Generate environment configuration

After setup completes, run the development servers:

```bash
# Backend (in one terminal)
source venv/bin/activate
./run.sh

# Frontend (in another terminal)
cd client
npm run dev  # Uses Node 16 via nvm automatically
```

**Note:** The project includes a `.nvmrc` file that specifies Node.js 16. If you have nvm installed, it will automatically use the correct version.

### Manual Setup (Windows or alternative)

If you're on Windows or prefer to set up manually:

#### Installing dependencies

You need Python 3.8+ and Node.js 16 installed.

**Recommended:** Use [nvm](https://github.com/nvm-sh/nvm) (macOS/Linux) or [nvm-windows](https://github.com/coreybutler/nvm-windows) to manage Node.js versions. The project includes a `.nvmrc` file that specifies Node.js 16.

```bash
# If using nvm (recommended)
nvm install 16
nvm use 16

# Create and activate virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
cd client
npm ci
```

#### Creating the environment

You can use the environment variables from above, or you can generate new ones by running the following:

```bash
./verify_env.py
```

Keep in mind that since the data is encrypted, if you modify the `DB_ENCRYPTION_KEY` variable, your data will not be accessible anymore.

#### Running

During development you need to run the client and server simultaneously

```bash
# Activate virtual environment first
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run backend
./run.sh
```

```bash
# In a separate terminal
cd client

# If using nvm, switch to Node 16 first (or run npm run dev)
nvm use  # Reads from .nvmrc file

# Start frontend dev server
npm run serve
# Or use the dev script which automatically uses Node 16:
npm run dev
```
