
import json
import csv
import base64
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

import torch
import numpy as np
from sentence_transformers import SentenceTransformer
import redis
from transformers import AutoTokenizer, pipeline
import nltk  # type: ignore
from nltk.tokenize import word_tokenize, sent_tokenize  # type: ignore

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')


class APIDatasetGenerator:
    
    def __init__(
        self,
        embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        llm_model_name: str = "microsoft/Phi-3-mini-4k-instruct",
        redis_host: str = "localhost",
        redis_port: int = 6379,
        output_dir: str = "./datasets",
        use_model_manager: bool = True
    ):
        self.embedding_model_name = embedding_model_name
        self.llm_model_name = llm_model_name
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)
        self.use_model_manager = use_model_manager
        
        print(f"🔧 Initializing APIDatasetGenerator...")
        print(f"   Embedding Model: {embedding_model_name}")
        print(f"   LLM Model: {llm_model_name}")
        print(f"   Using Model Manager: {use_model_manager}")
        
        if use_model_manager:
            print(f"📥 Using shared model manager (singleton)...")
            try:
                from app.core.model_manager import model_manager
                self.model_manager = model_manager
                self.embedding_model = self.model_manager.get_embedding_model(embedding_model_name)
            except ImportError:
                print(f"⚠️  Model manager not available, falling back to direct loading")
                self.use_model_manager = False
                print(f"📥 Loading embedding model...")
                self.embedding_model = SentenceTransformer(embedding_model_name)
        else:
            print(f"📥 Loading embedding model...")
            self.embedding_model = SentenceTransformer(embedding_model_name)
        
        try:
            self.redis_client = redis.Redis(
                host=redis_host,
                port=redis_port,
                decode_responses=False
            )
            self.redis_client.ping()  # type: ignore
            print(f"✅ Redis connected at {redis_host}:{redis_port}")
        except Exception as e:
            print(f"⚠️  Redis connection failed: {e}")
            print(f"   Continuing without Redis storage...")
            self.redis_client = None
        
        self.llm_pipeline = None
        self.tokenizer = None
    
    def clear_redis_embeddings(self) -> int:
        """Clear all existing API embeddings from Redis"""
        if not self.redis_client:
            return 0
        
        try:
            
            keys = self.redis_client.keys("api:embedding:*")  # type: ignore
            count = len(keys)  # type: ignore
            
            if count > 0:
                
                self.redis_client.delete(*keys)  # type: ignore
                # Clear the index
                self.redis_client.delete("api:embeddings:index")  # type: ignore
                print(f"🧹 Cleared {count} existing embeddings from Redis")
            else:
                print(f"ℹ️  No existing embeddings found in Redis")
            
            return count
        except Exception as e:
            print(f"⚠️  Error clearing Redis: {e}")
            return 0
        
    def initialize_llm(self, use_quantization: bool = True):
        """Initialize LLM pipeline using model manager if available"""
        if self.use_model_manager and hasattr(self, 'model_manager'):
            
            if self.model_manager.is_llm_loaded(self.llm_model_name):
                print(f"✅ Using pre-loaded LLM model from cache")
                self.llm_pipeline = self.model_manager.get_llm_pipeline(self.llm_model_name)
                self.tokenizer = self.model_manager.get_llm_tokenizer(self.llm_model_name)
                return
            
            print(f"📥 Loading LLM model via model manager...")
            print(f"   This may take a few minutes on first run...")
            
            try:
                self.llm_pipeline = self.model_manager.get_llm_pipeline(self.llm_model_name, use_quantization)
                self.tokenizer = self.model_manager.get_llm_tokenizer(self.llm_model_name)
                
                if self.llm_pipeline:
                    print(f"✅ LLM model loaded successfully (shared instance)")
                else:
                    print(f"⚠️  LLM initialization failed via model manager")
                    print(f"   Falling back to rule-based paraphrase generation")
                    
            except Exception as e:
                print(f"⚠️  LLM initialization failed: {e}")
                print(f"   Falling back to rule-based paraphrase generation")
                self.llm_pipeline = None
        else:
            # Fallback to direct loading
            print(f"📥 Loading LLM model for paraphrase generation...")
            print(f"   This may take a few minutes on first run...")
            
            try:
                self.tokenizer = AutoTokenizer.from_pretrained(  # type: ignore
                    self.llm_model_name,
                    trust_remote_code=True,
                    use_fast=True  # Use fast tokenizer for better performance
                )
                
                # Fix for DynamicCache error: disable caching
                self.llm_pipeline = pipeline(  # type: ignore
                    "text-generation",
                    model=self.llm_model_name,
                    tokenizer=self.tokenizer,  # type: ignore
                    device=-1,
                    trust_remote_code=True,
                    dtype=torch.float32,
                    model_kwargs={
                        "use_cache": False,  # Fix DynamicCache error
                        "low_cpu_mem_usage": True 
                    }
                )
                
                print(f"✅ LLM model loaded successfully")
                
            except Exception as e:
                print(f"⚠️  LLM initialization failed: {e}")
                print(f"   Falling back to rule-based paraphrase generation")
                self.llm_pipeline = None
    
    def chunk_text(self, text: str, max_tokens: int = 300) -> List[str]:
        sentences = sent_tokenize(text)  # type: ignore
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:  # type: ignore
            tokens = word_tokenize(sentence)  # type: ignore
            token_count = len(tokens)
            
            if current_length + token_count <= max_tokens:
                current_chunk.append(sentence)
                current_length += token_count
            else:
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                current_chunk = [sentence]
                current_length = token_count
        
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        return chunks
    
    def generate_embedding(self, text: str) -> np.ndarray:  # type: ignore
        """Generate embedding for a single text"""
        embedding = self.embedding_model.encode(
            text, 
            convert_to_numpy=True,
            show_progress_bar=False,  # Disable progress bar for single texts
            normalize_embeddings=True  # Normalize for better similarity search
        )  # type: ignore
        return embedding  # type: ignore
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[np.ndarray]:  # type: ignore
        """Generate embeddings for multiple texts (faster than one-by-one)"""
        embeddings = self.embedding_model.encode(
            texts,
            convert_to_numpy=True,
            show_progress_bar=False,
            normalize_embeddings=True,
            batch_size=32  # Process in batches for efficiency
        )  # type: ignore
        return embeddings  # type: ignore
    
    def store_in_redis(
        self,
        record_id: str,
        api_name: str,
        endpoint: str,
        text_chunk: str,
        embedding_vector: np.ndarray  # type: ignore
    ) -> bool:
        if not self.redis_client:
            return False
        
        try:
            key = f"api:embedding:{record_id}"
            
            self.redis_client.hset(key, mapping={  # type: ignore
                "id": record_id,
                "api_name": api_name,
                "endpoint": endpoint,
                "text_chunk": text_chunk,
                "embedding": embedding_vector.tobytes(),
                "embedding_dim": len(embedding_vector),
                "timestamp": datetime.now().isoformat()
            })
            
            self.redis_client.zadd(  # type: ignore
                "api:embeddings:index",
                {record_id: datetime.now().timestamp()}
            )
            
            return True
            
        except Exception as e:
            print(f"⚠️  Redis storage error: {e}")
            return False
    
    def generate_rule_based_paraphrases(self, base_text: str, count: int = 20) -> List[str]:
        paraphrases = []
        
        login_synonyms = [
            "login", "sign in", "sign-in", "signin", "log in", "log on",
            "authenticate", "authorize", "access account", "enter", "connect",
            "open session", "start session", "grant access"
        ]
        
        credential_synonyms = [
            "credentials", "creds", "login info", "login details",
            "account info", "account details", "authentication data",
            "login credentials", "user credentials"
        ]
        
        username_vars = ["username", "usarname", "user", "user name", "usrname", "usr", "username X", "user X", "X"]
        
        password_vars = ["password", "pass", "passwd", "pasword", "password Y", "pass Y", "Y"]
        
        templates = [
            "{login} using {username} and {password}",
            "{login} with {credentials} {username} and {password}",
            "{username} {password} {login}",
            "use {username} and {password} to {login}",
            "{login} to the system with {username} and {password}",
            "please {login} with my {credentials}",
            "{login} with {username} as username and {password} as password",
            "authenticate via {password} and {username}",
            "enter {username} and {password} to continue",
            "{login} {username}/{password}",
            "{login} u: {username} p: {password}",
            "with {username}, {login}",
            "kindly {login} using {username} and {password}",
            "access my account using {username} and {password}",
            "use my {credentials} to {login}",
            "let me in using {username} and {password}",
            "{login} now with {username} and {password}",
            "grant access after verifying {username} and {password}",
            "input {username} and {password} to authenticate",
            "start a session using {username} and {password}"
        ]
        
        import random
        random.seed(42)
        
        for _ in range(count):
            template = random.choice(templates)
            
            paraphrase = template.format(
                login=random.choice(login_synonyms),
                username=random.choice(username_vars),
                password=random.choice(password_vars),
                credentials=random.choice(credential_synonyms)
            )
            
            if random.random() < 0.15:
                paraphrase = self._add_typos(paraphrase)
            
            paraphrases.append(paraphrase.strip())
        
        paraphrases = list(set(paraphrases))
        
        return paraphrases[:count]
    
    def _add_typos(self, text: str) -> str:
        typo_map = {
            "login": "logn",
            "sign in": "signin",
            "authenticate": "autenticate",
            "credentials": "credentails",
            "username": "usrname",
            "password": "pasword",
            "account": "acount"
        }
        
        for correct, typo in typo_map.items():
            if correct in text.lower():
                text = text.replace(correct, typo)
                break
        
        return text
    
    def generate_llm_paraphrases(self, base_text: str, count: int = 20) -> List[str]:
        if not self.llm_pipeline:
            return self.generate_rule_based_paraphrases(base_text, count)
        
        prompt = f"""Generate {count} natural language paraphrases for the following API action:
"{base_text}"

Requirements:
- Use synonyms like: sign in, authenticate, log on, authorize, access account
- Include casual variations and typos
- Keep each under 20 tokens
- Maintain semantic meaning about authentication
- Include variations with 'username X and password Y'

Paraphrases:
1."""
        
        try:
            outputs = self.llm_pipeline(
                prompt,
                max_new_tokens=500,
                num_return_sequences=1,
                temperature=0.8,
                do_sample=True,
                use_cache=False  # Fix DynamicCache error
            )
            
            generated_text = outputs[0]["generated_text"]
            
            lines = generated_text.split("\n")
            paraphrases = []
            
            for line in lines:
                line = line.strip()
                match = re.match(r'^\d+\.\s*(.+)$', line)
                if match:
                    paraphrases.append(match.group(1).strip())
            
            if len(paraphrases) < count:
                additional = self.generate_rule_based_paraphrases(
                    base_text,
                    count - len(paraphrases)
                )
                paraphrases.extend(additional)
            
            return paraphrases[:count]
            
        except Exception as e:
            print(f"⚠️  LLM generation failed: {e}")
            return self.generate_rule_based_paraphrases(base_text, count)
    
    def generate_custom_apis_with_llm(self, context: str, api_count: int) -> List[Dict[str, str]]:
        """
        Generate custom API templates based on user context using LLM.
        
        Args:
            context: User-provided context (e.g., "e-commerce", "hotel booking")
            api_count: Number of APIs to generate
            
        Returns:
            List of API template dictionaries
        """
        if not self.llm_pipeline:
            self.initialize_llm()
        
        prompt = f"""Generate {api_count} REST API endpoints for a {context} system.
For each API, provide:
1. API name (short, lowercase, hyphen-separated)
2. Endpoint URL path
3. Brief definition (one sentence)
4. Natural language description

Format each API as:
API: <name>
ENDPOINT: /api/<path>
DEFINITION: <one sentence description>
NL: <natural language query>
---

Example:
API: search-products
ENDPOINT: /api/products/search
DEFINITION: Searches for products by name, category, or keywords in the catalog.
NL: search for products by name or category
---

Now generate {api_count} APIs for: {context}
"""

        try:
            print(f"🤖 Using LLM to generate custom APIs for: {context}")
            print(f"⏳ Generating text (this may take 1-2 minutes on CPU)...")
            print(f"💡 Tip: For faster generation, consider using a GPU or reducing the API count")
            
            import time
            start_time = time.time()
            
            outputs = self.llm_pipeline(  # type: ignore
                prompt,
                max_new_tokens=300,  # Further reduced for faster generation
                num_return_sequences=1,
                temperature=0.7,
                do_sample=True,
                use_cache=False,
                pad_token_id=self.tokenizer.eos_token_id,  # type: ignore
                top_p=0.9,
                repetition_penalty=1.2,
                early_stopping=True  # Stop when done
            )
            
            elapsed = time.time() - start_time
            print(f"✅ Text generation completed in {elapsed:.1f}s")
            
            generated_text = outputs[0]["generated_text"]
            
            
            api_blocks = generated_text.split("---")
            apis = []
            
            for block in api_blocks:
                if not block.strip():
                    continue
                    
                api_dict = {}
                lines = block.strip().split("\n")
                
                for line in lines:
                    line = line.strip()
                    if line.startswith("API:"):
                        api_dict["api"] = line.replace("API:", "").strip()
                    elif line.startswith("ENDPOINT:"):
                        api_dict["endpoint"] = "https://example.com" + line.replace("ENDPOINT:", "").strip()
                    elif line.startswith("DEFINITION:"):
                        api_dict["definition"] = line.replace("DEFINITION:", "").strip()
                    elif line.startswith("NL:"):
                        api_dict["base_nl"] = line.replace("NL:", "").strip()
                
                # Only add if we have all required fields
                if all(k in api_dict for k in ["api", "endpoint", "definition", "base_nl"]):
                    # Add a generic request object
                    api_dict["request"] = {"data": "request_payload"}
                    apis.append(api_dict)
                    
                if len(apis) >= api_count:
                    break
            
            print(f"✅ Generated {len(apis)} custom APIs")
            return apis
            
        except Exception as e:
            print(f"⚠️  Custom API generation failed: {e}")
            return []
    
    def _get_default_api_templates(self) -> List[Dict[str, Any]]:
        """Returns the default API templates for general-purpose use."""
        return [
            {
                "api": "login",
                "endpoint": "https://example.com/api/login",
                "request": {"username": "demo_user", "password": "demo_pass"},
                "definition": "Authenticates a user using provided username and password, returning an access token or session.",
                "base_nl": "login using username and password"
            },
            {
                "api": "register",
                "endpoint": "https://example.com/api/register",
                "request": {"username": "new_user", "password": "new_pass", "email": "user@example.com"},
                "definition": "Creates a new user account with username, password, and email address.",
                "base_nl": "register a new account with username and password"
            },
            {
                "api": "logout",
                "endpoint": "https://example.com/api/logout",
                "request": {"token": "session_token"},
                "definition": "Terminates the current user session and invalidates the authentication token.",
                "base_nl": "logout from the current session"
            },
            {
                "api": "forgot-password",
                "endpoint": "https://example.com/api/forgot-password",
                "request": {"email": "user@example.com"},
                "definition": "Initiates password reset process by sending a reset link to the user's email.",
                "base_nl": "reset forgotten password using email"
            },
            {
                "api": "change-password",
                "endpoint": "https://example.com/api/change-password",
                "request": {"old_password": "old_pass", "new_password": "new_pass"},
                "definition": "Updates user's password after verifying the old password.",
                "base_nl": "change current password to new password"
            },
            {
                "api": "verify-email",
                "endpoint": "https://example.com/api/verify-email",
                "request": {"token": "verification_token"},
                "definition": "Verifies user's email address using a verification token sent via email.",
                "base_nl": "verify email address with token"
            },
            {
                "api": "refresh-token",
                "endpoint": "https://example.com/api/refresh-token",
                "request": {"refresh_token": "refresh_token_value"},
                "definition": "Generates a new access token using a valid refresh token.",
                "base_nl": "refresh authentication token"
            },
            {
                "api": "get-profile",
                "endpoint": "https://example.com/api/profile",
                "request": {"token": "access_token"},
                "definition": "Retrieves the authenticated user's profile information.",
                "base_nl": "get user profile information"
            },
            {
                "api": "update-profile",
                "endpoint": "https://example.com/api/profile",
                "request": {"token": "access_token", "name": "User Name", "bio": "User bio"},
                "definition": "Updates the authenticated user's profile information.",
                "base_nl": "update user profile information"
            },
            {
                "api": "delete-account",
                "endpoint": "https://example.com/api/account",
                "request": {"token": "access_token", "password": "confirm_password"},
                "definition": "Permanently deletes the user account after password confirmation.",
                "base_nl": "delete user account permanently"
            }
        ]
    
    def generate_dataset(
        self,
        api_count: int = 10,
        nl_variations_per_api: int = 20,
        use_llm: bool = False,
        api_context: str = ""
    ) -> tuple[List[Dict[str, Any]], int]:
        print(f"\n🚀 Generating API Dataset...")
        print(f"   APIs: {api_count}")
        print(f"   NL Variations per API: {nl_variations_per_api}")
        print(f"   Using LLM: {use_llm}")
        if api_context:
            print(f"   Context: {api_context}")
        print()
        
        
        if api_context and api_context.strip():
            print(f"🎯 Generating custom APIs based on context: '{api_context}'")
            custom_apis = self.generate_custom_apis_with_llm(api_context, api_count)
            
            if custom_apis and len(custom_apis) > 0:
                api_templates = custom_apis
                print(f"✅ Using {len(api_templates)} custom-generated APIs")
            else:
                print(f"⚠️  Custom API generation failed, falling back to default templates")
                api_templates = self._get_default_api_templates()
        else:
            api_templates = self._get_default_api_templates()
        
        dataset = []
        redis_stored_count = 0
        
        if use_llm and not self.llm_pipeline:
            self.initialize_llm()
        
        for i, api_template in enumerate(api_templates[:api_count]):
            print(f"📝 Generating API {i+1}/{api_count}: {api_template['api']}")
            
            if use_llm:
                nl_inputs = self.generate_llm_paraphrases(
                    api_template['base_nl'],
                    nl_variations_per_api
                )
            else:
                nl_inputs = self.generate_rule_based_paraphrases(
                    api_template['base_nl'],
                    nl_variations_per_api
                )
            
            definition_embedding = self.generate_embedding(api_template['definition'])
            
            record_id = f"{api_template['api']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            if self.store_in_redis(
                record_id=record_id,
                api_name=api_template['api'],
                endpoint=api_template['endpoint'],
                text_chunk=api_template['definition'],
                embedding_vector=definition_embedding
            ):
                redis_stored_count += 1
            
            record = {
                "api": api_template['api'],
                "endpoint": api_template['endpoint'],
                "request": api_template['request'],
                "response": {
                    "definition": api_template['definition']
                },
                "nl_inputs": nl_inputs,
                "paraphrase_type": f"{api_template['api']}_synonyms_and_typos",
                "embedding_model": self.embedding_model_name,
                "embedding_vector": definition_embedding.tolist(),
                "embedding_base64": base64.b64encode(definition_embedding.tobytes()).decode('utf-8')
            }
            
            dataset.append(record)
            print(f"   ✅ Generated {len(nl_inputs)} NL variations")
        
        print(f"\n✅ Dataset generation complete! Total records: {len(dataset)}")
        
        if redis_stored_count > 0:
            print(f"🎉 Successfully stored {redis_stored_count} embeddings in Redis vector database!")
        elif self.redis_client:
            print(f"⚠️  Redis is configured but no embeddings were stored. Check Redis connection.")
        else:
            print(f"ℹ️  Redis storage skipped (Redis not configured)")
        
        return dataset, redis_stored_count
    
    def export_to_json(self, dataset: List[Dict[str, Any]], filename: Optional[str] = None) -> str:
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"api_dataset_{timestamp}.json"
        
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, indent=2, ensure_ascii=False)
        
        print(f"📄 JSON exported: {filepath}")
        return str(filepath)
    
    def export_to_jsonl(self, dataset: List[Dict[str, Any]], filename: Optional[str] = None) -> str:
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"api_dataset_{timestamp}.jsonl"
        
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            for record in dataset:
                for nl_input in record['nl_inputs']:
                    row = {
                        "api": record['api'],
                        "endpoint": record['endpoint'],
                        "nl_input": nl_input,
                        "definition_of_api": record['response']['definition'],
                        "paraphrase_type": record['paraphrase_type'],
                        "embedding_model": record['embedding_model']
                    }
                    f.write(json.dumps(row, ensure_ascii=False) + '\n')
        
        print(f"📄 JSONL exported: {filepath}")
        return str(filepath)
    
    def export_to_csv(self, dataset: List[Dict[str, Any]], filename: Optional[str] = None) -> str:
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"api_dataset_{timestamp}.csv"
        
        filepath = self.output_dir / filename
        
        rows = []
        for record in dataset:
            for nl_input in record['nl_inputs']:
                rows.append({
                    "api": record['api'],
                    "endpoint": record['endpoint'],
                    "nl_input": nl_input,
                    "definition_of_api": record['response']['definition'],
                    "paraphrase_type": record['paraphrase_type'],
                    "embedding_model": record['embedding_model']
                })
        
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ["api", "endpoint", "nl_input", "definition_of_api", "paraphrase_type", "embedding_model"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            writer.writeheader()
            writer.writerows(rows)
        
        print(f"📄 CSV exported: {filepath}")
        return str(filepath)
    
    def generate_summary(self, dataset: List[Dict[str, Any]], filename: Optional[str] = None) -> str:
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"dataset_summary_{timestamp}.txt"
        
        filepath = self.output_dir / filename
        
        total_apis = len(dataset)
        total_nl_variations = sum(len(record['nl_inputs']) for record in dataset)
        avg_variations = total_nl_variations / total_apis if total_apis > 0 else 0
        
        api_names = [record['api'] for record in dataset]
        
        summary = f"""
API Dataset Generation Summary
===============================
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

Configuration
-------------
Embedding Model: {self.embedding_model_name}
LLM Model: {self.llm_model_name}
Output Directory: {self.output_dir}

Dataset Statistics
------------------
Total API Entries: {total_apis}
Total NL Variations: {total_nl_variations}
Average Variations per API: {avg_variations:.1f}

API List
--------
{chr(10).join(f"{i+1}. {api}" for i, api in enumerate(api_names))}

Embedding Details
-----------------
Model: {self.embedding_model_name}
Dimension: {len(dataset[0]['embedding_vector']) if dataset else 'N/A'}

Export Files
------------
- JSON: Full dataset with embeddings
- JSONL: One NL variation per line
- CSV: Tabular format for analysis

Redis Storage
-------------
Status: {"Connected" if self.redis_client else "Not connected"}
Records Stored: {total_apis if self.redis_client else 0}

Notes
-----
- Each API entry contains multiple natural language variations
- Embeddings generated using sentence-transformers
- Paraphrases include synonyms, typos, and contextual variations
- Dataset optimized for embedding-based search and retrieval
"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(summary)
        
        print(f"📄 Summary generated: {filepath}")
        return summary
