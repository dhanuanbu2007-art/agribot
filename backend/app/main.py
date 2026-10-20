import os
import sys
from pathlib import Path

# Add project root to sys.path so 'backend' imports work regardless of execution directory
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi import Body, Depends, FastAPI, Header, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import io
import uuid

from backend.firebase_auth import verify_firebase_token, initialize_firebase
from backend.rag.chat import AgriGuideChat
from backend.app import history_db


# ==================================================
# FastAPI Application
# ==================================================

app = FastAPI(
    title="AgriGuide RAG API",
    description="Agriculture RAG Assistant Backend",
    version="1.0.0",
)


# ==================================================
# CORS Configuration
# ==================================================

frontend_url = os.getenv(
    "FRONTEND_URL",
    ""
).strip()

allowed_origins = [
    # Production frontend
    "https://agribot-amtz.onrender.com",
    # Localhost development origins
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

if frontend_url:
    allowed_origins.extend(
        origin.strip().rstrip("/")
        for origin in frontend_url.split(",")
        if origin.strip()
    )

allowed_origins = list(
    dict.fromkeys(allowed_origins)
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================================================
# RAG Chatbot Sessions
# ==================================================

chatbots = {}  # conversation_id -> AgriGuideChat


# ==================================================
# Request Models
# ==================================================

class ChatRequest(BaseModel):
    question: str
    conversation_id: str | None = None
    user_message_id: str | None = None
    assistant_message_id: str | None = None

class TTSRequest(BaseModel):
    text: str


# ==================================================
# Firebase Authentication
# ==================================================

def get_current_user(
    authorization: str = Header(default=None)
):
    """
    Read the Firebase ID token from:

        Authorization: Bearer <token>

    and verify it using Firebase Admin SDK.
    """

    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authentication required.",
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header.",
        )

    id_token = authorization[
        len("Bearer "):
    ].strip()

    if not id_token:
        raise HTTPException(
            status_code=401,
            detail="Firebase ID token is missing.",
        )

    try:
        decoded_token = verify_firebase_token(
            id_token
        )

        return decoded_token

    except ValueError as exc:
        raise HTTPException(
            status_code=401,
            detail=str(exc),
        ) from exc


# ==================================================
# Root Endpoint
# ==================================================

@app.on_event("startup")
def startup_event():
    # Initialize Firebase Admin SDK first so history_db can use Firestore
    try:
        initialize_firebase()
        print("[Startup] Firebase Admin SDK initialized successfully.")
    except Exception as exc:
        print(f"[Startup Warning] Firebase initialization deferred: {exc}")
    try:
        history_db.init_db()
    except Exception as exc:
        print(f"[Startup Warning] History DB initialization deferred: {exc}")

@app.get("/")
def root():
    return {
        "message": "AgriGuide RAG API is running"
    }


# ==================================================
# Health Endpoint
# ==================================================

@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


# ==================================================
# Authenticated Chat Endpoint
# ==================================================

@app.post("/chat")
def chat(
    request: ChatRequest,
    current_user: dict = Depends(
        get_current_user
    ),
):
    """
    Authenticated RAG chat endpoint with automatic Firestore conversation persistence.
    """

    question = request.question.strip()
    conversation_id = (
        request.conversation_id.strip()
        if request.conversation_id and request.conversation_id.strip()
        else str(uuid.uuid4())
    )

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty.",
        )

    # Firebase UID
    user_uid = current_user.get("uid")

    if not user_uid:
        raise HTTPException(
            status_code=401,
            detail="Authenticated user UID is missing.",
        )

    # Scoped chatbot instance per user & conversation
    chat_key = f"{user_uid}:{conversation_id}"
    if chat_key not in chatbots:
        new_bot = AgriGuideChat()
        # Hydrate from history if available
        try:
            conversations = history_db.get_user_history(user_uid)
            for conv in conversations:
                if conv.get("id") == conversation_id:
                    for msg in conv.get("messages", []):
                        if msg.get("role") == "user":
                            new_bot.state.update(msg.get("content", ""))
                    break
        except Exception as exc:
            print(f"[Hydration Warning] Context hydration deferred: {exc}")
        chatbots[chat_key] = new_bot
    
    chatbot = chatbots[chat_key]

    try:
        answer = chatbot.chat(question)
    except Exception as exc:
        print(
            f"[AgriGuide Chat Error] {exc}"
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to generate answer.",
        ) from exc

    # Persist question and answer pair to Firestore
    try:
        updated_conv = history_db.append_chat_turn(
            user_uid=user_uid,
            conversation_id=conversation_id,
            question=question,
            answer=answer,
            user_msg_id=request.user_message_id,
            assistant_msg_id=request.assistant_message_id,
        )
    except Exception as exc:
        print(f"[History Save Error] Failed to persist chat turn: {exc}")
        raise HTTPException(
            status_code=500,
            detail="Failed to persist conversation history to database.",
        ) from exc

    return {
        "question": question,
        "answer": answer,
        "conversation_id": conversation_id,
        "conversation": updated_conv,
    }


# ==================================================
# History Endpoints
# ==================================================

@app.get("/history")
def get_history(current_user: dict = Depends(get_current_user)):
    user_uid = current_user.get("uid")
    if not user_uid:
        raise HTTPException(status_code=401, detail="Authenticated user UID is missing.")
    try:
        conversations = history_db.get_user_history(user_uid)
        return conversations
    except Exception as exc:
        print(f"[History] get_history Firestore unavailable: {exc}")
        raise HTTPException(status_code=503, detail="History service temporarily unavailable.")

@app.post("/history")
def save_history(
    conversations: list = Body(...),
    current_user: dict = Depends(get_current_user)
):
    user_uid = current_user.get("uid")
    if not user_uid:
        raise HTTPException(status_code=401, detail="Authenticated user UID is missing.")
    try:
        history_db.save_user_history(user_uid, conversations)
        return {"status": "success"}
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as exc:
        print(f"[History] save_history Firestore unavailable: {exc}")
        raise HTTPException(status_code=503, detail="History service temporarily unavailable.")

@app.delete("/history/{conversation_id}")
def delete_history_item(
    conversation_id: str,
    current_user: dict = Depends(get_current_user),
):
    user_uid = current_user.get("uid")
    if not user_uid:
        raise HTTPException(status_code=401, detail="Authenticated user UID is missing.")
    try:
        remaining = history_db.delete_user_conversation(user_uid, conversation_id)
        return {"status": "success", "conversations": remaining}
    except Exception as exc:
        print(f"[History] delete_history failed: {exc}")
        raise HTTPException(status_code=503, detail="Failed to delete conversation.")


# ==================================================
# TTS Endpoint (Cloud TTS for Tamil)
# ==================================================

@app.post("/tts/tamil")
def generate_tamil_tts(
    request: TTSRequest,
    current_user: dict = Depends(get_current_user),
):
    """
    Generate Tamil Text-to-Speech using a Cloud Provider.
    Falls back to gTTS if Google Cloud credentials are not configured.
    """
    text = request.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text cannot be empty.")
    
    # 1. Try Google Cloud TTS (Premium) if GOOGLE_APPLICATION_CREDENTIALS exists
    if "GOOGLE_APPLICATION_CREDENTIALS" in os.environ:
        try:
            from google.cloud import texttospeech
            client = texttospeech.TextToSpeechClient()
            synthesis_input = texttospeech.SynthesisInput(text=text)
            voice = texttospeech.VoiceSelectionParams(
                language_code="ta-IN",
                name="ta-IN-Standard-A"
            )
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3
            )
            response = client.synthesize_speech(
                input=synthesis_input, voice=voice, audio_config=audio_config
            )
            audio_bytes = response.audio_content
            return Response(
                content=audio_bytes, 
                media_type="audio/mpeg",
                headers={
                    "Content-Disposition": "inline; filename=speech.mp3",
                    "Content-Length": str(len(audio_bytes)),
                    "Accept-Ranges": "bytes",
                    "Cache-Control": "no-cache",
                }
            )
        except Exception as e:
            print(f"[Google Cloud TTS Error] {e} - Falling back to gTTS")
            
    # 2. Fallback to gTTS (Free, no API keys required)
    try:
        from gtts import gTTS
        tts = gTTS(text, lang='ta')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        audio_bytes = fp.getvalue()
        return Response(
            content=audio_bytes, 
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "inline; filename=speech.mp3",
                "Content-Length": str(len(audio_bytes)),
                "Accept-Ranges": "bytes",
                "Cache-Control": "no-cache",
            }
        )
    except Exception as e:
        print(f"[gTTS Error] {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate Tamil speech from cloud providers."
        ) from e


# ==================================================
# Production Entry Point (Render / Local)
# ==================================================

if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
    )