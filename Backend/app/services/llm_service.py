# llm_service.py (Final Enhanced Version with Synonym + Typo + Fuzzy Support)

import logging
import json
import time
import requests
from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd  # type: ignore[reportMissingModuleSource]
import os
import struct
import random

from sentence_transformers import SentenceTransformer
import redis
from rapidfuzz import fuzz, process

logger = logging.getLogger(__name__)


class LLMService:
    DEFAULT_MODEL = "mistralai/Mistral-7B-Instruct-v0.2"
    API_BASE_URL = "https://api-inference.huggingface.co/models"
    EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

    def __init__(
        self,
        model_name: Optional[str] = None,
        api_token: Optional[str] = None,
        max_length: int = 2048,
        timeout: int = 120,
    ):
        self.model_name = model_name or self.DEFAULT_MODEL
        self.api_token = api_token
        self.max_length = max_length
        self.timeout = timeout
        self.api_url = f"{self.API_BASE_URL}/{self.model_name}"
        self.headers = {"Content-Type": "application/json"}
        if self.api_token:
            self.headers["Authorization"] = f"Bearer {self.api_token}"
        logger.info(f"✅ LLMService initialized with model {self.model_name}")

        
        self.embedding_model = SentenceTransformer(self.EMBEDDING_MODEL)

        
        self.synonyms = {
            "login": ["sign in", "log in", "authenticate", "access", "enter account"],
            "logout": ["sign out", "log out", "exit", "terminate session"],
            "register": ["sign up", "create account", "enroll", "open account"],
            "password": ["passcode", "credential", "secret", "pwd"],
            "username": ["user id", "login id", "handle", "account name"],
        }

        self.typo_patterns = {
            "login": ["logn", "loign", "lgin"],
            "password": ["pasword", "passwrd", "paswrd", "passwor"],
            "credentials": ["credentails", "crdentials", "credntials"],
            "username": ["usrname", "usrename", "usernme"],
        }

    # -------------------------------------------------------------------------------------
    # CORE API CALL
    # -------------------------------------------------------------------------------------
    def _call_api(self, payload: Dict[str, Any], max_retries: int = 3, retry_delay: int = 5):
        for attempt in range(max_retries):
            try:
                response = requests.post(self.api_url, headers=self.headers, json=payload, timeout=self.timeout)

                if response.status_code in (503, 429):
                    wait_time = response.json().get("estimated_time", retry_delay)
                    logger.warning(f"Model unavailable (status {response.status_code}), retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue

                response.raise_for_status()
                return response.json()

            except requests.exceptions.RequestException as e:
                logger.error(f"Request error: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    raise RuntimeError(f"API request failed after {max_retries} retries")

        raise RuntimeError("API failed after all retries")

    # -------------------------------------------------------------------------------------
    # TEXT GENERATION
    # -------------------------------------------------------------------------------------
    def generate_text(
        self,
        prompt: str,
        max_new_tokens: int = 1000,
        temperature: float = 0.7,
        top_p: float = 0.9,
        top_k: int = 50,
        repetition_penalty: float = 1.1,
    ) -> str:
        payload: Dict[str, Any] = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": max_new_tokens,
                "temperature": temperature,
                "top_p": top_p,
                "top_k": top_k,
                "repetition_penalty": repetition_penalty,
                "return_full_text": False,
                "truncate": True,
                "do_sample": True,
                "stop": ["<JSON_END>"],
            },
            "options": {"wait_for_model": True, "use_cache": False},
        }

        data = self._call_api(payload)
        generated_text: str = ""
        if isinstance(data, list) and data and isinstance(data[0], dict):
            generated_text = str(data[0].get("generated_text", ""))  # type: ignore[reportUnknownMemberType]
        elif isinstance(data, dict):
            generated_text = str(data.get("generated_text", ""))  # type: ignore[reportUnknownMemberType]
        return generated_text.strip()

    # -------------------------------------------------------------------------------------
    # SYNTHETIC DATASET GENERATION
    # -------------------------------------------------------------------------------------
    def generate_synthetic_dataset(
        self, base_url: str, apis: List[str], per_api_paraphrases_min: int = 15, per_api_paraphrases_max: int = 25
    ) -> Dict[str, Any]:
        prompt = self._build_dataset_prompt(base_url, apis, per_api_paraphrases_min, per_api_paraphrases_max)
        try:
            generated = self.generate_text(prompt)
            dataset = self._extract_json_from_text(generated)
            if dataset:
                logger.info("✅ LLM-generated dataset parsed successfully")
                return self._augment_dataset(dataset)
            raise ValueError("Invalid JSON from model")
        except Exception as e:
            logger.warning(f"❌ LLM generation failed ({e}), using fallback dataset")
            dataset = self._generate_fallback_dataset(base_url, apis, per_api_paraphrases_min)
            return self._augment_dataset(dataset)

    # -------------------------------------------------------------------------------------
    # PROMPT BUILDER
    # -------------------------------------------------------------------------------------
    def _build_dataset_prompt(self, base_url: str, apis: List[str], per_api_paraphrases_min: int, per_api_paraphrases_max: int) -> str:
        apis_str = ", ".join(apis)
        return f"""
Generate JSON dataset with paraphrases between <JSON_START> and <JSON_END> only.

Rules:
- For each API, include {per_api_paraphrases_min}-{per_api_paraphrases_max} variants.
- Include synonyms, typos, polite and imperative styles.

<JSON_START>
{{
  "project": {{
    "name": "AI Automation Dataset",
    "base_url": "{base_url}",
    "embedding_model": "{self.EMBEDDING_MODEL}",
    "vector_similarity": "cosine"
  }},
  "datasets": []
}}
<JSON_END>

APIs: {apis_str}
        """

    # -------------------------------------------------------------------------------------
    # JSON EXTRACTION
    # -------------------------------------------------------------------------------------
    def _extract_json_from_text(self, text: str) -> Optional[Dict[str, Any]]:
        start, end = text.find("<JSON_START>"), text.find("<JSON_END>")
        if start == -1 or end == -1:
            return None
        raw = text[start + len("<JSON_START>"):end].strip()
        try:
            return json.loads(raw)
        except Exception:
            return None

    # -------------------------------------------------------------------------------------
    # FALLBACK DATASET (STATIC)
    # -------------------------------------------------------------------------------------
    def _generate_fallback_dataset(self, base_url: str, apis: List[str], per_api_paraphrases: int) -> Dict[str, Any]:
        dataset: Dict[str, Any] = {
            "project": {
                "name": "AI Automation Dataset",
                "base_url": base_url,
                "embedding_model": self.EMBEDDING_MODEL,
                "vector_similarity": "cosine",
            },
            "datasets": [],
        }
        for api in apis:
            nl_inputs: List[Dict[str, Any]] = [
                {"id": i, "text": f"{api} example {i}", "token_count": 3, "char_count": len(api) + 10, "style": "synonym"}
                for i in range(per_api_paraphrases)
            ]
            dataset_item: Dict[str, Any] = {
                "api": api,
                "endpoint": f"{base_url}/api/{api}",
                "request": {},
                "response": {"definition": f"Handles {api} operation"},
                "paraphrase_type": f"{api}_synthetic",
                "nl_inputs": nl_inputs,
                "chunks": [],
            }
            datasets_list: List[Any] = dataset.get("datasets", [])
            datasets_list.append(dataset_item)  # type: ignore[reportUnknownMemberType]
        return dataset

    # -------------------------------------------------------------------------------------
    # SYNONYM + TYPO AUGMENTATION
    # -------------------------------------------------------------------------------------
    def _augment_dataset(self, dataset: Dict[str, Any]) -> Dict[str, Any]:
        logger.info("🔄 Augmenting dataset with synonyms, typos, and fuzzy variants...")
        for rec in dataset.get("datasets", []):
            new_variants: List[Dict[str, Any]] = []
            for inp in rec["nl_inputs"]:
                text = inp["text"]
               
                for key, values in self.synonyms.items():
                    if key in text:
                        for syn in values:
                            new_variants.append(self._make_variant(text.replace(key, syn), "synonym"))  # type: ignore[reportUnknownMemberType]
               
                for key, typos in self.typo_patterns.items():
                    if key in text:
                        typo = random.choice(typos)
                        new_variants.append(self._make_variant(text.replace(key, typo), "typo"))  # type: ignore[reportUnknownMemberType]

            rec["nl_inputs"].extend(new_variants)
        return dataset

    def _make_variant(self, text: str, style: str) -> Dict[str, Any]:
        return {
            "id": random.randint(10000, 99999),
            "text": text,
            "token_count": len(text.split()),
            "char_count": len(text),
            "style": style,
        }

    # -------------------------------------------------------------------------------------
    # FUZZY MATCH FOR RUNTIME QUERIES
    # -------------------------------------------------------------------------------------
    def fuzzy_match_query(self, query: str, stored_texts: List[str], threshold: int = 75) -> Optional[str]:
        """Return best fuzzy match for user query"""
        match, score, _ = process.extractOne(query, stored_texts, scorer=fuzz.token_sort_ratio)
        if score >= threshold:
            return match
        return None

    # -------------------------------------------------------------------------------------
    # VECTOR STORAGE (REDIS)
    # -------------------------------------------------------------------------------------
    def _float32_to_bytes(self, vec: np.ndarray[Any, Any]) -> bytes:  # type: ignore[reportMissingTypeArgument]
        vec_length: int = len(vec)  # type: ignore[reportUnknownArgumentType]
        return struct.pack("%sf" % vec_length, *vec.astype(np.float32))

    def upsert_to_redis(self, dataset: Dict[str, Any], redis_url: str = "redis://localhost:6379/0", prefix: str = "api:dataset") -> int:
        r = redis.from_url(redis_url)  # type: ignore[reportUnknownMemberType]
        count = 0
        pipe = r.pipeline()  # type: ignore[reportUnknownMemberType, reportAttributeAccessIssue]

        for rec in dataset.get("datasets", []):
            api = rec["api"]
            for item in rec["nl_inputs"]:
                vec = self.embedding_model.encode([item["text"]])[0]  # type: ignore[reportUnknownMemberType]
                key = f"{prefix}:{api}:{item['id']}"
                pipe.hset(  # type: ignore[reportUnknownMemberType]
                    key,
                    mapping={
                        "api": api,
                        "text": item["text"],
                        "style": item["style"],
                        "embedding_model": self.EMBEDDING_MODEL,
                    },
                )
                pipe.set(f"{key}:vec", self._float32_to_bytes(np.array(vec)))  # type: ignore[reportUnknownMemberType, reportUnknownArgumentType]
                count += 1

        pipe.execute()  # type: ignore[reportUnknownMemberType]
        logger.info(f"✅ Stored {count} augmented vectors in Redis")
        return count

    # -------------------------------------------------------------------------------------
    # EXPORT DATASET
    # -------------------------------------------------------------------------------------
    def export_dataset_files(self, dataset: Dict[str, Any], api_name: str, folder: str = "datasets") -> Dict[str, str]:
        os.makedirs(folder, exist_ok=True)
        rows: List[Dict[str, Any]] = []
        for rec in dataset.get("datasets", []):
            for item in rec["nl_inputs"]:
                row_item: Dict[str, Any] = {
                    "api": rec["api"],
                    "endpoint": rec["endpoint"],
                    "nl_input": item["text"],
                    "style": item["style"],
                }
                rows.append(row_item)  # type: ignore[reportUnknownMemberType]
        df = pd.DataFrame(rows)
        ts = int(time.time())
        csv_path = os.path.join(folder, f"{api_name}_dataset_{ts}.csv")
        jsonl_path = os.path.join(folder, f"{api_name}_dataset_{ts}.jsonl")
        df.to_csv(csv_path, index=False)
        df.to_json(jsonl_path, orient="records", lines=True)  # type: ignore[reportUnknownMemberType]
        return {"csv": csv_path, "jsonl": jsonl_path}



_llm_service: Optional[LLMService] = None

def get_llm_service(model_name: Optional[str] = None, api_token: Optional[str] = None) -> LLMService:
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService(model_name=model_name, api_token=api_token)
    return _llm_service
