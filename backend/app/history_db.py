"""
AgriGuide — Firestore Conversation History Storage.

Collection: user_history
Document ID: Firebase user UID
Field: user_uid (str)
Field: data (JSON-encoded list of conversation objects)

Requires Firebase Admin SDK initialization before use.
"""

import json
import logging
import time
import uuid

import firebase_admin
from firebase_admin import firestore

logger = logging.getLogger(__name__)

# Firestore single-document limit is 1,048,576 bytes (1 MiB).
# Keep payload safely below this threshold to prevent write failures.
MAX_PAYLOAD_BYTES = 950_000


def _get_db():
    """Return the initialized Firestore client."""
    if not firebase_admin._apps:
        try:
            from backend.firebase_auth import initialize_firebase
            initialize_firebase()
        except Exception as exc:
            raise RuntimeError(
                f"Firebase Admin SDK is not initialized and could not be auto-initialized: {exc}"
            ) from exc

    if not firebase_admin._apps:
        raise RuntimeError(
            "Firebase Admin SDK is not initialized. "
            "Check firebase_auth.initialize_firebase()."
        )

    return firestore.client()


def init_db():
    """Verify Firestore connection."""
    _get_db()


def _validate_message(msg: dict) -> dict:
    """Validate and sanitize a single message object."""
    if not isinstance(msg, dict):
        msg = {}

    msg_id = str(msg.get("id") or uuid.uuid4())
    role = str(msg.get("role", "user")).lower()
    if role not in ("user", "assistant", "system"):
        role = "user"
    content = str(msg.get("content", ""))
    timestamp = msg.get("timestamp")
    if not isinstance(timestamp, (int, float)):
        timestamp = int(time.time() * 1000)

    clean_msg = {
        "id": msg_id,
        "role": role,
        "content": content,
        "timestamp": timestamp,
    }
    if msg.get("isError"):
        clean_msg["isError"] = True

    return clean_msg


def _validate_conversation(conv: dict) -> dict:
    """Validate and sanitize a single conversation object."""
    if not isinstance(conv, dict):
        conv = {}

    conv_id = str(conv.get("id") or uuid.uuid4())
    title = str(conv.get("title") or "New conversation").strip()
    if not title:
        title = "New conversation"

    raw_messages = conv.get("messages", [])
    if not isinstance(raw_messages, list):
        raw_messages = []

    clean_messages = [_validate_message(m) for m in raw_messages if isinstance(m, dict)]

    now = int(time.time() * 1000)
    created_at = conv.get("createdAt")
    if not isinstance(created_at, (int, float)):
        created_at = now

    updated_at = conv.get("updatedAt")
    if not isinstance(updated_at, (int, float)):
        updated_at = created_at

    return {
        "id": conv_id,
        "title": title,
        "messages": clean_messages,
        "createdAt": created_at,
        "updatedAt": updated_at,
    }


def _prune_conversations_for_size(conversations: list) -> str:
    """
    Ensure the JSON representation of conversations stays within Firestore's 1 MiB limit.
    If payload exceeds MAX_PAYLOAD_BYTES, prunes older messages, truncates excessively long
    single messages, and retains the most recent conversations.
    """
    serialized = json.dumps(conversations, ensure_ascii=False)
    if len(serialized.encode("utf-8")) <= MAX_PAYLOAD_BYTES:
        return serialized

    logger.warning("Conversation history exceeds safe threshold. Trimming entries.")
    # Work on a deep copy of conversations
    pruned = []
    for c in conversations:
        c_copy = dict(c, messages=[dict(m) for m in c.get("messages", [])])
        for m in c_copy["messages"]:
            if len(m.get("content", "")) > 15_000:
                m["content"] = m["content"][:15_000] + "... [truncated]"
        pruned.append(c_copy)

    serialized = json.dumps(pruned, ensure_ascii=False)
    if len(serialized.encode("utf-8")) <= MAX_PAYLOAD_BYTES:
        return serialized

    # Trim older messages from conversations that have more than 4 messages
    for conv in reversed(pruned):
        while len(conv["messages"]) > 4:
            conv["messages"].pop(0)
            serialized = json.dumps(pruned, ensure_ascii=False)
            if len(serialized.encode("utf-8")) <= MAX_PAYLOAD_BYTES:
                return serialized

    # Trim down to 2 messages per conversation
    for conv in reversed(pruned):
        while len(conv["messages"]) > 2:
            conv["messages"].pop(0)
            serialized = json.dumps(pruned, ensure_ascii=False)
            if len(serialized.encode("utf-8")) <= MAX_PAYLOAD_BYTES:
                return serialized

    # If still oversized, drop oldest conversations until within limit
    while len(pruned) > 1:
        pruned.pop()
        serialized = json.dumps(pruned, ensure_ascii=False)
        if len(serialized.encode("utf-8")) <= MAX_PAYLOAD_BYTES:
            return serialized

    # If even 1 conversation is over limit, truncate its remaining message content
    if pruned and pruned[0].get("messages"):
        pruned[0]["messages"] = pruned[0]["messages"][-1:]
        m = pruned[0]["messages"][0]
        if len(m.get("content", "")) > 5_000:
            m["content"] = m["content"][:5_000] + "... [truncated]"

    return json.dumps(pruned, ensure_ascii=False)


def get_user_history(user_uid: str) -> list:
    """
    Load all saved conversations for one authenticated user.
    Returns list of conversation dicts sorted by updatedAt descending.
    """
    if not user_uid or not str(user_uid).strip():
        raise ValueError("User UID cannot be empty.")

    try:
        db = _get_db()
        document = (
            db.collection("user_history")
            .document(user_uid)
            .get()
        )

        if not document.exists:
            return []

        document_data = document.to_dict() or {}
        raw_data = document_data.get("data", "[]")

        if isinstance(raw_data, list):
            conversations = raw_data
        elif isinstance(raw_data, str):
            try:
                conversations = json.loads(raw_data)
            except json.JSONDecodeError as dec_err:
                logger.warning(
                    "Malformed JSON in user_history for uid prefix=%s: %s",
                    user_uid[:6],
                    dec_err,
                )
                return []
        else:
            conversations = []

        if not isinstance(conversations, list):
            return []

        cleaned = [_validate_conversation(c) for c in conversations if isinstance(c, dict)]
        cleaned.sort(key=lambda c: c.get("updatedAt", 0), reverse=True)
        return cleaned

    except Exception as exc:
        logger.exception(
            "Failed to retrieve conversation history for user prefix=%s: %s",
            user_uid[:6] if user_uid else "unknown",
            exc,
        )
        raise RuntimeError(
            "Failed to retrieve conversation history from Firestore."
        ) from exc


def save_user_history(user_uid: str, conversations: list) -> None:
    """Save the complete conversation list for one user."""
    if not user_uid or not str(user_uid).strip():
        raise ValueError("User UID cannot be empty.")

    if not isinstance(conversations, list):
        raise ValueError("Conversations must be a list.")

    try:
        cleaned = [_validate_conversation(c) for c in conversations if isinstance(c, dict)]
        cleaned.sort(key=lambda c: c.get("updatedAt", 0), reverse=True)
        serialized_data = _prune_conversations_for_size(cleaned)

        db = _get_db()
        db.collection("user_history").document(user_uid).set(
            {
                "user_uid": user_uid,
                "data": serialized_data,
            }
        )

        logger.info(
            "Conversation history saved successfully for user prefix=%s (%d convs).",
            user_uid[:6],
            len(cleaned),
        )

    except Exception as exc:
        logger.exception(
            "Failed to save conversation history for user prefix=%s: %s",
            user_uid[:6] if user_uid else "unknown",
            exc,
        )
        raise RuntimeError(
            "Failed to save conversation history to Firestore."
        ) from exc


def append_chat_turn(
    user_uid: str,
    conversation_id: str,
    question: str,
    answer: str,
    user_msg_id: str = None,
    assistant_msg_id: str = None,
) -> dict:
    """
    Atomically append a user question and assistant answer to the conversation.
    Creates the conversation if it does not already exist.
    Returns the updated conversation dict.
    """
    if not user_uid or not str(user_uid).strip():
        raise ValueError("User UID cannot be empty.")
    if not conversation_id or not str(conversation_id).strip():
        raise ValueError("Conversation ID cannot be empty.")

    conversations = get_user_history(user_uid)
    target_conv = None

    for conv in conversations:
        if conv.get("id") == conversation_id:
            target_conv = conv
            break

    now = int(time.time() * 1000)

    # Derive short title from question if new or placeholder
    clean_q = question.strip()
    title_snippet = clean_q[:36] + ("..." if len(clean_q) > 36 else "")

    if target_conv is None:
        target_conv = {
            "id": conversation_id,
            "title": title_snippet or "New conversation",
            "messages": [],
            "createdAt": now,
            "updatedAt": now,
        }
        conversations.insert(0, target_conv)
    else:
        # Update title if default
        if target_conv.get("title") in ("New conversation", "", None) or not target_conv.get("messages"):
            target_conv["title"] = title_snippet or "New conversation"

    # Append user message
    u_msg = {
        "id": user_msg_id or str(uuid.uuid4()),
        "role": "user",
        "content": question,
        "timestamp": now,
    }
    # Append assistant message
    a_msg = {
        "id": assistant_msg_id or str(uuid.uuid4()),
        "role": "assistant",
        "content": answer,
        "timestamp": now + 1,
    }

    target_conv["messages"].append(u_msg)
    target_conv["messages"].append(a_msg)
    target_conv["updatedAt"] = now + 1

    save_user_history(user_uid, conversations)
    return target_conv


def delete_user_conversation(user_uid: str, conversation_id: str) -> list:
    """
    Delete a single conversation by ID for the user.
    Returns the updated conversation list.
    """
    if not user_uid or not str(user_uid).strip():
        raise ValueError("User UID cannot be empty.")
    if not conversation_id or not str(conversation_id).strip():
        raise ValueError("Conversation ID cannot be empty.")

    conversations = get_user_history(user_uid)
    filtered = [c for c in conversations if c.get("id") != conversation_id]
    save_user_history(user_uid, filtered)
    return filtered
