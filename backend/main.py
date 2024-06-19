from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
from .chatbot.chatbot import upload_text_sources, ask_question, check_schema, check_data, check_document_count
from dotenv import load_dotenv
import os
from pydantic import BaseModel, Field
from uuid import uuid4  # Make sure uuid4 is also imported if not already
import logging 
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Question(BaseModel):
    question: str
    session_id: str = Field(default_factory=lambda: str(uuid4()))

@asynccontextmanager
async def app_lifespan(app):
     # Check the flag to see if data should be uploaded on startup
    should_upload = os.getenv("UPLOAD_DATA_ON_STARTUP", "false").lower() == "true"
    print("UPLOAD_DATA_ON_STARTUP:", should_upload)
    if should_upload:
        print("Starting data upload...")
        # Provide the path to your data file or directory
        file_paths = ["backend/chatbot/paca.html"]
        for file_path in file_paths:
            try:
                upload_text_sources(file_path)
                print(f"Data uploaded successfully from {file_path}")
                #check_schema()        # Verify the schema
                #check_data()          # Verify data in LangChain class
                #check_document_count()# Check document count
            except Exception as e:
                print(f"Failed to upload data from {file_path}: {e}")
    yield  # FastAPI starts serving requests
    print("Application is shutting down...")

app.router.lifespan_context = app_lifespan

@app.get("/")
def read_root():
    return {"Chatbot_API": "True"}

@app.post("/process-text/")
async def process_question(item: Question):
    try:
        if not item.session_id:
            item.session_id = str(uuid4())  # Ensure there's a session_id
        answer = await ask_question(item.session_id, item.question) 
        return {"answer": answer, "session_id": item.session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
