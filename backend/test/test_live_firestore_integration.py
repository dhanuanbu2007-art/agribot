"""
Live integration test for AgriGuide Firestore storage against project agriguide-838da.
Uses a temporary test UID, verifies document structure, Unicode/Tamil fidelity, and cleans up.
"""

import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from backend.app import history_db
from backend.firebase_auth import initialize_firebase


def run_live_test():
    print("[1] Initializing Firebase Admin SDK...")
    initialize_firebase()
    history_db.init_db()

    test_uid = "test-live-audit-uid-999"
    test_conv_id = "test-conv-tamil-1"

    print("[2] Cleaning up any prior test document...")
    try:
        db = history_db._get_db()
        db.collection("user_history").document(test_uid).delete()
    except Exception as e:
        print("Note on cleanup:", e)

    print("[3] Testing get_user_history for empty/new user...")
    history = history_db.get_user_history(test_uid)
    assert history == [], f"Expected empty list, got: {history}"
    print("  -> Passed: get_user_history returned empty list.")

    print("[4] Appending chat turn 1 (Tamil Question & Answer)...")
    q1 = "நெல் பயிருக்கு எந்த உரம் சிறந்தது?"
    a1 = "நெல் பயிருக்கு தழைச்சத்து, மணிச்சத்து மற்றும் சாம்பல்சத்து சமச்சீராக தேவைப்படுகிறது."
    conv1 = history_db.append_chat_turn(
        user_uid=test_uid,
        conversation_id=test_conv_id,
        question=q1,
        answer=a1,
        user_msg_id="u-msg-1",
        assistant_msg_id="a-msg-1",
    )
    assert conv1["id"] == test_conv_id
    assert len(conv1["messages"]) == 2
    assert conv1["messages"][0]["content"] == q1
    assert conv1["messages"][1]["content"] == a1
    print("  -> Passed: append_chat_turn created conversation.")

    print("[5] Reading back from Firestore...")
    loaded = history_db.get_user_history(test_uid)
    assert len(loaded) == 1, f"Expected 1 conversation, got {len(loaded)}"
    assert loaded[0]["id"] == test_conv_id
    assert loaded[0]["messages"][0]["content"] == q1
    assert loaded[0]["messages"][1]["content"] == a1
    print("  -> Passed: Firestore document successfully verified with Tamil text.")

    print("[6] Appending chat turn 2 (English follow-up)...")
    q2 = "How much urea should I apply per acre?"
    a2 = "Apply approximately 50 kg of Urea per acre in split doses."
    conv2 = history_db.append_chat_turn(
        user_uid=test_uid,
        conversation_id=test_conv_id,
        question=q2,
        answer=a2,
        user_msg_id="u-msg-2",
        assistant_msg_id="a-msg-2",
    )
    assert len(conv2["messages"]) == 4
    print("  -> Passed: follow-up turn appended.")

    print("[7] Creating a second conversation (Multiple conversations support)...")
    test_conv_2_id = "test-conv-cotton-2"
    q3 = "Cotton pest control guidance"
    a3 = "For cotton bollworm, use integrated pest management."
    history_db.append_chat_turn(
        user_uid=test_uid,
        conversation_id=test_conv_2_id,
        question=q3,
        answer=a3,
    )

    loaded_all = history_db.get_user_history(test_uid)
    assert len(loaded_all) == 2, f"Expected 2 conversations, got {len(loaded_all)}"
    print("  -> Passed: Multiple conversations preserved.")

    print("[8] Deleting one conversation...")
    remaining = history_db.delete_user_conversation(test_uid, test_conv_id)
    assert len(remaining) == 1
    assert remaining[0]["id"] == test_conv_2_id
    print("  -> Passed: Single conversation deleted successfully.")

    print("[9] Inspecting actual Firestore document structure...")
    doc = db.collection("user_history").document(test_uid).get()
    assert doc.exists
    raw_dict = doc.to_dict()
    assert "user_uid" in raw_dict, "Field 'user_uid' missing!"
    assert "data" in raw_dict, "Field 'data' missing!"
    assert raw_dict["user_uid"] == test_uid
    print(f"  -> Firestore structure confirmed: collection='user_history', doc_id='{test_uid}', fields: {list(raw_dict.keys())}")

    print("[10] Cleaning up test document...")
    db.collection("user_history").document(test_uid).delete()
    verify_deleted = db.collection("user_history").document(test_uid).get()
    assert not verify_deleted.exists
    print("  -> Cleaned up test document. All live integration checks PASSED!")


if __name__ == "__main__":
    run_live_test()
