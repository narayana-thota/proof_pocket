
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.auth import router as auth_router
from app.routes.documents import router as documents_router
from app.routes.search import router as search_router
from app.routes.chat import router as chat_router
from app.routes.reminders import router as reminders_router


app = FastAPI(
    title="ProofPocket API",
    description="Personal Document and Warranty Management System",
    version="1.0.0"
)


# Configure CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Register authentication routes
app.include_router(auth_router)
app.include_router(documents_router)
app.include_router(search_router)
app.include_router(chat_router)
app.include_router(reminders_router)


@app.get("/")
def home():
    return {
        "message": "Welcome to ProofPocket API",
        "status": "Running"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}
