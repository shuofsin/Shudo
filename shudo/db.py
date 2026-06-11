# db.py
import sqlite3
import os

class Database:
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = os.path.join(os.path.dirname(__file__), "shudo.db")
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.c = self.conn.cursor()

    def init_db(self):
        """Create tables if they don't exist"""
        self.c.executescript("""
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task TEXT NOT NULL,
                priority TEXT NOT NULL DEFAULT 'medium'
                    CHECK(priority IN ('high', 'medium', 'low')),
                status TEXT NOT NULL DEFAULT 'pending'
                    CHECK(status IN ('pending', 'done')),
                due_date TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS pomodoros (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER,
                duration_minutes INTEGER NOT NULL,
                completed_at TEXT NOT NULL DEFAULT (datetime('now')), 
                FOREIGN KEY (task_id) REFERENCES tasks(id)
            );    
        """)
        self.conn.commit()
    
    def add_note(self, title, content):
        self.c.execute("INSERT INTO notes (title, content) VALUES (?, ?)",
                       (title, content))
        self.conn.commit()
        return self.c.lastrowid

    def get_notes(self):
        self.c.execute("SELECT id, title, content, created_at FROM notes ORDER BY created_at DESC")
        return self.c.fetchall()

    def search_notes_by_keyword(self, keyword):
        pattern = f"%{keyword}%"
        self.c.execute("SELECT id, title, content, created_at FROM notes WHERE title LIKE ? OR content LIKE ?",
                       (pattern, pattern))
        return self.c.fetchall()

    def delete_note(self, note_id):
        self.c.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        self.conn.commit()

    def add_task(self, task, priority="medium", due_date=None):
        self.c.execute("INSERT INTO tasks (task, priority, status, due_date) VALUES (?, ?, ?, ?)", 
                       (task, priority, "pending", due_date))
        self.conn.commit()
    
    def get_tasks(self):
        self.c.execute("SELECT task, priority, due_date FROM tasks ORDER BY due_date ASC, priority DESC")
        self.c.fetchall()
    
    def set_task_status(self, task_id, status="done"):
        self.c.execute("UPDATE tasks SET status = ? WHERE id = ?", 
                       (status, task_id))
        self.conn.commit();