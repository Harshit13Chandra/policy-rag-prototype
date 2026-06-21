import re
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.api.auth_routes import router as auth_router
from app.api.document_routes import router as document_router
from app.api.chat_routes import router as chat_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Policy RAG backend starting...")
    settings = get_settings()
    
    # Mask password in URL as a sanity check
    masked_url = re.sub(r"(://)(.*?)(@)", r"\1***\3", settings.database_url)
    print(f"Database URL: {masked_url}")
    
    yield

app = FastAPI(lifespan=lifespan)

app.include_router(auth_router)
app.include_router(document_router)
app.include_router(chat_router)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok"}
