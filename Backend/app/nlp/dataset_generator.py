# app/nlp/dataset_generator.py
import os
import csv
import uuid
import json
import logging
from typing import List, Dict
from google import genai 
from core.config import DATASETS_DIR, GEMINI_API_KEY
from nlp.dataset_ingestor import ingest_csv_to_redis

logger = logging.getLogger(__name__)

def _mock_generate_variations(seed: str, examples: int = 50) -> List[str]:
    """Fallback when Gemini API fails."""
    variations: List[str] = []
    for i in range(examples):
        text = f"{seed} variation {i+1}"
        if i % 5 == 0:
            text = text.replace("login", "loign")
        variations.append(text)
    return variations


def generate_dataset_from_prompt(
    seed_prompt: str,
    api_name: str,
    endpoint: str,
    request_obj: Dict = None,
    response_obj: Dict = None,
    examples: int = 50
) -> Dict:
    """Generate dataset using Gemini API."""
    request_obj = request_obj or {}
    response_obj = response_obj or {}

    try:
        logger.info(f"Generating dataset for: {api_name}, prompt={seed_prompt}")

        client = genai.Client(api_key=GEMINI_API_KEY)

        prompt_text = f"""
You will produce a CSV dataset. Use schema:
query,api,endpoint,request,response

Example:
lo gin pratul.ag Welcome#2025,login,<base_url>/api/login,"{{"username": "pratul.ag", "password": "Welcome#2025"}}","{{"definition": "Authenticates user with username and password credentials."}}"
"log in please. account name: frontend_pro, password: User@321",login,<base_url>/api/login,"{{"username": "frontend_pro", "password": "User@321"}}","{{"definition": "Authenticates user and starts a new session."}}"

Now generate {examples} natural language variations (including synonyms, misspellings) for:
"{seed_prompt}"
Each variation must be one row following the same CSV schema.
        """

        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt_text,
                config={"temperature": 0.7}
            )
            text_output = response.text.strip()

            if text_output.startswith("["):
                variations = json.loads(text_output)
            else:
                variations = text_output.splitlines()
        except Exception as e:
            logger.error(f"Gemini generation failed: {e}")
            variations = _mock_generate_variations(seed_prompt, examples)

        os.makedirs(DATASETS_DIR, exist_ok=True)
        file_id = uuid.uuid4().hex[:8]
        csv_path = os.path.join(DATASETS_DIR, f"{api_name}_{file_id}.csv")
        json_path = os.path.join(DATASETS_DIR, f"{api_name}_{file_id}.json")

        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["query", "api", "endpoint", "request", "response"])
            writer.writeheader()
            for q in variations:
                writer.writerow({
                    "query": q,
                    "api": api_name,
                    "endpoint": endpoint,
                    "request": json.dumps(request_obj, ensure_ascii=False),
                    "response": json.dumps(response_obj, ensure_ascii=False)
                })

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump({
                "seed_prompt": seed_prompt,
                "api_name": api_name,
                "endpoint": endpoint,
                "total_generated": len(variations),
                "variations": variations
            }, f, indent=2, ensure_ascii=False)

        logger.info(f"Dataset saved: {csv_path}")

        ingestion_summary = ingest_csv_to_redis(csv_path)

        return {
            "success": True,
            "api": api_name,
            "endpoint": endpoint,
            "csv_path": csv_path,
            "json_path": json_path,
            "num_examples": len(variations),
            "message": f"Generated {len(variations)} examples for {api_name}",
            "ingestion": ingestion_summary
        }

    except Exception as e:
        logger.exception("Dataset generation failed")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to generate dataset"
        }
