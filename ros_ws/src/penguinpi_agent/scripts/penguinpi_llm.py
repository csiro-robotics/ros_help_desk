#!/usr/bin/env python
import os
import dotenv
from langchain_openai import ChatOpenAI

# def get_llm(streaming: bool = False):
#     """Get the LLM instance for PenguinPi agent"""
#     dotenv.load_dotenv()
#     
#     # Try to get API key from environment variable
#     api_key = os.getenv('OPENAI_API_KEY')
#     
#     if not api_key:
#         # Fallback to a default key (you should set this in your .env file)
#         api_key = 'API_KEY'
#     
#     openai_llm = ChatOpenAI(
#         model_name="gpt-4o",  # or your preferred model
#         temperature=0,
#         max_tokens=None,
#         timeout=None,
#         max_retries=2,
#         openai_api_key=api_key,
#     )
#     
#     return openai_llm

def get_llm(streaming: bool = False):
    import dotenv
    from langchain_ollama import ChatOllama
    from langchain_core.messages import BaseMessage
    from langchain_core.tools import tool # Import tool decorator or Tool class
    """Get the LLM instance for PenguinPi agent using Ollama"""
    dotenv.load_dotenv()

  
    ollama_model = 'qwen2.5:7b' 
    ollama_base_url = 'http://localhost:11434' 

    ollama_llm = ChatOllama(
        model=ollama_model,
        base_url=ollama_base_url,
        temperature=0,
        keep_alive="5m",
        streaming=streaming,
        num_ctx=8192,   # Increase context length for better tool understanding
    )
    return ollama_llm

def get_env_variable(var_name: str) -> str:
    """
    Retrieves the value of the specified environment variable.
    
    Args:
        var_name (str): The name of the environment variable to retrieve.
        
    Returns:
        str: The value of the environment variable.
        
    Raises:
        ValueError: If the environment variable is not set.
    """
    value = os.getenv(var_name)
    if value is None:
        raise ValueError(f"Environment variable {var_name} is not set.")
    return value 