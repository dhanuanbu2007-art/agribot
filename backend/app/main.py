from fastapi import FastAPI
from pydantic import BaseModel

from backend.rag.chat import AgriGuideChat


app = FastAPI(
    title="AgriGuide RAG",
    description="Agriculture Knowledge & Advisory Assistant",
    version="1.0.0"
)


chatbot = AgriGuideChat()


class ChatRequest(BaseModel):
    question: str


@app.get("/")
def root():
    return {
        "message": "AgriGuide RAG API is running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.post("/chat")
def chat(request: ChatRequest):

    answer = chatbot.chat(request.question)

    return {
        "question": request.question,
        "answer": answer
    }