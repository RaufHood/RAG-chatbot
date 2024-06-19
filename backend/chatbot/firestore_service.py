import firebase_admin
from firebase_admin import credentials, firestore
import datetime

# Initialize Firestore
cred = credentials.Certificate('asklepi-sak.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

def store_conversation(session_id: str, question: str, answer: str):
    doc_ref = db.collection('conversations').document(session_id)
    doc_ref.set({
        'history': firestore.ArrayUnion([{
            'question': question,
            'answer': answer,
            'timestamp': datetime.datetime.now()
        }])
    }, merge=True)

def get_conversation_history(session_id: str):
    doc_ref = db.collection('conversations').document(session_id)
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict().get('history', [])
    return []
