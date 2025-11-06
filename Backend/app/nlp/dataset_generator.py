# app/nlp/dataset_generator.py
import os
import csv
import uuid
import json
from typing import List, Dict
from app.core.config import DATASETS_DIR, GEMINI_API_KEY
from app.nlp.embedding_model import get_model
from app.nlp.dataset_ingestor import ingest_csv_to_redis

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

os.makedirs(DATASETS_DIR, exist_ok=True)

def _mock_generate_variations(seed: str, examples: int = 50) -> List[str]:
    """
    Lightweight fallback generator that produces simple variations.
    Replace with a stronger LLM prompt if OPENAI_API_KEY is present.
    """
    variations = []
    for i in range(examples):
        variations.append(f"{seed} variation {i+1}")
        if i % 5 == 0:
            variations.append(seed.replace("login", "loign"))
    return variations

def generate_dataset_from_prompt(seed_prompt: str, examples: int = 50, api_name: str = "login", endpoint: str = "<base_url>/api/login", request_obj: dict = None, response_obj: dict = None):
    """
    Generate a dataset CSV file using Google Gemini API if available,
    or fallback to a simple generator. Then ingest the CSV into Redis.
    Returns the created CSV path and ingestion summary.
    """
    request_obj = request_obj or {"username": "user", "password": "pass"}
    response_obj = response_obj or {"definition": "Authenticates user with credentials"}

    # 1) Generate variations
    if GEMINI_AVAILABLE and GEMINI_API_KEY:
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel('gemini-pro')
            prompt = (
                "Generate a JSON array of short natural language query variations (including synonyms and misspellings) "
                f"for the seed query: {seed_prompt}\nReturn only a JSON array of strings, no markdown or code blocks."
            )
            response = model.generate_content(prompt)
            content = response.text.strip()
            
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            variations = json.loads(content)
            if not isinstance(variations, list):
                variations = _mock_generate_variations(seed_prompt, examples)
        except Exception as e:
            print(f"Gemini generation failed: {e}. Using mock generator.")
            variations = _mock_generate_variations(seed_prompt, examples)
    else:
        variations = _mock_generate_variations(seed_prompt, examples)

    variations = variations[:examples]

    # 2) Build rows and write CSV
    filename = f"generated_{uuid.uuid4().hex[:8]}.csv"
    csv_path = os.path.join(DATASETS_DIR, filename)
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["query", "api", "endpoint", "request", "response"])
        writer.writeheader()
        for q in variations:
            writer.writerow({
                "query": q,
                "api": api_name,
                "endpoint": endpoint,
                "request": json.dumps(request_obj, ensure_ascii=False),
                "response": json.dumps(response_obj, ensure_ascii=False),
            })

    # 3) Ingest into Redis
    ingestion_summary = ingest_csv_to_redis(csv_path)
    return {"csv_path": csv_path, "ingestion": ingestion_summary}