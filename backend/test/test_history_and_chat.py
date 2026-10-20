"""
Comprehensive tests for AgriGuide History Storage, Chat Turn Persistence,
and Authentication Verification.
"""

import json
import unittest
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from backend.app import history_db
from backend.app.main import app


class TestHistoryStorageUnit(unittest.TestCase):
    """Unit tests for history_db data validation, serialization, and size control."""

    def test_validate_conversation_sanitization(self):
        raw = {
            "id": "conv-1",
            "title": "  Paddy cultivation  ",
            "messages": [
                {"id": "m1", "role": "USER", "content": "How to plant paddy?", "timestamp": 12345},
                {"role": "assistant", "content": "Transplant seedlings in 20 days."},
            ],
            "createdAt": 1000,
            "updatedAt": 2000,
        }
        cleaned = history_db._validate_conversation(raw)
        self.assertEqual(cleaned["id"], "conv-1")
        self.assertEqual(cleaned["title"], "Paddy cultivation")
        self.assertEqual(len(cleaned["messages"]), 2)
        self.assertEqual(cleaned["messages"][0]["role"], "user")
        self.assertEqual(cleaned["messages"][1]["role"], "assistant")
        self.assertTrue(bool(cleaned["messages"][1]["id"]))

    def test_unicode_and_tamil_preservation(self):
        tamil_text = "நெல் சாகுபடிக்கு உரம் எவ்வளவு போட வேண்டும்?"
        tamil_answer = "ஒரு ஏக்கருக்கு 50 கிலோ யூரியா தேவைப்படுகிறது."
        raw_conv = {
            "id": "ta-conv",
            "title": tamil_text[:36],
            "messages": [
                {"id": "m-ta-1", "role": "user", "content": tamil_text, "timestamp": 1000},
                {"id": "m-ta-2", "role": "assistant", "content": tamil_answer, "timestamp": 1001},
            ],
            "createdAt": 1000,
            "updatedAt": 1001,
        }
        serialized = history_db._prune_conversations_for_size([raw_conv])
        self.assertIn("நெல் சாகுபடிக்கு", serialized)
        self.assertIn("யூரியா", serialized)
        # Parse back and verify exact string equality
        deserialized = json.loads(serialized)
        self.assertEqual(deserialized[0]["messages"][0]["content"], tamil_text)
        self.assertEqual(deserialized[0]["messages"][1]["content"], tamil_answer)

    def test_prune_oversized_payload(self):
        # Create a large conversation
        large_content = "X" * 100_000
        conversations = [
            {
                "id": f"conv-{i}",
                "title": f"Conversation {i}",
                "messages": [
                    {"id": f"m-{i}-{j}", "role": "user", "content": large_content, "timestamp": 1000 + j}
                    for j in range(12)
                ],
                "createdAt": 1000,
                "updatedAt": 2000 + i,
            }
            for i in range(12)
        ]
        serialized = history_db._prune_conversations_for_size(conversations)
        self.assertLessEqual(len(serialized.encode("utf-8")), history_db.MAX_PAYLOAD_BYTES)


class TestHistoryDbMockedFirestore(unittest.TestCase):
    """Tests for Firestore CRUD with mocked Firestore client."""

    @patch("backend.app.history_db._get_db")
    def test_get_user_history_success(self, mock_get_db):
        mock_doc = MagicMock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            "user_uid": "user-abc",
            "data": json.dumps([
                {
                    "id": "c1",
                    "title": "First chat",
                    "messages": [{"id": "m1", "role": "user", "content": "Hi", "timestamp": 10}],
                    "createdAt": 10,
                    "updatedAt": 20,
                }
            ]),
        }
        mock_db = MagicMock()
        mock_db.collection().document().get.return_value = mock_doc
        mock_get_db.return_value = mock_db

        history = history_db.get_user_history("user-abc")
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["id"], "c1")
        self.assertEqual(history[0]["title"], "First chat")

    @patch("backend.app.history_db._get_db")
    def test_get_user_history_not_found_returns_empty(self, mock_get_db):
        mock_doc = MagicMock()
        mock_doc.exists = False
        mock_db = MagicMock()
        mock_db.collection().document().get.return_value = mock_doc
        mock_get_db.return_value = mock_db

        history = history_db.get_user_history("user-nonexistent")
        self.assertEqual(history, [])

    @patch("backend.app.history_db._get_db")
    def test_save_user_history_failure_raises_runtime_error(self, mock_get_db):
        mock_db = MagicMock()
        mock_db.collection().document().set.side_effect = Exception("Firestore unavailable")
        mock_get_db.return_value = mock_db

        with self.assertRaises(RuntimeError):
            history_db.save_user_history("user-123", [{"id": "c1", "title": "Test", "messages": []}])

    @patch("backend.app.history_db.save_user_history")
    @patch("backend.app.history_db.get_user_history")
    def test_append_chat_turn_creates_and_saves(self, mock_get, mock_save):
        mock_get.return_value = []
        updated = history_db.append_chat_turn(
            user_uid="user-test",
            conversation_id="conv-new",
            question="What is urea?",
            answer="Urea is a nitrogenous fertilizer.",
            user_msg_id="u-1",
            assistant_msg_id="a-1",
        )
        self.assertEqual(updated["id"], "conv-new")
        self.assertEqual(len(updated["messages"]), 2)
        self.assertEqual(updated["messages"][0]["id"], "u-1")
        self.assertEqual(updated["messages"][1]["id"], "a-1")
        mock_save.assert_called_once()


class TestFastApiEndpoints(unittest.TestCase):
    """Integration tests for FastAPI endpoints with auth and history."""

    def setUp(self):
        self.client = TestClient(app)

    def test_health_check(self):
        res = self.client.get("/health")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json(), {"status": "healthy"})

    def test_history_missing_token(self):
        res = self.client.get("/history")
        self.assertEqual(res.status_code, 401)
        self.assertIn("Authentication required", res.json()["detail"])

    def test_history_invalid_bearer_token(self):
        res = self.client.get("/history", headers={"Authorization": "Basic 12345"})
        self.assertEqual(res.status_code, 401)
        self.assertIn("Invalid authorization header", res.json()["detail"])

    @patch("backend.app.main.verify_firebase_token")
    @patch("backend.app.main.history_db.get_user_history")
    def test_get_history_authenticated_user(self, mock_get_history, mock_verify):
        mock_verify.return_value = {"uid": "user-alice", "email": "alice@test.com"}
        mock_get_history.return_value = [
            {"id": "conv-1", "title": "Rice cultivation", "messages": [], "createdAt": 100, "updatedAt": 200}
        ]

        res = self.client.get("/history", headers={"Authorization": "Bearer valid-token"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.json()), 1)
        self.assertEqual(res.json()[0]["id"], "conv-1")
        mock_get_history.assert_called_once_with("user-alice")

    @patch("backend.app.main.verify_firebase_token")
    @patch("backend.app.main.history_db.get_user_history")
    def test_user_isolation(self, mock_get_history, mock_verify):
        """Ensure User A cannot fetch User B's history."""
        # Alice requests history
        mock_verify.return_value = {"uid": "user-alice"}
        mock_get_history.return_value = [{"id": "alice-conv", "title": "Alice's Chat", "messages": []}]
        res_alice = self.client.get("/history", headers={"Authorization": "Bearer token-alice"})
        self.assertEqual(res_alice.status_code, 200)
        self.assertEqual(res_alice.json()[0]["id"], "alice-conv")
        mock_get_history.assert_called_with("user-alice")

        # Bob requests history
        mock_verify.return_value = {"uid": "user-bob"}
        mock_get_history.return_value = [{"id": "bob-conv", "title": "Bob's Chat", "messages": []}]
        res_bob = self.client.get("/history", headers={"Authorization": "Bearer token-bob"})
        self.assertEqual(res_bob.status_code, 200)
        self.assertEqual(res_bob.json()[0]["id"], "bob-conv")
        mock_get_history.assert_called_with("user-bob")

    @patch("backend.app.main.verify_firebase_token")
    @patch("backend.app.main.history_db.save_user_history")
    def test_save_history_json_array_body(self, mock_save_history, mock_verify):
        """Verify that save_history receives the JSON array body properly without 422 error."""
        mock_verify.return_value = {"uid": "user-alice"}
        payload = [
            {"id": "c1", "title": "Test Chat", "messages": [], "createdAt": 100, "updatedAt": 200}
        ]
        res = self.client.post("/history", json=payload, headers={"Authorization": "Bearer valid-token"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json(), {"status": "success"})
        mock_save_history.assert_called_once_with("user-alice", payload)

    @patch("backend.app.main.verify_firebase_token")
    @patch("backend.app.main.history_db.save_user_history")
    def test_save_history_failure_returns_503(self, mock_save_history, mock_verify):
        mock_verify.return_value = {"uid": "user-alice"}
        mock_save_history.side_effect = RuntimeError("Firestore down")
        res = self.client.post("/history", json=[], headers={"Authorization": "Bearer valid-token"})
        self.assertEqual(res.status_code, 503)

    @patch("backend.app.main.verify_firebase_token")
    @patch("backend.app.main.AgriGuideChat")
    @patch("backend.app.main.history_db.append_chat_turn")
    @patch("backend.app.main.history_db.get_user_history")
    def test_chat_turn_persists_to_history(self, mock_get_hist, mock_append, mock_chat_cls, mock_verify):
        mock_verify.return_value = {"uid": "user-alice"}
        mock_get_hist.return_value = []
        mock_bot = MagicMock()
        mock_bot.chat.return_value = "Hello! I can help you with paddy, crops, and fertilizers."
        mock_chat_cls.return_value = mock_bot

        mock_append.return_value = {
            "id": "conv-100",
            "title": "Hi",
            "messages": [
                {"id": "u-1", "role": "user", "content": "Hi", "timestamp": 1000},
                {"id": "a-1", "role": "assistant", "content": "Hello! I can help you with paddy, crops, and fertilizers.", "timestamp": 1001},
            ],
            "createdAt": 1000,
            "updatedAt": 1001,
        }

        res = self.client.post(
            "/chat",
            json={"question": "Hi", "conversation_id": "conv-100", "user_message_id": "u-1"},
            headers={"Authorization": "Bearer token-alice"},
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["question"], "Hi")
        self.assertEqual(data["conversation_id"], "conv-100")
        self.assertIn("Hello!", data["answer"])
        mock_append.assert_called_once()


if __name__ == "__main__":
    unittest.main()
