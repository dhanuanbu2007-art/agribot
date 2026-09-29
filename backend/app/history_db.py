import sqlite3
import json
from pathlib import Path

DB_PATH = Path(__file__).parent.parent.parent / "history.db"

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS user_history (
                user_uid TEXT PRIMARY KEY,
                data TEXT NOT NULL
            )
        ''')

def get_user_history(user_uid: str) -> list:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT data FROM user_history WHERE user_uid = ?", (user_uid,))
        row = cur.fetchone()
        if row:
            return json.loads(row[0])
        return []

def save_user_history(user_uid: str, conversations: list):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO user_history (user_uid, data) VALUES (?, ?)",
            (user_uid, json.dumps(conversations))
        )
