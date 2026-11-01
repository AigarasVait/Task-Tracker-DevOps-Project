import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from app import create_app


class TaskTrackerTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.database = str(Path(self.directory.name) / "test.sqlite3")
        self.app = create_app({"TESTING": True, "DATABASE": self.database})
        self.client = self.app.test_client()
        self.client.get("/")
        with self.client.session_transaction() as session:
            self.token = session["csrf_token"]

    def tearDown(self):
        self.directory.cleanup()

    def post(self, path, **data):
        return self.client.post(path, data={"csrf_token": self.token, **data})

    def test_full_task_lifecycle_and_persistence(self):
        response = self.post("/tasks/new", title="Read chapter", description="Take notes", due_date="2026-12-01")
        self.assertEqual(response.status_code, 302)
        restarted = create_app({"TESTING": True, "DATABASE": self.database}).test_client()
        self.assertIn(b"Read chapter", restarted.get("/").data)
        self.assertEqual(self.post("/tasks/1/edit", title="Review chapter").status_code, 302)
        self.assertIn(b"Review chapter", self.client.get("/?status=active").data)
        self.post("/tasks/1/toggle")
        self.assertNotIn(b"Review chapter", self.client.get("/?status=active").data)
        self.assertIn(b"Review chapter", self.client.get("/?status=completed").data)
        self.post("/tasks/1/toggle")
        self.assertIn(b"Review chapter", self.client.get("/?status=active").data)
        self.post("/tasks/1/delete")
        with closing(sqlite3.connect(self.database)) as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM tasks").fetchone()[0], 0)

    def test_validation_and_missing_tasks(self):
        for fields in ({"title": " "}, {"title": "x" * 201}, {"title": "Test", "due_date": "2026-02-30"}):
            self.assertEqual(self.post("/tasks/new", **fields).status_code, 400)
        self.assertEqual(self.client.get("/tasks/999/edit").status_code, 404)
        self.assertEqual(self.post("/tasks/999/toggle").status_code, 404)
        self.assertEqual(self.post("/tasks/999/delete").status_code, 404)
        self.assertEqual(self.client.get("/tasks/1/delete").status_code, 405)

    def test_csrf_and_html_escaping(self):
        self.assertEqual(self.client.post("/tasks/new", data={"title": "Blocked"}).status_code, 400)
        self.post("/tasks/new", title="<script>alert(1)</script>")
        page = self.client.get("/").data
        self.assertNotIn(b"<script>alert(1)</script>", page)
        self.assertIn(b"&lt;script&gt;", page)


if __name__ == "__main__":
    unittest.main()
