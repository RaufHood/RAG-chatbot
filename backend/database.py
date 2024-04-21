import sqlite3
from sqlite3 import Connection
import uuid

DATABASE_URL = "sqlite:///./test.db"  # The path to your database file

def get_db_connection() -> Connection:
    conn = sqlite3.connect("test.db")  # Ensure this path matches the DATABASE_URL
    conn.row_factory = sqlite3.Row
    return conn

def create_tables(conn: Connection):
    queries = [
        """CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )"""
    ]
    cursor = conn.cursor()
    for query in queries:
        cursor.execute(query)
    conn.commit()

# Store conversation in the database
def store_conversation(conn: Connection, session_id: str, question: str, answer: str):
    cursor = conn.cursor()
    cursor.execute("INSERT INTO conversations (session_id, question, answer) VALUES (?, ?, ?)",
                   (session_id, question, answer))
    conn.commit()

# Retrieve conversation history from the database
def get_conversation_context(conn: Connection, session_id: str):
    cursor = conn.cursor()
    cursor.execute("SELECT question, answer FROM conversations WHERE session_id = ? ORDER BY timestamp DESC",
                   (session_id,))
    return cursor.fetchall()

# Generate a new session id
def generate_session_id() -> str:
    return str(uuid.uuid4())

# Call the create_tables function to initialize the database tables
# It's better to call this once externally or check for table existence before calling it
# create_tables(get_db_connection())
