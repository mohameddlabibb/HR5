# Somabay Handbook — Manual Installation Guide

This guide helps any developer set up and run the project locally on Windows, macOS, or Linux.

## Prerequisites
- **Python**: 3.10 or newer
- **Node.js**: 18.x or newer (includes npm)
- **Git**: optional, for cloning
- **SQLite**: optional CLI tools (Python includes the SQLite library already)

## 1) Get the source code
If you already have this folder locally, skip cloning.

```bash
# Via git (choose a destination folder)
git clone <your-repo-url> Somabay-Handbook
cd Somabay-Handbook
```

## 2) Create and activate a Python virtual environment
- Windows (PowerShell):
```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
```
- macOS/Linux (bash):
```bash
python3 -m venv .venv
source .venv/bin/activate
```

## 3) Install Python dependencies
From the project root:
```bash
pip install -r requirements.txt
```
Included packages:
- Flask, Werkzeug, Flask-Cors
- python-dotenv
- bleach
- Jinja2

## 4) Install Node.js dependencies
From the project root:
```bash
npm install
# Required by server.js for correct JS content types
npm install mime-types --save
```
This installs:
- express, http-proxy-middleware, concurrently (from package.json)
- mime-types (needed by server.js)

## 5) Initialize the database (SQLite)
Create the SQLite schema and ensure an admin user exists.
```bash
# Option A: Initialize via database.py (creates tables and ensures admin)
python backend/database.py

# Option B: Initialize via init_db.py
python backend/init_db.py

# Ensure admin user matches config.py (default username: admin, password: adminpass)
python backend/create_admin.py
```
This creates/updates site.db at the project root.

## 6) Seed content (optional)
- Import structured pages from JSON:
```bash
python import_pages.py
# or
python import_and_publish_pages.py
```
- Generate static HTML pages (optional utility):
```bash
python backend/generate_static_pages.py
```

## 7) Run the project in development
You need both the Flask API (port 5000) and the Node static server (port 3000).

- Option A: One command (requires your virtualenv to be activated so the `flask` CLI is available)
```bash
npm run dev
```
This runs:
- `flask --app backend.app run --debug` at http://localhost:5000
- `node server.js` at http://localhost:3000

- Option B: Two terminals
1) Terminal A (with venv active):
```bash
flask --app backend.app run --debug
```
2) Terminal B:
```bash
npm start
```

Open the app:
- Frontend: http://localhost:3000
- Admin panel: http://localhost:3000/admin_panel (or /admin.html)
- API (examples): http://localhost:5000/api/... (proxied via Node at /api/*)

## 8) Common troubleshooting
- **`flask` not found when running `npm run dev`**:
  - Ensure your Python virtualenv is activated in the same terminal before running the command.
- **Cannot find module 'mime-types'** when starting Node server:
  - Run: `npm install mime-types --save`
- **Port already in use (3000 or 5000)**:
  - Stop the process using that port or change the port in `server.js` (Node) / use `--port` with Flask.
- **Database schema errors**:
  - Delete `site.db` (if you don’t need existing data) and re-run the DB initialization commands in step 5.
- **Admin login**:
  - Default credentials set by `backend/create_admin.py` are `admin` / `adminpass` (see `backend/config.py`).

## 9) Useful scripts
- Initialize DB (safe, idempotent):
```bash
python backend/init_db.py
```
- Force (re)create admin with config password:
```bash
python backend/create_admin.py
```
- Import pages data:
```bash
python import_pages.py
```
- Generate static pages from templates and data:
```bash
python backend/generate_static_pages.py
```

## 10) Next steps
- Keep your virtualenv active when running `npm run dev` so the Flask CLI is available.
- For production, consider a WSGI server (e.g., gunicorn or waitress) for Flask and a proper reverse proxy; not required for local development.