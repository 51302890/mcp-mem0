from mem0 import Memory
import os

# Custom instructions for memory processing
# These aren't being used right now but Mem0 does support adding custom prompting
# for handling memory retrieval and processing.
CUSTOM_INSTRUCTIONS = """
Extract the Following Information:  

- Key Information: Identify and save the most important details.
- Context: Capture the surrounding context to understand the memory's relevance.
- Connections: Note any relationships to other topics or memories.
- Importance: Highlight why this information might be valuable in the future.
- Source: Record where this information came from when applicable.
"""

def get_mem0_client():
    # Get LLM provider and configuration
    llm_provider = os.getenv('LLM_PROVIDER')
    llm_api_key = os.getenv('LLM_API_KEY')
    llm_model = os.getenv('LLM_CHOICE')
    llm_base_url = os.getenv('LLM_BASE_URL')
    embedding_model = os.getenv('EMBEDDING_MODEL_CHOICE')
    
    # Initialize config dictionary
    config = {}
    
    # Configure LLM based on provider
    if llm_provider == 'deepseek':
        # 设置环境变量供OpenAI客户端使用
        if llm_api_key:
            os.environ["OPENAI_API_KEY"] = llm_api_key
        if llm_base_url:
            os.environ["OPENAI_BASE_URL"] = llm_base_url
            
        config["llm"] = {
            "provider": "openai",
            "config": {
                "model": llm_model or "deepseek-chat",
                "temperature": 0.2,
                "max_tokens": 2000
            }
        }
            
    elif llm_provider == 'openai' or llm_provider == 'openrouter':
        config["llm"] = {
            "provider": "openai",
            "config": {
                "model": llm_model,
                "temperature": 0.2,
                "max_tokens": 2000,
            }
        }
        
        # Set API key in environment if not already set
        if llm_api_key and not os.environ.get("OPENAI_API_KEY"):
            os.environ["OPENAI_API_KEY"] = llm_api_key
            
        # For OpenRouter, set the specific API key
        if llm_provider == 'openrouter' and llm_api_key:
            os.environ["OPENROUTER_API_KEY"] = llm_api_key
    
    elif llm_provider == 'ollama':
        config["llm"] = {
            "provider": "ollama",
            "config": {
                "model": llm_model,
                "temperature": 0.2,
                "max_tokens": 2000,
            }
        }
        
        # Set base URL for Ollama if provided
        llm_base_url = os.getenv('LLM_BASE_URL')
        if llm_base_url:
            config["llm"]["config"]["ollama_base_url"] = llm_base_url
    
    # Configure embedder based on provider
    embedding_api_key = os.getenv('EMBEDDING_API_KEY')
    
    if llm_provider == 'openai':
        config["embedder"] = {
            "provider": "openai",
            "config": {
                "model": embedding_model or "text-embedding-3-small",
                "embedding_dims": 1024  # Default for text-embedding-3-small
            }
        }
        
        # Set API key in environment if not already set
        if embedding_api_key:
            os.environ["OPENAI_API_KEY"] = embedding_api_key
        elif llm_api_key and not os.environ.get("OPENAI_API_KEY"):
            os.environ["OPENAI_API_KEY"] = llm_api_key
    
    # 单独配置向量模型服务
    embedding_base_url = os.getenv('EMBEDDING_BASE_URL')
    if embedding_base_url:
        config["embedder"] = {
            "provider": "ollama",
            "config": {
                "model": os.getenv('EMBEDDING_MODEL_CHOICE') or "nomic-embed-text",
                "embedding_dims": int(os.getenv('EMBEDDING_DIMS') or 1024),
                "ollama_base_url": embedding_base_url
            }
        }
    
    # Configure Supabase vector store
    config["vector_store"] = {
        "provider": "supabase",
        "config": {
            "connection_string": os.environ.get('DATABASE_URL', ''),
            "collection_name": "mem0_memories",
            "embedding_model_dims": 1024  # 统一使用1024维度
        }
    }

    # config["custom_fact_extraction_prompt"] = CUSTOM_INSTRUCTIONS
    
    # Create and return the Memory client
    return Memory.from_config(config)
