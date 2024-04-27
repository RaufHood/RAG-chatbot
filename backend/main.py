from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
from .chatbot.chatbot import upload_text_sources, ask_question
from dotenv import load_dotenv
import os
from typing import Optional
from .database import *
import uuid
load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    #allow_origins=["*"],
    allow_origins=["http://127.0.0.1:5500"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def startup():
    print("Running startup routine...")
    conn = get_db_connection()
    create_tables(conn)
    close_db_connection(conn)

def shutdown():
    # Here you can handle cleanup actions
    print("Running shutdown routine...")

app.add_event_handler("startup", startup)
app.add_event_handler("shutdown", shutdown)

@app.get("/test-db-init/")
def test_db_init():
    conn = get_db_connection()
    create_tables(conn)
    close_db_connection(conn)
    return {"status": "Database initialized, check logs for details."}

class Question(BaseModel):
    question: str
    session_id: Optional[str]

@asynccontextmanager
async def app_lifespan(app):
    # Check the flag to see if data should be uploaded on startup
    should_upload = os.getenv("UPLOAD_DATA_ON_STARTUP", "false").lower() == "true"
    print("UPLOAD_DATA_ON_STARTUP:", should_upload)
    if should_upload:
        print("Starting data upload...")
        # Provide the path to your data file or directory
        file_paths = ["backend/chatbot/paca.html"] #, "path/to/your/datafile2.html"]
        for file_path in file_paths:
            try:
                upload_text_sources(file_path)
                print(f"Data uploaded successfully from {file_path}")
            except Exception as e:
                print(f"Failed to upload data from {file_path}: {e}")
    yield  # FastAPI starts serving requests
    print("Application is shutting down...")

app.router.lifespan_context = app_lifespan

@app.get("/")
def read_root():
    return {"Chatbot_API": "True"}

  
@app.post("/process-text/")
def process_question(item: Question, db = Depends(get_db_connection)):
    print("process_question called")  # Debug print
    # If no session_id is provided, generate a new one
    try:
        if not item.session_id:
            item.session_id = str(uuid.uuid4()) #generate_session_id()
    
        # Retrieve the conversation context based on session_id
        context = get_conversation_context(db, item.session_id)
        print("Retrieved context:", context)  # Debug print to verify context retrieval
        # Process the input here; ensure your `process_input` can handle `context`
    
        answer = ask_question(item.question, item.session_id, db)
        store_conversation(db, item.session_id, item.question, answer)
        return {"session_id": item.session_id, "answer": answer}
    except Exception as e:
        print("Error in process_question:", str(e))  # Print any exceptions
        raise HTTPException(status_code=500, detail=str(e))

