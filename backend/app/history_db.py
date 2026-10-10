import json
import firebase_admin
from firebase_admin import firestore

def _get_db():
    # Ensure Firebase is initialized
    if not firebase_admin._apps:
        from backend import firebase_auth
        firebase_auth.initialize_firebase()
    return firestore.client()

def init_db():
    # Firestore creates collections/documents automatically on first write
    pass

def get_user_history(user_uid: str) -> list:
    try:
        db = _get_db()
        doc_ref = db.collection('user_history').document(user_uid)
        doc = doc_ref.get()
        if doc.exists:
            data = doc.to_dict().get('data', '[]')
            return json.loads(data)
        return []
    except Exception as e:
        print(f"[History DB Error] Failed to get history for {user_uid}: {e}")
        return []

def save_user_history(user_uid: str, conversations: list):
    try:
        db = _get_db()
        doc_ref = db.collection('user_history').document(user_uid)
        doc_ref.set({
            'user_uid': user_uid,
            'data': json.dumps(conversations)
        })
    except Exception as e:
        print(f"[History DB Error] Failed to save history for {user_uid}: {e}")
