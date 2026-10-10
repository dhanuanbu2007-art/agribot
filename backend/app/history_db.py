"""
AgriGuide — Firestore-backed conversation history storage.

Each Firebase user's conversations are stored as a single Firestore document:
  Collection : user_history
  Document ID: <firebase_uid>   (guaranteed unique per user, never guessable)
  Fields:
    user_uid  : str  (redundant but useful for Firestore console queries)
    data      : str  (JSON-encoded list of conversation objects)

No SQLite is used. Firestore is persistent across Render restarts and
redeployments. Firebase Admin SDK must be fully initialised before any
function here is called (done at startup via firebase_auth.initialize_firebase
which is imported in main.py before history_db is used).
"""

import json

from firebase_admin import firestore


def _get_db():
    """Return an authenticated Firestore client.

    Raises RuntimeError if Firebase Admin SDK was not initialised before this
    module was used, so failures are loud and actionable rather than silent.
    """
    import firebase_admin  # local import so the check is always current
    if not firebase_admin._apps:
        raise RuntimeError(
            "[history_db] Firebase Admin SDK is not initialised. "
            "Ensure firebase_auth.initialize_firebase() is called during "
            "application startup (main.py startup_event)."
        )
    return firestore.client()


def init_db():
    """No-op: Firestore creates collections/documents on first write."""
    pass


def get_user_history(user_uid: str) -> list:
    """Return the conversation list for *user_uid*, or [] on any error.

    Errors are printed to stderr so they appear in Render logs without
    exposing user data in API responses.
    """
    if not user_uid:
        return []
    try:
        db = _get_db()
        doc = db.collection("user_history").document(user_uid).get()
        if doc.exists:
            raw = doc.to_dict().get("data", "[]")
            try:
                parsed = json.loads(raw)
                return parsed if isinstance(parsed, list) else []
            except (json.JSONDecodeError, TypeError):
                print(
                    f"[History DB] Stored data for uid={user_uid[:8]}… "
                    "is not valid JSON; returning empty history."
                )
                return []
        return []
    except RuntimeError:
        raise  # propagate SDK-not-initialised error so it surfaces in logs
    except Exception as exc:
        print(f"[History DB] get failed for uid={user_uid[:8]}…: {exc}")
        return []


def save_user_history(user_uid: str, conversations: list) -> None:
    """Persist *conversations* for *user_uid* to Firestore.

    Uses set() (full overwrite) so the stored document always reflects the
    complete, authoritative list sent by the authenticated user.  The caller
    (main.py) verifies the Firebase ID token before reaching this function, so
    user_uid is always the server-verified UID.
    """
    if not user_uid:
        print("[History DB] save called with empty user_uid; skipped.")
        return
    try:
        db = _get_db()
        db.collection("user_history").document(user_uid).set(
            {
                "user_uid": user_uid,
                "data": json.dumps(conversations, ensure_ascii=False),
            }
        )
    except RuntimeError:
        raise
    except Exception as exc:
        print(f"[History DB] save failed for uid={user_uid[:8]}…: {exc}")
