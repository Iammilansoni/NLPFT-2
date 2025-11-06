#app/nlp/embedding_model.py

from sentence_transformers import SentenceTransformer
from app.core.config import MODEL_NAME

# load model once
_model = None

def get_model():
    """
    Returns a shared SentenceTransformer model instance.
    Loading once avoids repeated downloads / init cost.
    """
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
        _model.max_seq_length = 256
    return _model