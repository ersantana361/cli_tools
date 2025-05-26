import os
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI # Import ChatOpenAI for DeepSeek

def get_llm(provider: str = "anthropic"): # Added provider argument with a default
    """
    Initializes and returns the LLM instance based on the specified provider.
    
    Args:
        provider (str): The name of the LLM provider ("anthropic" or "deepseek").
                        Defaults to "anthropic".
    
    Returns:
        An initialized Langchain LLM instance.
    
    Raises:
        Exception: If the required API key environment variable is not set,
                   or if an unsupported provider is specified.
    """
    if provider == "anthropic":
        ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
        if not ANTHROPIC_API_KEY:
            raise Exception("Missing ANTHROPIC_API_KEY environment variable for Anthropic")
        llm = ChatAnthropic(
            api_key=ANTHROPIC_API_KEY,
            model="claude-3-opus-20240229" # You can choose other Anthropic models here
        )
    elif provider == "deepseek":
        DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
        if not DEEPSEEK_API_KEY:
            raise Exception("Missing DEEPSEEK_API_KEY environment variable for DeepSeek")
        llm = ChatOpenAI( # DeepSeek uses OpenAI-compatible API
            api_key=DEEPSEEK_API_KEY,
            model_name="deepseek-chat", # DeepSeek's model name
            base_url="https://api.deepseek.com" # DeepSeek's base URL
        )
    else:
        raise Exception(f"Unsupported LLM provider: {provider}. Choose 'anthropic' or 'deepseek'.")
    
    return llm
