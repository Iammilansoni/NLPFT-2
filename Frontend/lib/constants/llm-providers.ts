/**
 * LLM Provider Constants
 * 
 * Defines available LLM providers and their models for the configuration UI.
 * This is the frontend counterpart to the backend provider factory.
 */

export type LLMProviderType =
    | 'openai'
    | 'google'
    | 'grok'
    | 'ollama'
    | 'deepseek'
    | 'anthropic'
    | 'huggingface'
    | 'custom';

export interface LLMModelOption {
    id: string;
    name: string;
    description: string;
    contextLength: number;
    supportsVision?: boolean;
    supportsFunctions?: boolean;
    tier?: 'flagship' | 'fast' | 'legacy' | 'reasoning' | 'open-source' | 'image';
    inputPrice?: number;  // Per million tokens
    outputPrice?: number; // Per million tokens
}

export interface LLMProviderInfo {
    id: LLMProviderType;
    name: string;
    description: string;
    color: string;
    icon: 'openai' | 'google' | 'grok' | 'claude' | 'ollama' | 'deepseek' | 'huggingface' | 'custom';
    requiresApiKey: boolean;
    supportsCustomBaseUrl: boolean;
    baseUrlPlaceholder?: string;
    apiKeyPlaceholder?: string;
    docsUrl?: string;
    models: LLMModelOption[];
    implemented: boolean;
}

// =============================================================================
// PROVIDER DEFINITIONS
// =============================================================================

export const LLM_PROVIDERS: Record<LLMProviderType, LLMProviderInfo> = {
    openai: {
        id: 'openai',
        name: 'OpenAI',
        description: 'GPT-5.x, o3/o4 Reasoning, GPT-4.1, GPT-4o, Open-Weight OSS',
        color: '#10a37f',
        icon: 'openai',
        requiresApiKey: true,
        supportsCustomBaseUrl: true,
        baseUrlPlaceholder: 'https://api.openai.com/v1',
        apiKeyPlaceholder: 'sk-...',
        docsUrl: 'https://platform.openai.com/docs/models',
        implemented: true,
        models: [
            // GPT-5.x Frontier
            { id: 'gpt-5.2', name: 'GPT-5.2', description: 'Best for coding and agentic tasks', contextLength: 128000, tier: 'flagship' },
            { id: 'gpt-5.2-pro', name: 'GPT-5.2 Pro', description: 'Smarter, more precise responses', contextLength: 128000, tier: 'flagship' },
            { id: 'gpt-5', name: 'GPT-5', description: 'Intelligent reasoning model', contextLength: 128000, tier: 'flagship' },
            { id: 'gpt-5-mini', name: 'GPT-5 Mini', description: 'Fast, cost-efficient', contextLength: 128000, tier: 'fast' },
            { id: 'gpt-5-nano', name: 'GPT-5 Nano', description: 'Fastest, most cost-efficient', contextLength: 128000, tier: 'fast' },
            // Reasoning
            { id: 'o3', name: 'o3', description: 'Complex reasoning tasks', contextLength: 200000, tier: 'reasoning' },
            { id: 'o3-pro', name: 'o3 Pro', description: 'More compute for better responses', contextLength: 200000, tier: 'reasoning' },
            { id: 'o4-mini', name: 'o4 Mini', description: 'Fast reasoning model', contextLength: 200000, tier: 'reasoning' },
            // GPT-4.1
            { id: 'gpt-4.1', name: 'GPT-4.1', description: 'Smartest non-reasoning model', contextLength: 128000, tier: 'flagship' },
            { id: 'gpt-4.1-mini', name: 'GPT-4.1 Mini', description: 'Smaller, faster version', contextLength: 128000, tier: 'fast' },
            // GPT-4o
            { id: 'gpt-4o', name: 'GPT-4o', description: 'Fast, intelligent, flexible', contextLength: 128000, supportsVision: true },
            { id: 'gpt-4o-mini', name: 'GPT-4o Mini', description: 'Affordable for focused tasks', contextLength: 128000, supportsVision: true, tier: 'fast' },
            // Open-Weight
            { id: 'gpt-oss-120b', name: 'GPT-OSS 120B', description: 'Most powerful open-weight', contextLength: 128000, tier: 'open-source' },
            { id: 'gpt-oss-20b', name: 'GPT-OSS 20B', description: 'Medium open-weight for low latency', contextLength: 128000, tier: 'open-source' },
            // Legacy
            { id: 'gpt-4-turbo', name: 'GPT-4 Turbo', description: 'Older high-intelligence model', contextLength: 128000, tier: 'legacy' },
            { id: 'gpt-3.5-turbo', name: 'GPT-3.5 Turbo', description: 'Legacy budget model', contextLength: 16385, tier: 'legacy' },
        ],
    },

    google: {
        id: 'google',
        name: 'Google Gemini',
        description: 'Gemini 3.0, 2.5 Pro/Flash, 2.0 Flash, 1.5 series',
        color: '#4285f4',
        icon: 'google',
        requiresApiKey: true,
        supportsCustomBaseUrl: false,
        apiKeyPlaceholder: 'AIza...',
        docsUrl: 'https://ai.google.dev/gemini-api/docs/models',
        implemented: true,
        models: [
            // Gemini 3 Series (Preview)
            { id: 'gemini-3-pro-preview', name: 'Gemini 3 Pro Preview', description: 'Latest flagship preview', contextLength: 1000000, tier: 'flagship' },
            { id: 'gemini-3-flash-preview', name: 'Gemini 3 Flash Preview', description: 'Fast next-gen model', contextLength: 1000000, tier: 'fast' },
            // Gemini 2.5
            { id: 'gemini-2.5-pro', name: 'Gemini 2.5 Pro', description: 'State-of-the-art reasoning', contextLength: 1000000, tier: 'flagship' },
            { id: 'gemini-2.5-flash', name: 'Gemini 2.5 Flash', description: 'Best price-performance', contextLength: 1000000, tier: 'fast' },
            { id: 'gemini-2.5-flash-lite', name: 'Gemini 2.5 Flash-Lite', description: 'Lightweight, ultra-fast', contextLength: 1000000, tier: 'fast' },
            // Gemini 2.0
            { id: 'gemini-2.0-flash', name: 'Gemini 2.0 Flash', description: 'Fast multimodal model', contextLength: 1000000, supportsVision: true },
            // Legacy
            { id: 'gemini-1.5-pro', name: 'Gemini 1.5 Pro', description: 'Advanced reasoning (legacy)', contextLength: 1000000, tier: 'legacy' },
            { id: 'gemini-1.5-flash', name: 'Gemini 1.5 Flash', description: 'High-volume tasks (legacy)', contextLength: 1000000, tier: 'legacy' },
        ],
    },

    grok: {
        id: 'grok',
        name: 'Grok (xAI)',
        description: 'xAI Grok models: Grok-4, Grok-3, Vision',
        color: '#000000',
        icon: 'grok',
        requiresApiKey: true,
        supportsCustomBaseUrl: false,
        apiKeyPlaceholder: 'xai-...',
        docsUrl: 'https://docs.x.ai/docs',
        implemented: true,
        models: [
            // Grok 4.1 Fast Series
            {
                id: 'grok-4-1-fast-reasoning',
                name: 'Grok 4.1 Fast Reasoning',
                description: 'Fast reasoning with 2M context',
                contextLength: 2000000,
                tier: 'reasoning',
                inputPrice: 0.20,
                outputPrice: 0.50,
            },
            {
                id: 'grok-4-1-fast-non-reasoning',
                name: 'Grok 4.1 Fast Non-Reasoning',
                description: 'Fast non-reasoning with 2M context',
                contextLength: 2000000,
                tier: 'fast',
                inputPrice: 0.20,
                outputPrice: 0.50,
            },
            // Grok Code
            {
                id: 'grok-code-fast-1',
                name: 'Grok Code Fast 1',
                description: 'Optimized for code generation',
                contextLength: 256000,
                tier: 'fast',
                inputPrice: 0.20,
                outputPrice: 1.50,
            },
            // Grok 4 Fast Series
            {
                id: 'grok-4-fast-reasoning',
                name: 'Grok 4 Fast Reasoning',
                description: 'Fast reasoning model',
                contextLength: 2000000,
                tier: 'reasoning',
                inputPrice: 0.20,
                outputPrice: 0.50,
            },
            {
                id: 'grok-4-fast-non-reasoning',
                name: 'Grok 4 Fast Non-Reasoning',
                description: 'Fast general model',
                contextLength: 2000000,
                tier: 'fast',
                inputPrice: 0.20,
                outputPrice: 0.50,
            },
            {
                id: 'grok-4-0709',
                name: 'Grok 4 (0709)',
                description: 'Flagship Grok 4 model',
                contextLength: 256000,
                tier: 'flagship',
                inputPrice: 3.00,
                outputPrice: 15.00,
            },
            // Grok 3 Series
            {
                id: 'grok-3-mini',
                name: 'Grok 3 Mini',
                description: 'Lightweight Grok 3',
                contextLength: 131072,
                tier: 'fast',
                inputPrice: 0.30,
                outputPrice: 0.50,
            },
            {
                id: 'grok-3',
                name: 'Grok 3',
                description: 'Standard Grok 3 model',
                contextLength: 131072,
                tier: 'flagship',
                inputPrice: 3.00,
                outputPrice: 15.00,
            },
            // Grok 2 Vision
            {
                id: 'grok-2-vision-1212',
                name: 'Grok 2 Vision',
                description: 'Multimodal vision model',
                contextLength: 32768,
                supportsVision: true,
                inputPrice: 2.00,
                outputPrice: 10.00,
            },
        ],
    },

    ollama: {
        id: 'ollama',
        name: 'Ollama',
        description: 'Local LLMs (Llama, Mistral, Qwen, DeepSeek, Gemma)',
        color: '#1a1a2e',
        icon: 'ollama',
        requiresApiKey: false,
        supportsCustomBaseUrl: true,
        baseUrlPlaceholder: 'http://localhost:11434',
        docsUrl: 'https://ollama.com/library',
        implemented: true,
        models: [
            // Llama 3.2 Series (Latest, recommended)
            { id: 'llama3.2:3b', name: 'Llama 3.2 3B', description: 'Compact, fast, great for simple tasks', contextLength: 128000, tier: 'fast' },
            { id: 'llama3.2:1b', name: 'Llama 3.2 1B', description: 'Ultra-lightweight, fastest inference', contextLength: 128000, tier: 'fast' },
            // Llama 3.3 (Latest flagship)
            { id: 'llama3.3:70b', name: 'Llama 3.3 70B', description: 'Latest flagship, best quality', contextLength: 128000, tier: 'flagship' },
            // Llama 3.1 Series
            { id: 'llama3.1:8b', name: 'Llama 3.1 8B', description: 'Balanced speed and quality', contextLength: 128000 },
            { id: 'llama3.1:70b', name: 'Llama 3.1 70B', description: 'High quality, more resources', contextLength: 128000, tier: 'flagship' },
            // Qwen 2.5 Series (Excellent for coding and reasoning)
            { id: 'qwen2.5:3b', name: 'Qwen 2.5 3B', description: 'Fast Alibaba model', contextLength: 128000, tier: 'fast' },
            { id: 'qwen2.5:7b', name: 'Qwen 2.5 7B', description: 'Balanced Alibaba model', contextLength: 128000 },
            { id: 'qwen2.5:14b', name: 'Qwen 2.5 14B', description: 'Strong reasoning and coding', contextLength: 128000 },
            { id: 'qwen2.5:32b', name: 'Qwen 2.5 32B', description: 'High-quality generation', contextLength: 128000, tier: 'flagship' },
            { id: 'qwen2.5:72b', name: 'Qwen 2.5 72B', description: 'Best Qwen quality', contextLength: 128000, tier: 'flagship' },
            // Qwen 2.5 Coder (Specialized for code)
            { id: 'qwen2.5-coder:7b', name: 'Qwen 2.5 Coder 7B', description: 'Coding specialist', contextLength: 128000 },
            { id: 'qwen2.5-coder:32b', name: 'Qwen 2.5 Coder 32B', description: 'Advanced coding', contextLength: 128000 },
            // Mistral Series
            { id: 'mistral:7b', name: 'Mistral 7B', description: 'Fast, efficient, versatile', contextLength: 32768 },
            { id: 'mistral-small:24b', name: 'Mistral Small 24B', description: 'Balanced Mistral', contextLength: 128000 },
            { id: 'mistral-large:123b', name: 'Mistral Large 123B', description: 'Most capable Mistral', contextLength: 128000, tier: 'flagship' },
            // DeepSeek R1 Series (Reasoning)
            { id: 'deepseek-r1:1.5b', name: 'DeepSeek R1 1.5B', description: 'Tiny reasoning model', contextLength: 64000, tier: 'fast' },
            { id: 'deepseek-r1:7b', name: 'DeepSeek R1 7B', description: 'Fast reasoning', contextLength: 64000, tier: 'reasoning' },
            { id: 'deepseek-r1:8b', name: 'DeepSeek R1 8B', description: 'Balanced reasoning', contextLength: 64000, tier: 'reasoning' },
            { id: 'deepseek-r1:14b', name: 'DeepSeek R1 14B', description: 'Strong reasoning', contextLength: 64000, tier: 'reasoning' },
            { id: 'deepseek-r1:32b', name: 'DeepSeek R1 32B', description: 'Advanced reasoning', contextLength: 64000, tier: 'reasoning' },
            { id: 'deepseek-r1:70b', name: 'DeepSeek R1 70B', description: 'Best reasoning quality', contextLength: 64000, tier: 'reasoning' },
            // Gemma 2 Series (Google)
            { id: 'gemma2:2b', name: 'Gemma 2 2B', description: 'Compact Google model', contextLength: 8192, tier: 'fast' },
            { id: 'gemma2:9b', name: 'Gemma 2 9B', description: 'Balanced Google model', contextLength: 8192 },
            { id: 'gemma2:27b', name: 'Gemma 2 27B', description: 'High-quality Google model', contextLength: 8192 },
            // Phi-4 (Microsoft)
            { id: 'phi4:14b', name: 'Phi-4 14B', description: 'Microsoft small language model', contextLength: 16384 },
            // Command R Series (Cohere)
            { id: 'command-r:35b', name: 'Command R 35B', description: 'Cohere RAG-optimized', contextLength: 128000 },
            { id: 'command-r-plus:104b', name: 'Command R+ 104B', description: 'Best Cohere model', contextLength: 128000, tier: 'flagship' },
            // Codestral (Mistral for code)
            { id: 'codestral:22b', name: 'Codestral 22B', description: 'Mistral code specialist', contextLength: 32768 },
            // Custom model entry
            { id: 'custom', name: 'Custom Model', description: 'Enter any Ollama model name', contextLength: 4096 },
        ],
    },

    deepseek: {
        id: 'deepseek',
        name: 'DeepSeek',
        description: 'DeepSeek Chat, Coder, and R1 Reasoning models',
        color: '#0066ff',
        icon: 'deepseek',
        requiresApiKey: true,
        supportsCustomBaseUrl: true,
        baseUrlPlaceholder: 'https://api.deepseek.com/v1',
        apiKeyPlaceholder: 'sk-...',
        docsUrl: 'https://platform.deepseek.com/api-docs',
        implemented: true,
        models: [
            { id: 'deepseek-chat', name: 'DeepSeek Chat', description: 'General chat model', contextLength: 64000 },
            { id: 'deepseek-coder', name: 'DeepSeek Coder', description: 'Code generation', contextLength: 64000 },
            { id: 'deepseek-reasoner', name: 'DeepSeek R1', description: 'Advanced reasoning', contextLength: 64000, tier: 'reasoning' },
        ],
    },

    anthropic: {
        id: 'anthropic',
        name: 'Anthropic Claude',
        description: 'Claude Sonnet 4.5, Claude 4, Claude 3.5',
        color: '#d97706',
        icon: 'claude',
        requiresApiKey: true,
        supportsCustomBaseUrl: false,
        apiKeyPlaceholder: 'sk-ant-...',
        docsUrl: 'https://platform.claude.com/docs/en/about-claude/models/overview',
        implemented: true,
        models: [
            // Claude 4.5 (Latest)
            { id: 'claude-sonnet-4-5-20250929', name: 'Claude Sonnet 4.5', description: 'Best for coding & agentic tasks, 1M context', contextLength: 200000, tier: 'flagship', supportsVision: true },
            { id: 'claude-opus-4-5', name: 'Claude Opus 4.5', description: 'Most powerful Claude, highest capability', contextLength: 200000, tier: 'flagship', supportsVision: true },
            // Claude 4
            { id: 'claude-4-opus', name: 'Claude 4 Opus', description: 'Most capable for complex reasoning', contextLength: 200000, tier: 'flagship', supportsVision: true },
            { id: 'claude-4-sonnet', name: 'Claude 4 Sonnet', description: 'Balanced intelligence and speed', contextLength: 200000, supportsVision: true },
            // Claude 3.5 (Previous Gen)
            { id: 'claude-3-5-sonnet-20241022', name: 'Claude 3.5 Sonnet', description: 'Previous gen, still excellent ($3/$15)', contextLength: 200000, supportsVision: true },
            { id: 'claude-3-5-haiku-20241022', name: 'Claude 3.5 Haiku', description: 'Fast and cost-effective ($0.25/$1.25)', contextLength: 200000, tier: 'fast', supportsVision: true },
            // Claude 3 Legacy
            { id: 'claude-3-opus-20240229', name: 'Claude 3 Opus', description: 'Legacy flagship ($15/$75)', contextLength: 200000, tier: 'legacy', supportsVision: true },
        ],
    },

    huggingface: {
        id: 'huggingface',
        name: 'HuggingFace',
        description: 'Inference API and custom model endpoints',
        color: '#ff9d00',
        icon: 'huggingface',
        requiresApiKey: true,
        supportsCustomBaseUrl: true,
        baseUrlPlaceholder: 'https://api-inference.huggingface.co',
        apiKeyPlaceholder: 'hf_...',
        docsUrl: 'https://huggingface.co/docs/api-inference',
        implemented: true,
        models: [
            // Meta Llama 3 Series
            { id: 'meta-llama/Llama-3.3-70B-Instruct', name: 'Llama 3.3 70B Instruct', description: 'Latest Meta flagship', contextLength: 128000, tier: 'flagship' },
            { id: 'meta-llama/Llama-3.2-3B-Instruct', name: 'Llama 3.2 3B Instruct', description: 'Fast, compact Llama', contextLength: 128000, tier: 'fast' },
            { id: 'meta-llama/Llama-3.2-1B-Instruct', name: 'Llama 3.2 1B Instruct', description: 'Ultra lightweight', contextLength: 128000, tier: 'fast' },
            { id: 'meta-llama/Meta-Llama-3.1-8B-Instruct', name: 'Llama 3.1 8B Instruct', description: 'Balanced Meta model', contextLength: 128000 },
            { id: 'meta-llama/Meta-Llama-3.1-70B-Instruct', name: 'Llama 3.1 70B Instruct', description: 'Large Llama model', contextLength: 128000, tier: 'flagship' },
            // Google Gemma Series
            { id: 'google/gemma-3-27b-it', name: 'Gemma 3 27B Instruct', description: 'Latest Google open model', contextLength: 128000 },
            { id: 'google/gemma-3-12b-it', name: 'Gemma 3 12B Instruct', description: 'Balanced Gemma 3', contextLength: 128000 },
            { id: 'google/gemma-3-4b-it', name: 'Gemma 3 4B Instruct', description: 'Fast Gemma 3', contextLength: 128000, tier: 'fast' },
            { id: 'google/gemma-2-27b-it', name: 'Gemma 2 27B Instruct', description: 'High quality Gemma 2', contextLength: 8192 },
            { id: 'google/gemma-2-9b-it', name: 'Gemma 2 9B Instruct', description: 'Balanced Gemma 2', contextLength: 8192 },
            // Qwen Series
            { id: 'Qwen/Qwen2.5-72B-Instruct', name: 'Qwen 2.5 72B Instruct', description: 'Best Qwen model', contextLength: 131072, tier: 'flagship' },
            { id: 'Qwen/Qwen2.5-32B-Instruct', name: 'Qwen 2.5 32B Instruct', description: 'Strong Qwen model', contextLength: 131072 },
            { id: 'Qwen/Qwen2.5-14B-Instruct', name: 'Qwen 2.5 14B Instruct', description: 'Balanced Qwen', contextLength: 131072 },
            { id: 'Qwen/Qwen2.5-7B-Instruct', name: 'Qwen 2.5 7B Instruct', description: 'Fast Qwen model', contextLength: 131072, tier: 'fast' },
            { id: 'Qwen/Qwen2.5-Coder-32B-Instruct', name: 'Qwen 2.5 Coder 32B', description: 'Coding specialist', contextLength: 131072 },
            // Mistral Series
            { id: 'mistralai/Mistral-Large-Instruct-2411', name: 'Mistral Large 123B', description: 'Most capable Mistral', contextLength: 128000, tier: 'flagship' },
            { id: 'mistralai/Mistral-Small-24B-Instruct-2501', name: 'Mistral Small 24B', description: 'Efficient Mistral', contextLength: 32768 },
            { id: 'mistralai/Mistral-7B-Instruct-v0.3', name: 'Mistral 7B Instruct', description: 'Fast and efficient', contextLength: 32768, tier: 'fast' },
            { id: 'mistralai/Mixtral-8x7B-Instruct-v0.1', name: 'Mixtral 8x7B MoE', description: 'Mixture of experts', contextLength: 32768 },
            { id: 'mistralai/Codestral-22B-v0.1', name: 'Codestral 22B', description: 'Code specialist', contextLength: 32768 },
            // Microsoft Phi Series
            { id: 'microsoft/Phi-4', name: 'Phi-4 14B', description: 'Latest Microsoft SLM', contextLength: 16384 },
            { id: 'microsoft/Phi-3.5-mini-instruct', name: 'Phi-3.5 Mini', description: 'Compact and capable', contextLength: 128000, tier: 'fast' },
            { id: 'microsoft/Phi-3-medium-4k-instruct', name: 'Phi-3 Medium 14B', description: 'Balanced Phi model', contextLength: 4096 },
            // DeepSeek Series
            { id: 'deepseek-ai/DeepSeek-V3', name: 'DeepSeek V3', description: 'Latest DeepSeek', contextLength: 128000, tier: 'flagship' },
            { id: 'deepseek-ai/DeepSeek-R1', name: 'DeepSeek R1', description: 'Reasoning model', contextLength: 64000, tier: 'reasoning' },
            { id: 'deepseek-ai/DeepSeek-Coder-V2-Instruct', name: 'DeepSeek Coder V2', description: 'Code specialist', contextLength: 128000 },
            // Custom model - enter any HuggingFace model path
            { id: 'custom', name: 'Custom Model Path', description: 'Enter any HuggingFace model (e.g., org/model-name)', contextLength: 4096 },
        ],
    },

    custom: {
        id: 'custom',
        name: 'Custom / Local',
        description: 'OpenAI-compatible API (vLLM, LocalAI, LM Studio)',
        color: '#6b7280',
        icon: 'custom',
        requiresApiKey: false,  // API key is optional for local servers
        supportsCustomBaseUrl: true,
        baseUrlPlaceholder: 'http://localhost:8000/v1',
        apiKeyPlaceholder: 'optional-api-key',
        docsUrl: 'https://platform.openai.com/docs/api-reference/chat',
        implemented: true,
        models: [
            // Users enter their own model name
            { id: 'custom-model', name: 'Enter Model Name', description: 'Specify the model served by your endpoint', contextLength: 4096 },
        ],
    },
};

// =============================================================================
// HELPER FUNCTIONS
// =============================================================================

export const getProviderById = (id: LLMProviderType): LLMProviderInfo => {
    return LLM_PROVIDERS[id];
};

export const getImplementedProviders = (): LLMProviderInfo[] => {
    return Object.values(LLM_PROVIDERS).filter(p => p.implemented);
};

export const getAllProviders = (): LLMProviderInfo[] => {
    return Object.values(LLM_PROVIDERS);
};

export const getProviderModels = (providerId: LLMProviderType): LLMModelOption[] => {
    return LLM_PROVIDERS[providerId]?.models || [];
};

export const getModelById = (providerId: LLMProviderType, modelId: string): LLMModelOption | undefined => {
    return LLM_PROVIDERS[providerId]?.models.find(m => m.id === modelId);
};

// Default provider and model
export const DEFAULT_LLM_PROVIDER: LLMProviderType = 'ollama';
export const DEFAULT_LLM_MODEL = 'llama3.1:8b-instruct-q4_K_M';
