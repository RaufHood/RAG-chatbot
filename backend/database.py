import psycopg2
from psycopg2 import sql
from psycopg2.extensions import connection as Connection
from psycopg2.extras import RealDictCursor
import uuid
import os
import uuid

DATABASE_URL = os.environ["DATABASE_URL"]
DATABASE_URL = "postgresql://postgres:hip@localhost/hipdatabase"
#DATABASE_URL = "sqlite:///./test.db"  # The path to your database file

def get_db_connection() -> Connection:
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn

def create_tables(conn: Connection):
    cursor = conn.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id SERIAL PRIMARY KEY,
                session_id UUID NOT NULL,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        print("Table 'conversations' created successfully.")
    except Exception as e:
        print(f"Failed to create table: {str(e)}")
    finally:
        cursor.close()


# Store conversation in the database
def store_conversation(conn: Connection, session_id: str, question: str, answer: str):
    cursor = conn.cursor()
    cursor.execute("INSERT INTO conversations (session_id, question, answer) VALUES (%s, %s, %s)",
                   (session_id, question, answer))
    conn.commit()

# Retrieve conversation history from the database
def get_conversation_context(conn: Connection, session_id: str):
    cursor = conn.cursor()
    cursor.execute("SELECT question, answer FROM conversations WHERE session_id = %s ORDER BY timestamp DESC",
                   (session_id,))
    return cursor.fetchall()

# Generate a new session id
def generate_session_id() -> str:
    return str(uuid.uuid4())

def close_db_connection(conn: Connection):
    if conn:
        conn.close()
