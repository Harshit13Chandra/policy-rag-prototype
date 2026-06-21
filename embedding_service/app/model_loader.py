from sentence_transformers import SentenceTransformer

# Load the model at module load time
# We use "BAAI/bge-small-en-v1.5" as a smaller/faster model, which is good enough for prototype validation.
# Note: This can be swapped for "intfloat/multilingual-e5-large" later if multilingual support or higher recall is needed.
model_name = "BAAI/bge-small-en-v1.5"
model = SentenceTransformer(model_name)

dim = model.get_sentence_embedding_dimension()
print(f"Embedding model loaded successfully, dimension: {dim}")

def embed_texts(texts: list[str]) -> list[list[float]]:
    """
    Embeds a list of texts into a list of vectors.
    """
    # model.encode returns a numpy array or tensor, .tolist() converts it to a standard Python list of lists
    embeddings = model.encode(texts, normalize_embeddings=True)
    return embeddings.tolist()
