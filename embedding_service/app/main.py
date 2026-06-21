from fastapi import FastAPI
from pydantic import BaseModel
from .model_loader import embed_texts

app = FastAPI(title="Embedding Service")

class EmbedRequest(BaseModel):
    texts: list[str]

class EmbedResponse(BaseModel):
    embeddings: list[list[float]]
    dimension: int

@app.post("/embed", response_model=EmbedResponse)
def embed(request: EmbedRequest):
    embeddings = embed_texts(request.texts)
    dimension = len(embeddings[0]) if embeddings else 0
    return EmbedResponse(embeddings=embeddings, dimension=dimension)

@app.get("/health")
def health():
    return {"status": "ok", "model": "BAAI/bge-small-en-v1.5"}
