"""
AgriGuide — Firebase Admin SDK Authentication
==============================================

Initializes Firebase Admin SDK using a service-account JSON file
referenced by the GOOGLE_APPLICATION_CREDENTIALS environment variable.

This module is intentionally designed for local Windows development
with an explicit service-account credential file.

DO NOT commit service-account JSON files to Git.
DO NOT hardcode private keys in this file.
"""

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

def _get_credential_path() -> str:
    """
    Read the service-account JSON path from the environment variable
    GOOGLE_APPLICATION_CREDENTIALS.

    Raises a clear RuntimeError if:
    - the environment variable is not set
    - the file does not exist at the specified path
    """
    env_var = "GOOGLE_APPLICATION_CREDENTIALS"
    credential_path = os.environ.get(env_var, "").strip()

    if not credential_path:
        raise RuntimeError(
            "GOOGLE_APPLICATION_CREDENTIALS is not set. "
            "Please set GOOGLE_APPLICATION_CREDENTIALS in backend/.env or your environment "
            "pointing to your Firebase service-account JSON file."
        )

    if not os.path.isfile(credential_path):
        raise RuntimeError(
            f"Firebase credential file could not be found at: {credential_path}. "
            f"Please verify the file path specified in GOOGLE_APPLICATION_CREDENTIALS."
        )

    return credential_path


def _build_credential(credential_path: str) -> credentials.Certificate:
    """
    Build a firebase_admin.credentials.Certificate from the JSON file.
    Raises RuntimeError with a clear message on failure without printing keys.
    """
    try:
        return credentials.Certificate(credential_path)
    except Exception as exc:
        raise RuntimeError(
            f"Failed to load Firebase service-account JSON certificate from '{credential_path}': {exc}"
        ) from exc


# ---------------------------------------------------------------------------
# Public initializer
# ---------------------------------------------------------------------------

def initialize_firebase() -> firebase_admin.App:
    """
    Initialize Firebase Admin SDK using the service-account JSON file.

    - If the app is already initialized, returns the existing default app.
    - Uses credentials.Certificate() (explicit credentials) so it works
      reliably on local Windows without GCP ADC configured.
    - Explicitly sets projectId to FIREBASE_PROJECT_ID matching frontend/src/firebase.js.

    Called once at module import time.
    """
    # Already initialized — return existing app immediately
    if firebase_admin._apps:
        return firebase_admin.get_app()

    credential_path = _get_credential_path()
    cred = _build_credential(credential_path)

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