# LLM Providers Package
"""
LLM Provider abstraction layer for dynamic model configuration.

This package provides a unified interface for multiple LLM providers:
- OpenAI (GPT-4, GPT-4 Turbo, GPT-3.5)
- Anthropic (Claude 3, Claude 2)
- Google (Gemini Pro, Gemini Flash)
- Ollama (Local models)
- HuggingFace (Inference API)
- Custom HTTP endpoints

Usage:
    from app.llm.provider_factory import LLMProviderFactory
    
    provider = await LLMProviderFactory.create_from_config(user_config)
    response = await provider.generate(prompt, system_prompt, config)
"""
