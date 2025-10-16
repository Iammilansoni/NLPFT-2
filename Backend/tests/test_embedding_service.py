
import pytest
import numpy as np
from app.services.embedding_service import EmbeddingService, get_embedding_service


@pytest.fixture
def embedding_service():
    return get_embedding_service()


class TestEmbeddingGeneration:
    
    def test_generate_single_embedding(self, embedding_service):
        text = "login using username and password"
        
        embedding = embedding_service.generate_embedding(text)
        
        assert embedding.shape == (384,), "Embedding should be 384-dimensional"
        
        norm = np.linalg.norm(embedding)
        assert abs(norm - 1.0) < 0.01, "Embedding should be L2 normalized"
    
    def test_generate_batch_embeddings(self, embedding_service):
        texts = [
            "login with username and password",
            "sign in to the system",
            "authenticate using credentials",
            "log me in now"
        ]
        
        embeddings = embedding_service.generate_embeddings_batch(texts)
        
        assert embeddings.shape == (4, 384), "Should generate 4 embeddings of 384 dimensions"
        
        for emb in embeddings:
            norm = np.linalg.norm(emb)
            assert abs(norm - 1.0) < 0.01, "Each embedding should be L2 normalized"
    
    def test_empty_batch(self, embedding_service):
        embeddings = embedding_service.generate_embeddings_batch([])
        assert embeddings.shape == (0,), "Empty input should return empty array"
    
    def test_embedding_similarity(self, embedding_service):
        text1 = "login with username and password"
        text2 = "sign in using username and password"
        text3 = "logout from the system"
        
        emb1 = embedding_service.generate_embedding(text1)
        emb2 = embedding_service.generate_embedding(text2)
        emb3 = embedding_service.generate_embedding(text3)
        
        sim_similar = embedding_service.compute_similarity(emb1, emb2, metric="cosine")
        sim_different = embedding_service.compute_similarity(emb1, emb3, metric="cosine")
        
        assert sim_similar > sim_different, "Similar texts should have higher similarity"
        assert sim_similar > 0.7, "Similar texts should have high similarity score"


class TestTokenCounting:
    
    def test_simple_text(self, embedding_service):
        text = "login using username and password"
        count = embedding_service.approximate_token_count(text)
        
        assert 5 <= count <= 7, f"Expected 5-7 tokens, got {count}"
    
    def test_complex_text(self, embedding_service):
        text = "Please log in with username 'user123' and password 'pass@123'!"
        count = embedding_service.approximate_token_count(text)
        
        assert count > 10, "Should count punctuation as separate tokens"
    
    def test_empty_text(self, embedding_service):
        count = embedding_service.approximate_token_count("")
        assert count == 0, "Empty text should have 0 tokens"


class TestChunking:
    
    def test_basic_chunking(self, embedding_service):
        texts = [
            "This is text one with some words.",
            "This is text two with more words.",
            "This is text three with additional words.",
            "This is text four with even more words.",
        ] * 10
        
        chunks = embedding_service.chunk_texts(
            texts, 
            target_min_tokens=350, 
            target_max_tokens=450
        )
        
        assert len(chunks) > 0, "Should create at least one chunk"
        
        for chunk in chunks:
            assert "chunk_id" in chunk
            assert "paraphrase_ids" in chunk
            assert "approx_token_count" in chunk
            assert "text_joined" in chunk
            assert "embedding_model" in chunk
            assert "start_index" in chunk
            assert "end_index" in chunk
    
    def test_chunk_token_limits(self, embedding_service):
        texts = ["This is a test sentence with about ten words here."] * 50
        
        chunks = embedding_service.chunk_texts(
            texts,
            target_min_tokens=100,
            target_max_tokens=200
        )
        
        for i, chunk in enumerate(chunks[:-1]):
            token_count = chunk["approx_token_count"]
            assert token_count >= 100, f"Chunk {i} has {token_count} tokens, below minimum"
            assert token_count <= 200, f"Chunk {i} has {token_count} tokens, above maximum"
    
    def test_empty_texts(self, embedding_service):
        chunks = embedding_service.chunk_texts([])
        assert len(chunks) == 0, "Empty input should produce no chunks"
    
    def test_single_text(self, embedding_service):
        texts = ["This is a single text for chunking."]
        
        chunks = embedding_service.chunk_texts(texts)
        
        assert len(chunks) == 1, "Single text should produce one chunk"
        assert chunks[0]["paraphrase_ids"] == [0]


class TestEmbedChunks:
    
    def test_embed_chunks(self, embedding_service):
        chunks = [
            {
                "chunk_id": 0,
                "text_joined": "login with username\nsign in with password",
                "paraphrase_ids": [0, 1],
                "approx_token_count": 8
            },
            {
                "chunk_id": 1,
                "text_joined": "logout from system\nsign out now",
                "paraphrase_ids": [2, 3],
                "approx_token_count": 6
            }
        ]
        
        enriched_chunks = embedding_service.embed_chunks(chunks)
        
        assert len(enriched_chunks) == 2
        
        for chunk in enriched_chunks:
            assert "embedding" in chunk, "Chunk should have embedding field"
            assert "vector_dim" in chunk, "Chunk should have vector_dim field"
            
            assert isinstance(chunk["embedding"], list)
            assert len(chunk["embedding"]) == 384
            
            assert chunk["vector_dim"] == 384
    
    def test_embed_empty_chunks(self, embedding_service):
        enriched = embedding_service.embed_chunks([])
        assert enriched == [], "Empty chunks should return empty list"


class TestSimilaritySearch:
    
    def test_find_similar_chunks(self, embedding_service):
        texts = [
            "login with username and password",
            "sign in to the system",
            "logout from account",
            "create a new user",
            "register new account"
        ]
        
        embeddings = embedding_service.generate_embeddings_batch(texts)
        
        query = "authenticate with username and password"
        query_emb = embedding_service.generate_embedding(query)
        
        similar = embedding_service.find_similar_chunks(query_emb, embeddings, top_k=3)
        
        assert len(similar) == 3, "Should return top 3 results"
        
        top_idx, top_score = similar[0]
        assert top_idx in [0, 1], "Most similar should be login or sign in"
        assert top_score > 0.5, "Top score should be reasonably high"
        
        scores = [s[1] for s in similar]
        assert scores == sorted(scores, reverse=True), "Results should be sorted by similarity"


class TestModelInfo:
    
    def test_get_model_info(self, embedding_service):
        info = embedding_service.get_model_info()
        
        assert info["model_name"] == "sentence-transformers/all-MiniLM-L6-v2"
        assert info["vector_dim"] == 384
        assert info["device"] == "cpu"
        assert info["similarity_metric"] == "cosine"
        assert info["normalization"] == "L2"
        assert info["framework"] == "sentence-transformers"


class TestSingletonPattern:
    
    def test_singleton_instance(self):
        service1 = get_embedding_service()
        service2 = get_embedding_service()
        
        assert service1 is service2, "Should return same instance (singleton)"


@pytest.mark.parametrize("text,expected_min,expected_max", [
    ("login", 1, 2),
    ("sign in now", 3, 4),
    ("authenticate with username and password", 5, 7),
    ("Please log me in with my credentials!", 7, 10),
])
def test_token_counting_parametrized(embedding_service, text, expected_min, expected_max):
    count = embedding_service.approximate_token_count(text)
    assert expected_min <= count <= expected_max, \
        f"Token count {count} not in expected range [{expected_min}, {expected_max}] for text: '{text}'"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
