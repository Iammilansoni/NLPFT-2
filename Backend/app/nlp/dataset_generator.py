# nlp/dataset_generator.py
import os
import csv
import uuid
import json
from typing import List, Dict
from core.config import DATASETS_DIR, OPENAI_API_KEY
from nlp.embedding_model import get_model
from nlp.dataset_ingestor import ingest_csv_to_redis
import openai

os.makedirs(DATASETS_DIR, exist_ok=True)

def _mock_generate_variations(seed: str, examples: int = 50) -> List[str]:
    """
    Lightweight fallback generator that produces simple variations.
    Replace with a stronger LLM prompt if OPENAI_API_KEY is present.
    """
    variations = []
    for i in range(examples):
        variations.append(f"{seed} variation {i+1}")
        # add a few misspellings
        if i % 5 == 0:
            variations.append(seed.replace("login", "loign"))
    return variations

def generate_dataset_from_prompt(seed_prompt: str, examples: int = 50, api_name: str = "login", endpoint: str = "<base_url>/api/login", request_obj: dict = None, response_obj: dict = None):
    """
    Generate a dataset CSV file using an LLM (OpenAI) if available,
    or fallback to a simple generator. Then ingest the CSV into Redis.
    Returns the created CSV path and ingestion summary.
    """
    request_obj = request_obj or {"username": "user", "password": "pass"}
    response_obj = response_obj or {"definition": "Authenticates user with credentials"}

    # 1) Generate variations
    if OPENAI_API_KEY:
        openai.api_key = OPENAI_API_KEY
        prompt = (
            "Generate a JSON array of short natural language query variations (including synonyms and misspellings) "
            f"for the seed query: {seed_prompt}\nReturn only a JSON array of strings."
        )
        try:
            resp = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1500,
            )
            content = resp.choices[0].message.content
            variations = json.loads(content)
            # ensure it's a list
            if not isinstance(variations, list):
                variations = _mock_generate_variations(seed_prompt, examples)
        except Exception:
            variations = _mock_generate_variations(seed_prompt, examples)
    else:
        variations = _mock_generate_variations(seed_prompt, examples)

    # limit to requested number
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

    # 3) Ingest into Redis (you may call this async/background from the route)
    ingestion_summary = ingest_csv_to_redis(csv_path)
    return {"csv_path": csv_path, "ingestion": ingestion_summary}
