# Task tracker

A basic Python Flask app with a file-based SQLite database. Add tasks, edit their titles and notes, set optional due dates, mark tasks complete, and delete tasks. Filter by all, active, or completed tasks.

## Run on Windows

Open PowerShell in this folder and run:

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python app.py
```

Open http://127.0.0.1:5000 in your browser. Stop the app with Ctrl+C.

On macOS or Linux, use `.venv/bin/python` instead of `.\.venv\Scripts\python`.

## Database

The app creates `instance/tasks.sqlite3` on its first run. Tasks stay in that file when the app stops or restarts. Python includes SQLite, so no separate database server is needed. To back up tasks, stop the app and copy this file.

The `tasks` table contains `id`, `title`, `description`, `due_date`, `completed`, and `created_at`. All database queries use parameter binding. Forms include CSRF protection, and task text is escaped when displayed. A local session secret is generated in `instance/secret.key`; an optional `SECRET_KEY` environment variable overrides it.

This is a local, single-user app without accounts. It listens on your own computer at `127.0.0.1`, with debug mode off. Public hosting would need authentication and a production server.

The interface uses Google Fonts when connected to the internet and system fonts otherwise. No sample tasks are added.

## Tests

```powershell
.\.venv\Scripts\python -m unittest -v
```

Tests use a separate temporary SQLite file. They check task creation, editing, completion, deletion, persistence across app instances, filters, validation, missing tasks, CSRF protection, and HTML escaping.
