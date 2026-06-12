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
                duration_minutes INTEGER NOT NULL DEFAULT 25,
                rest_minutes INTEGER NOT NULL DEFAULT 5,
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
    
    def update_note(self, note_id, title, content):
        self.c.execute(
            "UPDATE notes SET title = ?, content = ? WHERE id = ?",
            (title, content, note_id))
        self.conn.commit()

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
        return self.c.lastrowid
    
    def get_tasks(self):
        self.c.execute("""
                        SELECT id, task, priority, status, due_date 
                        FROM tasks 
                        ORDER BY 
                            CASE WHEN due_date IS NULL THEN 1 ELSE 0 END,
                            due_date ASC
                       """)
        return self.c.fetchall()

    def get_task_by_id(self, task_id):
        self.c.execute("SELECT id, task, priority, status, due_date FROM tasks WHERE id = ?", (task_id,))
        return self.c.fetchone()
    
    def set_task_status(self, task_id, status="done"):
        self.c.execute("UPDATE tasks SET status = ? WHERE id = ?", 
                       (status, task_id))
        self.conn.commit()

    def delete_task(self, task_id):
        self.c.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        self.conn.commit()
    
    def add_pomo_session(self, task_id, duration_minutes=25, rest_minutes=5):
        self.c.execute(
            "INSERT INTO pomodoros (task_id, duration_minutes, rest_minutes) VALUES (?, ?, ?)", 
            (task_id, duration_minutes, rest_minutes))
        self.conn.commit()
        return self.c.lastrowid

    def get_pomo_stats(self, task_id=None):
        if task_id is None:
            self.c.execute("""
                SELECT COUNT(*) as total_sessions,
                    COALESCE(SUM(duration_minutes), 0) as total_minutes
                FROM pomodoros
            """)
        else:
            self.c.execute("""
                SELECT COUNT(*) as total_sessions,
                    COALESCE(SUM(duration_minutes), 0) as total_minutes
                FROM pomodoros WHERE task_id = ?
            """, (task_id,))
        return self.c.fetchone()

    def get_pomo_sessions_all(self):
        self.c.execute("""
                        SELECT p.id, p.duration_minutes, p.completed_at, t.task
                        FROM pomodoros p
                        LEFT JOIN tasks t ON p.task_id = t.id
                        ORDER BY p.completed_at DESC
                       """)
        return self.c.fetchall()
    
    def close(self):
        self.conn.close()
