/**
 * LLM provider metadata for the connection form: name, icon, key format, docs.
 *
 * Deliberately NO model lists. Models come from the live model catalogue
 * (GET /api/v1/model-catalog, POST /api/v1/model-catalog/discover), which asks
 * each provider what it serves right now. A list written here goes stale the
 * week after it is written.
 */

export type LLMProviderType =
    | 'openai'
    | 'google'
    | 'groq'
    | 'openrouter'
    | 'grok'
    | 'ollama'
    | 'deepseek'
    | 'anthropic'
    | 'huggingface'
    | 'custom';

export interface LLMProviderInfo {
    id: LLMProviderType;
    name: string;
    description: string;
    icon: 'openai' | 'google' | 'groq' | 'openrouter' | 'grok' | 'claude' | 'ollama' | 'deepseek' | 'huggingface' | 'custom';
    requiresApiKey: boolean;
    /** Only self-hosted providers take a URL; hosted ones always use their public API. */
    supportsCustomBaseUrl: boolean;
    baseUrlPlaceholder?: string;
    apiKeyPlaceholder?: string;
    /** Where to get an API key. */
    keyUrl?: string;
    /** Has a free tier or free models, worth pointing new users at. */
    freeTier?: boolean;
    /** Runs on the user's own hardware. */
    local?: boolean;
}

export const LLM_PROVIDERS: Record<LLMProviderType, LLMProviderInfo> = {
    ollama: {
        id: 'ollama',
        name: 'Ollama',
        description: 'Models running on your own machine. Free, private, no key needed.',
        icon: 'ollama',
        requiresApiKey: false,
        supportsCustomBaseUrl: true,
        baseUrlPlaceholder: 'Leave empty to use the bundled Ollama',
        keyUrl: 'https://ollama.com/library',
        local: true,
        freeTier: true,
    },
    google: {
        id: 'google',
        name: 'Google Gemini',
        description: "Google's Gemini models. Generous free tier.",
        icon: 'google',
        requiresApiKey: true,
        supportsCustomBaseUrl: false,
        apiKeyPlaceholder: 'AIza...',
        keyUrl: 'https://aistudio.google.com/apikey',
        freeTier: true,
    },
    groq: {
        id: 'groq',
        name: 'Groq',
        description: 'Open-weight models on very fast inference hardware. Free tier.',
        icon: 'groq',
        requiresApiKey: true,
        supportsCustomBaseUrl: false,
        apiKeyPlaceholder: 'gsk_...',
        keyUrl: 'https://console.groq.com/keys',
        freeTier: true,
    },
    openrouter: {
        id: 'openrouter',
        name: 'OpenRouter',
        description: 'One key for hundreds of models from every major lab, some free.',
        icon: 'openrouter',
        requiresApiKey: true,
        supportsCustomBaseUrl: false,
        apiKeyPlaceholder: 'sk-or-...',
        keyUrl: 'https://openrouter.ai/keys',
        freeTier: true,
    },
    openai: {
        id: 'openai',
        name: 'OpenAI',
        description: "OpenAI's GPT and reasoning models.",
        icon: 'openai',
        requiresApiKey: true,
        supportsCustomBaseUrl: false,
        apiKeyPlaceholder: 'sk-...',
        keyUrl: 'https://platform.openai.com/api-keys',
    },
    anthropic: {
        id: 'anthropic',
        name: 'Anthropic Claude',
        description: "Anthropic's Claude models.",
        icon: 'claude',
        requiresApiKey: true,
        supportsCustomBaseUrl: false,
        apiKeyPlaceholder: 'sk-ant-...',
        keyUrl: 'https://console.anthropic.com/settings/keys',
    },
    deepseek: {
        id: 'deepseek',
        name: 'DeepSeek',
        description: "DeepSeek's chat and reasoning models.",
        icon: 'deepseek',
        requiresApiKey: true,
        supportsCustomBaseUrl: false,
        apiKeyPlaceholder: 'sk-...',
        keyUrl: 'https://platform.deepseek.com/api_keys',
    },
    grok: {
        id: 'grok',
        name: 'xAI Grok',
        description: "xAI's Grok models.",
        icon: 'grok',
        requiresApiKey: true,
        supportsCustomBaseUrl: false,
        apiKeyPlaceholder: 'xai-...',
        keyUrl: 'https://console.x.ai',
    },
    huggingface: {
        id: 'huggingface',
        name: 'Hugging Face',
        description: 'Models served by Hugging Face inference providers.',
        icon: 'huggingface',
        requiresApiKey: true,
        supportsCustomBaseUrl: false,
        apiKeyPlaceholder: 'hf_...',
        keyUrl: 'https://huggingface.co/settings/tokens',
    },
    custom: {
        id: 'custom',
        name: 'Custom endpoint',
        description: 'Any OpenAI-compatible server you run: LM Studio, vLLM, LocalAI.',
        icon: 'custom',
        requiresApiKey: false,
        supportsCustomBaseUrl: true,
        baseUrlPlaceholder: 'http://localhost:1234/v1',
        apiKeyPlaceholder: 'Optional',
        local: true,
    },
};

export const getProviderById = (id: string): LLMProviderInfo =>
    LLM_PROVIDERS[id as LLMProviderType] ?? LLM_PROVIDERS.custom;

export const getAllProviders = (): LLMProviderInfo[] => Object.values(LLM_PROVIDERS);
