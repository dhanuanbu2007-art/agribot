"""
AgriGuide — Firebase Admin SDK Authentication
==============================================

Initializes Firebase Admin SDK using a service-account JSON file or string
referenced by FIREBASE_SERVICE_ACCOUNT_JSON or GOOGLE_APPLICATION_CREDENTIALS.

Supports:
- Local Windows development (via file path in GOOGLE_APPLICATION_CREDENTIALS)
- Cloud/Render deployment (via raw JSON string or Secret File path in
  FIREBASE_SERVICE_ACCOUNT_JSON or GOOGLE_APPLICATION_CREDENTIALS)

DO NOT commit service-account JSON files to Git.
DO NOT hardcode private keys in this file.
"""

import json
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

import firebase_admin
from firebase_admin import auth, credentials

# ---------------------------------------------------------------------------
# Load environment variables (.env)
# ---------------------------------------------------------------------------

_BACKEND_DIR = Path(__file__).resolve().parent
_BACKEND_ENV = _BACKEND_DIR / ".env"
_ROOT_ENV = _BACKEND_DIR.parent / ".env"

if _BACKEND_ENV.exists():
    load_dotenv(_BACKEND_ENV)
elif _ROOT_ENV.exists():
    load_dotenv(_ROOT_ENV)
else:
    load_dotenv()


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Must match the Firebase project used by the React frontend (frontend/src/firebase.js).
FIREBASE_PROJECT_ID = "agriguide-838da"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _build_credential() -> credentials.Certificate:
    """
    Build a firebase_admin.credentials.Certificate from either:
    1. A raw JSON string or file path in FIREBASE_SERVICE_ACCOUNT_JSON
    2. A file path or raw JSON string in GOOGLE_APPLICATION_CREDENTIALS

    Raises a clear RuntimeError if credentials are missing or invalid.
    """
    # 1. Check FIREBASE_SERVICE_ACCOUNT_JSON (recommended for Render cloud env vars)
    raw_env_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON", "").strip()
    if raw_env_json:
        if raw_env_json.startswith("{"):
            try:
                cert_dict = json.loads(raw_env_json)
                return credentials.Certificate(cert_dict)
            except Exception as exc:
                raise RuntimeError(
                    f"Failed to parse FIREBASE_SERVICE_ACCOUNT_JSON as valid JSON: {exc}"
                ) from exc
        elif os.path.isfile(raw_env_json):
            try:
                return credentials.Certificate(raw_env_json)
            except Exception as exc:
                raise RuntimeError(
                    f"Failed to load service-account certificate from file '{raw_env_json}': {exc}"
                ) from exc

    # 2. Check GOOGLE_APPLICATION_CREDENTIALS (standard GCP env var, supports file path or raw JSON)
    cred_val = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "").strip()
    if cred_val:
        if cred_val.startswith("{"):
            try:
                cert_dict = json.loads(cred_val)
                return credentials.Certificate(cert_dict)
            except Exception as exc:
                raise RuntimeError(
                    f"Failed to parse GOOGLE_APPLICATION_CREDENTIALS as valid JSON: {exc}"
                ) from exc
        elif os.path.isfile(cred_val):
            try:
                return credentials.Certificate(cred_val)
            except Exception as exc:
                raise RuntimeError(
                    f"Failed to load service-account certificate from file '{cred_val}': {exc}"
                ) from exc
        else:
            raise RuntimeError(
                f"Firebase credential file could not be found at: {cred_val}. "
                "Please verify the file path specified in GOOGLE_APPLICATION_CREDENTIALS."
            )

    # 3. Neither environment variable is configured
    raise RuntimeError(
        "Neither GOOGLE_APPLICATION_CREDENTIALS nor FIREBASE_SERVICE_ACCOUNT_JSON is set. "
        "For local development: set GOOGLE_APPLICATION_CREDENTIALS to your local service-account JSON path in backend/.env. "
        "For Render/cloud deployment: set FIREBASE_SERVICE_ACCOUNT_JSON with the contents of your service-account JSON."
    )


# ---------------------------------------------------------------------------
# Public initializer
# ---------------------------------------------------------------------------

def initialize_firebase() -> firebase_admin.App:
    """
    Initialize Firebase Admin SDK.

    - If the app is already initialized, returns the existing default app.
    - Uses credentials.Certificate() (explicit credentials) so it works
      reliably on local Windows and Linux cloud hosts (Render).
    - Explicitly sets projectId to FIREBASE_PROJECT_ID matching frontend/src/firebase.js.

    Called once at module import time.
    """
    # Already initialized — return existing app immediately
    if firebase_admin._apps:
        return firebase_admin.get_app()

    cred = _build_credential()

    try:
        app = firebase_admin.initialize_app(
            cred,
            {
                "projectId": FIREBASE_PROJECT_ID,
            },
        )

        print(
            f"[AgriGuide Firebase] Admin SDK initialized successfully for project: {FIREBASE_PROJECT_ID}"
        )

        return app

    except Exception as exc:
        raise RuntimeError(
            f"Failed to initialize Firebase Admin SDK for project '{FIREBASE_PROJECT_ID}': {exc}"
        ) from exc


# ---------------------------------------------------------------------------
# Token verification
# ---------------------------------------------------------------------------

def verify_firebase_token(id_token: str) -> dict:
    """
    Verify a Firebase ID token sent by the React frontend as:
        Authorization: Bearer <id_token>

    Returns:
        dict: The decoded token payload containing uid, email, etc.

    Raises:
        ValueError: With a clean error message for expected token errors.
    """
    if not id_token or not id_token.strip():
        raise ValueError("Firebase ID token is missing.")

    try:
        decoded_token = auth.verify_id_token(id_token.strip())
        return decoded_token

    except auth.ExpiredIdTokenError as exc:
        raise ValueError("Firebase ID token has expired.") from exc

    except auth.RevokedIdTokenError as exc:
        raise ValueError("Firebase ID token has been revoked.") from exc

    except auth.InvalidIdTokenError as exc:
        raise ValueError("Firebase ID token is invalid.") from exc

    except auth.UserDisabledError as exc:
        raise ValueError("Firebase user account is disabled.") from exc

    except Exception as exc:
        # Log error on server without leaking sensitive info to client
        print(
            f"[Firebase Auth Error] {type(exc).__name__}: {exc}"
        )
        raise ValueError("Firebase authentication failed.") from exc


# ---------------------------------------------------------------------------
# Initialize on module import
# ---------------------------------------------------------------------------

initialize_firebase()