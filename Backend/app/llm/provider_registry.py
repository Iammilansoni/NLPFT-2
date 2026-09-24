"""
Provider registry
=================

Every AI provider NLPForge can talk to, described as data. Adding a provider
that speaks the OpenAI API (most of them) is one entry here: chat, model
listing and embeddings all work from its `base_url`, with no new code.

The frontend reads this list from GET /api/v1/llm-config/providers, so the
connection form, the embedding picker and the docs page cannot drift from what
the backend supports.

Models are NOT listed here -- they come live from each provider (see
model_discovery). A provider appears as an option whether or not the deployment
has a key for it: a user who brings their own key can use it.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

# Wire protocols. Each maps to one chat class, one lister and one embedder.
OPENAI = "openai"        # OpenAI-compatible REST: /models, /chat/completions, /embeddings
GEMINI = "gemini"
ANTHROPIC = "anthropic"
OLLAMA = "ollama"
HUGGINGFACE = "huggingface"
XAI = "xai"              # OpenAI-compatible, with its own chat class for xAI extras
CUSTOM = "custom"        # a user-run OpenAI-compatible server
BUILTIN = "builtin"      # ONNX models running inside the backend process


@dataclass(frozen=True)
class ProviderSpec:
    id: str
    label: str
    description: str
    api: str
    base_url: str = ""
    key_url: str = ""
    env_key: str = ""                 # deployment-wide key, if the admin sets one
    requires_key: bool = True         # to chat / embed
    list_requires_key: bool = True    # to list models (some listings are public)
    chat: bool = True
    embeddings: bool = False
    local: bool = False
    free_tier: bool = False
    custom_base_url: bool = False     # only self-hosted providers take a user URL
    # Extra JSON fields some providers require on /embeddings.
    embed_extra: Dict[str, Any] = field(default_factory=dict)
    embed_batch: int = 64

    def public_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data.pop("embed_extra")
        data.pop("env_key")
        return data


PROVIDERS: List[ProviderSpec] = [
    ProviderSpec(
        "ollama", "Ollama", "Models running on your own machine. Free, private, no key needed.",
        OLLAMA, key_url="https://ollama.com/library", requires_key=False, list_requires_key=False,
        embeddings=True, local=True, free_tier=True, custom_base_url=True,
    ),
    ProviderSpec(
        "builtin", "Built-in (ONNX)",
        "Small embedding models that run inside NLPForge itself. No server, no key. Downloaded on first use.",
        BUILTIN, requires_key=False, list_requires_key=False, chat=False, embeddings=True,
        local=True, free_tier=True,
    ),
    ProviderSpec(
        "google", "Google Gemini", "Google's Gemini chat and embedding models. Generous free tier.",
        GEMINI, "https://generativelanguage.googleapis.com/v1beta", "https://aistudio.google.com/apikey",
        env_key="GEMINI_API_KEY", embeddings=True, free_tier=True, embed_batch=100,
    ),
    ProviderSpec(
        "groq", "Groq", "Open-weight models on very fast inference hardware. Free tier.",
        OPENAI, "https://api.groq.com/openai/v1", "https://console.groq.com/keys",
        env_key="GROQ_API_KEY", free_tier=True,
    ),
    ProviderSpec(
        "openrouter", "OpenRouter", "One key for hundreds of models from every major lab, some free.",
        OPENAI, "https://openrouter.ai/api/v1", "https://openrouter.ai/keys",
        env_key="OPENROUTER_API_KEY", list_requires_key=False, embeddings=True, free_tier=True,
    ),
    ProviderSpec(
        "openai", "OpenAI", "OpenAI's GPT, reasoning and text-embedding models.",
        OPENAI, "https://api.openai.com/v1", "https://platform.openai.com/api-keys",
        env_key="OPENAI_API_KEY", embeddings=True, embed_batch=256,
    ),
    ProviderSpec(
        "anthropic", "Anthropic Claude", "Anthropic's Claude models.",
        ANTHROPIC, "https://api.anthropic.com/v1", "https://console.anthropic.com/settings/keys",
        env_key="ANTHROPIC_API_KEY",
    ),
    ProviderSpec(
        "mistral", "Mistral AI", "Mistral's chat models and mistral-embed.",
        OPENAI, "https://api.mistral.ai/v1", "https://console.mistral.ai/api-keys",
        env_key="MISTRAL_API_KEY", embeddings=True, free_tier=True,
    ),
    ProviderSpec(
        "deepseek", "DeepSeek", "DeepSeek's chat and reasoning models.",
        OPENAI, "https://api.deepseek.com/v1", "https://platform.deepseek.com/api_keys",
        env_key="DEEPSEEK_API_KEY",
    ),
    ProviderSpec(
        "grok", "xAI Grok", "xAI's Grok models.",
        XAI, "https://api.x.ai/v1", "https://console.x.ai", env_key="XAI_API_KEY",
    ),
    ProviderSpec(
        "together", "Together AI", "Open-weight chat and embedding models.",
        OPENAI, "https://api.together.xyz/v1", "https://api.together.ai/settings/api-keys",
        env_key="TOGETHER_API_KEY", embeddings=True,
    ),
    ProviderSpec(
        "fireworks", "Fireworks AI", "Fast hosting for open-weight chat and embedding models.",
        OPENAI, "https://api.fireworks.ai/inference/v1", "https://fireworks.ai/account/api-keys",
        env_key="FIREWORKS_API_KEY", embeddings=True,
    ),
    ProviderSpec(
        "deepinfra", "DeepInfra", "Low-cost hosting for open-weight chat and embedding models.",
        OPENAI, "https://api.deepinfra.com/v1/openai", "https://deepinfra.com/dash/api_keys",
        env_key="DEEPINFRA_API_KEY", list_requires_key=False, embeddings=True,
    ),
    ProviderSpec(
        "nvidia", "NVIDIA NIM", "NVIDIA-hosted chat and retrieval embedding models. Free credits.",
        OPENAI, "https://integrate.api.nvidia.com/v1", "https://build.nvidia.com",
        env_key="NVIDIA_API_KEY", list_requires_key=False, embeddings=True, free_tier=True,
        embed_extra={"input_type": "query", "truncate": "END"},
    ),
    ProviderSpec(
        "cerebras", "Cerebras", "Open-weight models on Cerebras wafer-scale hardware. Free tier.",
        OPENAI, "https://api.cerebras.ai/v1", "https://cloud.cerebras.ai",
        env_key="CEREBRAS_API_KEY", free_tier=True,
    ),
    ProviderSpec(
        "sambanova", "SambaNova", "Fast open-weight chat models. Free tier.",
        OPENAI, "https://api.sambanova.ai/v1", "https://cloud.sambanova.ai/apis",
        env_key="SAMBANOVA_API_KEY", list_requires_key=False, free_tier=True,
    ),
    ProviderSpec(
        "cohere", "Cohere", "Cohere's Command chat models and Embed models.",
        OPENAI, "https://api.cohere.ai/compatibility/v1", "https://dashboard.cohere.com/api-keys",
        env_key="COHERE_API_KEY", embeddings=True, free_tier=True,
        embed_extra={"encoding_format": "float"}, embed_batch=96,
    ),
    ProviderSpec(
        "jina", "Jina AI", "Jina's multilingual embedding models.",
        OPENAI, "https://api.jina.ai/v1", "https://jina.ai/api-dashboard",
        env_key="JINA_API_KEY", list_requires_key=False, chat=False, embeddings=True, free_tier=True,
    ),
    ProviderSpec(
        "nebius", "Nebius AI Studio", "Open-weight chat and embedding models.",
        OPENAI, "https://api.studio.nebius.com/v1", "https://studio.nebius.com/settings/api-keys",
        env_key="NEBIUS_API_KEY", embeddings=True,
    ),
    ProviderSpec(
        "novita", "Novita AI", "Low-cost hosting for open-weight models.",
        OPENAI, "https://api.novita.ai/v3/openai", "https://novita.ai/settings/key-management",
        env_key="NOVITA_API_KEY", list_requires_key=False, embeddings=True,
    ),
    ProviderSpec(
        "hyperbolic", "Hyperbolic", "Open-weight chat models.",
        OPENAI, "https://api.hyperbolic.xyz/v1", "https://app.hyperbolic.xyz/settings",
        env_key="HYPERBOLIC_API_KEY",
    ),
    ProviderSpec(
        "huggingface", "Hugging Face", "Models served by Hugging Face inference providers.",
        HUGGINGFACE, "https://router.huggingface.co", "https://huggingface.co/settings/tokens",
        env_key="HF_TOKEN", list_requires_key=False, embeddings=True,
    ),
    ProviderSpec(
        "custom", "Custom endpoint",
        "Any OpenAI-compatible server: LM Studio, vLLM, LocalAI, or a provider not listed here.",
        CUSTOM, requires_key=False, list_requires_key=False, embeddings=True, local=True,
        custom_base_url=True,
    ),
]

_BY_ID: Dict[str, ProviderSpec] = {p.id: p for p in PROVIDERS}


def get_provider(provider_id: str) -> Optional[ProviderSpec]:
    return _BY_ID.get(provider_id)


def require_provider(provider_id: str) -> ProviderSpec:
    spec = _BY_ID.get(provider_id)
    if spec is None:
        raise KeyError(f"Unknown provider '{provider_id}'")
    return spec


def provider_label(provider_id: str) -> str:
    spec = _BY_ID.get(provider_id)
    return spec.label if spec else provider_id


def embedding_providers() -> List[ProviderSpec]:
    return [p for p in PROVIDERS if p.embeddings]
