"""A small, single-user task tracker backed by a SQLite file."""

import os
import secrets
import sqlite3
from datetime import date
from pathlib import Path

from flask import Flask, abort, g, redirect, render_template, request, session, url_for


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(DATABASE=str(Path(app.instance_path) / "tasks.sqlite3"))
    if test_config:
        app.config.update(test_config)
    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    key_path = Path(app.instance_path) / "secret.key"
    if not key_path.exists():
        try:
            with key_path.open("x") as key_file:
                key_file.write(secrets.token_hex(32))
        except FileExistsError:
            pass
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY") or key_path.read_text()

    def get_db():
        if "db" not in g:
            g.db = sqlite3.connect(app.config["DATABASE"])
            g.db.row_factory = sqlite3.Row
        return g.db

    @app.teardown_appcontext
    def close_db(_error):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    with app.app_context():
        db = get_db()
        db.execute("""CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT NOT NULL DEFAULT '',
            due_date TEXT NOT NULL DEFAULT '',
            completed INTEGER NOT NULL DEFAULT 0 CHECK (completed IN (0, 1)),
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )""")
        db.commit()

    @app.before_request
    def protect_forms():
        if "csrf_token" not in session:
            session["csrf_token"] = secrets.token_hex(32)
        if request.method == "POST":
            submitted = request.form.get("csrf_token", "")
            if not secrets.compare_digest(submitted, session["csrf_token"]):
                abort(400, "The form expired. Reload the page and try again.")

    def find_task(task_id):
        task = get_db().execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if task is None:
            abort(404)
        return task

    def read_form():
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        due_date = request.form.get("due_date", "").strip()
        error = None
        if not title or len(title) > 200:
            error = "Enter a task title between 1 and 200 characters."
        elif len(description) > 5000:
            error = "Keep the description under 5,001 characters."
        elif due_date:
            try:
                date.fromisoformat(due_date)
                if len(due_date) != 10:
                    raise ValueError
            except ValueError:
                error = "Enter a valid due date."
        return {"title": title, "description": description, "due_date": due_date}, error

    @app.get("/")
    def index():
        status = request.args.get("status", "all")
        if status not in ("all", "active", "completed"):
            status = "all"
        db = get_db()
        query = "SELECT * FROM tasks"
        params = ()
        if status != "all":
            query += " WHERE completed = ?"
            params = (int(status == "completed"),)
        tasks = db.execute(query + " ORDER BY completed, due_date = '', due_date, id DESC", params).fetchall()
        counts = db.execute("SELECT COUNT(*) AS total, COALESCE(SUM(completed), 0) AS done FROM tasks").fetchone()
        return render_template("index.html", tasks=tasks, counts=counts, status=status, today=date.today().isoformat())

    @app.route("/tasks/new", methods=["GET", "POST"])
    def create_task():
        task, error = {}, None
        if request.method == "POST":
            task, error = read_form()
            if error is None:
                db = get_db()
                db.execute("INSERT INTO tasks (title, description, due_date) VALUES (?, ?, ?)", tuple(task.values()))
                db.commit()
                return redirect(url_for("index"))
        return render_template("form.html", task=task, error=error, editing=False), 400 if error else 200

    @app.route("/tasks/<int:task_id>/edit", methods=["GET", "POST"])
    def edit_task(task_id):
        task, error = find_task(task_id), None
        if request.method == "POST":
            task, error = read_form()
            if error is None:
                db = get_db()
                db.execute("UPDATE tasks SET title = ?, description = ?, due_date = ? WHERE id = ?", (*task.values(), task_id))
                db.commit()
                return redirect(url_for("index"))
        return render_template("form.html", task=task, error=error, editing=True), 400 if error else 200

    @app.post("/tasks/<int:task_id>/toggle")
    def toggle_task(task_id):
        find_task(task_id)
        db = get_db()
        db.execute("UPDATE tasks SET completed = 1 - completed WHERE id = ?", (task_id,))
        db.commit()
        return redirect(url_for("index"))

    @app.post("/tasks/<int:task_id>/delete")
    def delete_task(task_id):
        find_task(task_id)
        db = get_db()
        db.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        db.commit()
        return redirect(url_for("index"))

    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5000)
