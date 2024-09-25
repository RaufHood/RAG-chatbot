import firebase_admin
from firebase_admin import credentials, firestore
import datetime

# Initialize Firestore
cred = credentials.Certificate('asklepi-sak.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

def store_conversation(user_id: str, session_id: str, question: str, answer: str):
    user_ref = db.collection('users').document(user_id)
        # Ensure the user document exists (optional: you can also add more userInfo fields)
    user_ref.set({"userInfo": {"createdAt": datetime.datetime.now()}}, merge=True)
    conversation_ref = user_ref.collection('conversations').document(session_id)

    conversation_ref.set({
        'history': firestore.ArrayUnion([{
            'question': question,
            'answer': answer,
            'timestamp': datetime.datetime.now()
        }])
    }, merge=True)

def get_conversation_history(user_id:str, session_id: str):
    conversation_ref = db.collection('users').document(user_id).collection('conversations').document(session_id)
    #doc_ref = db.collection('conversations').document(session_id)
    doc = conversation_ref.get()
    if doc.exists:
        return doc.to_dict().get('history', [])
    return []
