from mcp.server.fastmcp import FastMCP, Context
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dataclasses import dataclass
from dotenv import load_dotenv
from mem0 import Memory
import asyncio
import json
import os

from utils import get_mem0_client
import re

def clean_mem0_response(response):
    """Clean and extract text from complex mem0 response structure."""
    if not response:
        return ""
    
    # If already a simple string, return as-is
    if isinstance(response, str) and not response.startswith(('[', '{')):
        return response
    
    try:
        # Handle string responses that may contain JSON
        if isinstance(response, str):
            # Remove Tool execution result prefix if present
            if response.startswith('Tool execution result:'):
                response = response.replace('Tool execution result: ', '')
            
            # Unescape any escaped JSON strings
            response = re.sub(r'\\"', '"', response)
            response = re.sub(r'\\n', '\n', response)
            response = re.sub(r'\\u([0-9a-fA-F]{4})', 
                            lambda m: chr(int(m.group(1), 16)), response)
            
            # Parse the JSON
            parsed = json.loads(response)
        else:
            parsed = response
        
        # Extract text from different response formats
        if isinstance(parsed, list):
            texts = []
            for item in parsed:
                if isinstance(item, dict):
                    text = item.get('text', '')
                    if text:
                        # Recursively clean nested text
                        texts.append(clean_mem0_response(text))
                elif isinstance(item, str):
                    texts.append(item)
            return '\n'.join(texts)
        
        elif isinstance(parsed, dict):
            text = parsed.get('text', '')
            if text:
                return clean_mem0_response(text)
            return str(parsed)
        
        return str(parsed)
    
    except (json.JSONDecodeError, TypeError):
        return str(response)

load_dotenv()

# Default user ID for memory operations
DEFAULT_USER_ID = "user"

# Create a dataclass for our application context
@dataclass
class Mem0Context:
    """Context for the Mem0 MCP server."""
    mem0_client: Memory

@asynccontextmanager
async def mem0_lifespan(server: FastMCP) -> AsyncIterator[Mem0Context]:
    """
    Manages the Mem0 client lifecycle.
    
    Args:
        server: The FastMCP server instance
        
    Yields:
        Mem0Context: The context containing the Mem0 client
    """
    # Create and return the Memory client with the helper function in utils.py
    mem0_client = get_mem0_client()
    
    try:
        yield Mem0Context(mem0_client=mem0_client)
    finally:
        # No explicit cleanup needed for the Mem0 client
        pass

# Initialize FastMCP server with the Mem0 client as context
mcp = FastMCP(
    "mcp-mem0",
    description="MCP server for long term memory storage and retrieval with Mem0",
    lifespan=mem0_lifespan,
    host=os.getenv("HOST", "0.0.0.0"),
    port=os.getenv("PORT", "8050")
)        

@mcp.tool()
async def save_memory(ctx: Context, text: str) -> str:
    """Save information to your long-term memory.

    This tool is designed to store any type of information that might be useful in the future.
    The content will be processed and indexed for later retrieval through semantic search.

    Args:
        ctx: The MCP server provided context which includes the Mem0 client
        text: The content to store in memory, including any relevant details and context
    """
    try:
        mem0_client = ctx.request_context.lifespan_context.mem0_client
        messages = [{"role": "user", "content": text}]
        print(f"Attempting to save memory: {text[:100]}...")  # Debug log
        try:
            result = mem0_client.add(messages, user_id=DEFAULT_USER_ID)
            print(f"Save memory result type: {type(result)}")  # Debug log
            print(f"Save memory result content: {result}")  # Debug log
            if result is None:
                return "Failed to save memory: No result returned"
            
            # Clean and extract text from the response
            cleaned = clean_mem0_response(result)
            if cleaned:
                return cleaned
            
            return f"Successfully saved memory: {text[:100]}..." if len(text) > 100 else f"Successfully saved memory: {text}"
        except Exception as e:
            print(f"Error saving memory: {str(e)}")  # Debug log
            return f"Error saving memory: {str(e)}"
    except Exception as e:
        return f"Error saving memory: {str(e)}"

@mcp.tool()
async def get_all_memories(ctx: Context) -> str:
    """Get all stored memories for the user.
    
    Call this tool when you need complete context of all previously memories.

    Args:
        ctx: The MCP server provided context which includes the Mem0 client

    Returns a JSON formatted list of all stored memories, including when they were created
    and their content. Results are paginated with a default of 50 items per page.
    """
    try:
        mem0_client = ctx.request_context.lifespan_context.mem0_client
        memories = mem0_client.get_all(user_id=DEFAULT_USER_ID)
        if isinstance(memories, dict) and "results" in memories:
            flattened_memories = [memory["memory"] for memory in memories["results"]]
        else:
            flattened_memories = memories
        return json.dumps(flattened_memories, indent=2)
    except Exception as e:
        return f"Error retrieving memories: {str(e)}"

@mcp.tool()
async def search_memories(ctx: Context, query: str, limit: int = 3, min_score: float = 0.5) -> str:
    """Search memories using semantic search with enhanced accuracy.

    This tool performs semantic search with query preprocessing and result filtering.
    Only returns memories with similarity score above the threshold (default: 0.5).

    Args:
        ctx: The MCP server provided context which includes the Mem0 client
        query: Search query string describing what you're looking for. Can be natural language.
        limit: Maximum number of results to return (default: 3)
        min_score: Minimum similarity score (0-1) for results to be included (default: 0.5)
    """
    try:
        mem0_client = ctx.request_context.lifespan_context.mem0_client
        
        # Preprocess query - remove stopwords and normalize
        processed_query = ' '.join([word for word in query.split() 
                                  if word.lower() not in ['的', '是', '在', '和', '有']])
        
        print(f"Searching memories with query: {processed_query}")  # Debug log
        
        # Search with enhanced parameters
        memories = mem0_client.search(
            processed_query, 
            user_id=DEFAULT_USER_ID, 
            limit=limit*2  # Get more results to filter
        )
        
        cleaned = clean_mem0_response(memories)
        if cleaned:
            return cleaned
        
        results = []
        if isinstance(memories, dict):
            if "results" in memories:
                for memory in memories.get("results", []):
                    if memory.get("score", 0) >= min_score:
                        results.append({
                            "text": memory.get("memory"),
                            "score": memory.get("score"),
                            "timestamp": memory.get("timestamp")
                        })
            elif "facts" in memories:
                results = memories.get("facts", [])
            else:
                results = [memories]
        else:
            results = memories if isinstance(memories, list) else [memories]
        
        # Sort by score descending
        if all(isinstance(r, dict) and 'score' in r for r in results):
            results.sort(key=lambda x: x['score'], reverse=True)
        
        # Apply limit after filtering
        results = results[:limit]
        
        # Format output with scores
        output = []
        for result in results:
            if isinstance(result, dict):
                score = result.get('score', 'N/A')
                text = result.get('text', result.get('memory', str(result)))
                output.append(f"[相似度: {score:.2f}] {text}")
            else:
                output.append(str(result))
                
        return "\n\n".join(output) if output else "未找到相关记忆"
    except Exception as e:
        return f"Error searching memories: {str(e)}"

async def main():
    transport = os.getenv("TRANSPORT", "sse")
    if transport == 'sse':
        # Run the MCP server with sse transport
        await mcp.run_sse_async()
    else:
        # Run the MCP server with stdio transport
        await mcp.run_stdio_async()

if __name__ == "__main__":
    asyncio.run(main())
