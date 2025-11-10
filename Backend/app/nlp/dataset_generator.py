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
import logging

logger = logging.getLogger(__name__)

def _mock_generate_variations(seed: str, examples: int = 50) -> List[str]:
    """
    Lightweight fallback generator that produces simple variations of the seed query.
    You can replace this with a more sophisticated LLM prompt if OPENAI API key is provided.
    """
    variations: List[str] = []
    for i in range(examples):
        variations.append(f"{seed} variation {i+1}")
        # introduce a few misspellings as basic noise
        if i % 5 == 0:
            variations.append(seed.replace("login", "loign"))
    return variations

def generate_dataset_from_prompt(
    seed_prompt: str,
    api_name: str,
    endpoint: str,
    request_obj: Dict = None,
    response_obj: Dict = None,
    examples: int = 50
) -> Dict:
    """
    Generate a dataset CSV file from a natural-language seed prompt provided by the user,
    then ingest that CSV into Redis (vector store) using your ingestion pipeline.

    Args:
        seed_prompt (str): The natural-language query seed that describes the scenario, e.g., "login as admin ..."
        api_name (str): The API name (intent) that this dataset corresponds to, e.g., "login"
        endpoint (str): The API endpoint path, e.g., "/api/login"
        request_obj (Dict, optional): Example request object payload metadata
        response_obj (Dict, optional): Example response object metadata
        examples (int): Number of variations/rows to generate in the dataset.

    Returns:
        Dict: {
            "success": bool,
            "api": str,
            "endpoint": str,
            "csv_path": str,
            "json_path": str,
            "num_examples": int,
            "message": str,
            "error": str (only present on failure)
        }
    """
    request_obj = request_obj or {}
    response_obj = response_obj or {}

    try:
        logger.info(f"Starting dataset generation: seed_prompt={seed_prompt}, api_name={api_name}, endpoint={endpoint}, examples={examples}")

        # 1) Generate variations of the seed prompt
        if OPENAI_API_KEY:
            openai.api_key = OPENAI_API_KEY
            prompt_text = (
    "You will produce a CSV dataset. Use the schema: query, api, endpoint, request, response\n"
    "Include actual CSV rows. For example:\n"
    "lo gin pratul.ag Welcome#2025,login,<base_url>/api/login,\"{""username"": ""pratul.ag"", ""password"": ""Welcome#2025""}\","
    "\"{""definition"": ""Authenticates user with username and password credentials and starts a new session.""}\"\n"
    "\"log in please. account name: frontend_pro, password: User@321\",login,<base_url>/api/login,"
    "\"{""username"": ""frontend_pro"", ""password"": ""User@321""}\","
    "\"{""definition"": ""Authenticates user with username and password credentials and starts a new session.""}\"\n\n"
    f"Now generate a JSON array of natural-language query variations including synonyms and misspellings for the seed query: {seed_prompt}. "
    "After that, transform each variation into a full CSV row following the schema, filling api, endpoint, request, and response accordingly. Return only the CSV content (rows) or a JSON-encoded array of rows."
)
            try:
                resp = openai.ChatCompletion.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt_text}],
                    temperature=0.7,
                    max_tokens=1500,
                )
                content = resp.choices[0].message.content
                variations = json.loads(content)
                if not isinstance(variations, list):
                    logger.warning("LLM returned non-list, falling back to mock variations")
                    variations = _mock_generate_variations(seed_prompt, examples)
            except Exception as e:
                logger.error(f"OpenAI call failed: {e}", exc_info=True)
                variations = _mock_generate_variations(seed_prompt, examples)
        else:
            variations = _mock_generate_variations(seed_prompt, examples)

        # Limit to requested number of rows
        variations = variations[:examples]
        total_generated = len(variations)

        # 2) Build filesystem paths and save CSV + optional JSON metadata
        os.makedirs(DATASETS_DIR, exist_ok=True)
        filename_base = f"{api_name}_{uuid.uuid4().hex[:8]}"
        csv_filename = f"{filename_base}.csv"
        csv_path = os.path.join(DATASETS_DIR, csv_filename)
        json_filename = f"{filename_base}.json"
        json_path = os.path.join(DATASETS_DIR, json_filename)

        # Write the CSV file with required columns
        with open(csv_path, "w", newline="", encoding="utf-8") as f_csv:
            writer = csv.DictWriter(
                f_csv,
                fieldnames=["query", "api", "endpoint", "request", "response"]
            )
            writer.writeheader()
            for q in variations:
                writer.writerow({
                    "query": q,
                    "api": api_name,
                    "endpoint": endpoint,
                    "request": json.dumps(request_obj, ensure_ascii=False),
                    "response": json.dumps(response_obj, ensure_ascii=False),
                })

        # Save metadata to JSON file optionally
        metadata = {
            "seed_prompt": seed_prompt,
            "api_name": api_name,
            "endpoint": endpoint,
            "request_obj": request_obj,
            "response_obj": response_obj,
            "total_generated": total_generated,
            "variations": variations
        }
        with open(json_path, "w", encoding="utf-8") as f_json:
            json.dump(metadata, f_json, ensure_ascii=False, indent=2)

        logger.info(f"Dataset files saved: csv_path={csv_path}, json_path={json_path}")

        # 3) Ingest dataset into Redis (vector store)
        ingestion_summary = ingest_csv_to_redis(csv_path)
        logger.info(f"Ingestion summary: {ingestion_summary}")

        return {
            "success": True,
            "api": api_name,
            "endpoint": endpoint,
            "csv_path": csv_path,
            "json_path": json_path,
            "num_examples": total_generated,
            "message": f"Generated {total_generated} examples for {api_name}",
            "ingestion": ingestion_summary
        }

    except Exception as e:
        logger.error(f"Error generating dataset: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to generate dataset: {str(e)}"
        }
