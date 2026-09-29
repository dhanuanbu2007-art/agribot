import os

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.firebase_auth import verify_firebase_token
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
    conversation_id: str


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
    history_db.init_db()

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
    Authenticated RAG chat endpoint.
    """

    question = request.question.strip()
    conversation_id = request.conversation_id.strip() if request.conversation_id else "default"

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

    # Scoped chatbot instance
    if conversation_id not in chatbots:
        new_bot = AgriGuideChat()
        # Hydrate from history if available
        conversations = history_db.get_user_history(user_uid)
        for conv in conversations:
            if conv.get("id") == conversation_id:
                for msg in conv.get("messages", []):
                    if msg.get("role") == "user":
                        new_bot.state.update(msg.get("content", ""))
                break
        chatbots[conversation_id] = new_bot
    
    chatbot = chatbots[conversation_id]

    try:
        answer = chatbot.chat(question)

        return {
            "question": question,
            "answer": answer,
        }

    except Exception as exc:
        print(
            f"[AgriGuide Chat Error] {exc}"
        )

        raise HTTPException(
            status_code=500,
            detail="Failed to generate answer.",
        ) from exc


# ==================================================
# History Endpoints
# ==================================================

@app.get("/history")
def get_history(current_user: dict = Depends(get_current_user)):
    user_uid = current_user.get("uid")
    conversations = history_db.get_user_history(user_uid)
    return conversations

@app.post("/history")
def save_history(
    conversations: list,
    current_user: dict = Depends(get_current_user)
):
    user_uid = current_user.get("uid")
    history_db.save_user_history(user_uid, conversations)
    return {"status": "success"}


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