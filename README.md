<h1 align="center">MCP-Mem0：AI 代理的长期记忆</h1>

<p align="center">
  <img src="public/Mem0AndMCP.png" alt="Mem0 and MCP Integration" width="600">
</p>

这是一个模板实现，展示了如何将 模型上下文协议（MCP） 服务器与 Mem0 集成，以为 AI 代理提供持久记忆功能。

您可以将此项目作为构建 MCP 服务器的参考，或者将其作为示例提供给 AI 编码助手，并告诉它遵循此示例的结构和代码正确性！

概览

此项目展示了如何构建一个 MCP 服务器，使 AI 代理能够使用语义搜索存储、检索和搜索记忆。它作为一个实用的模板，用于创建您自己的 MCP 服务器，简单地使用 Mem0 和一个实用示例。
该实现遵循 Anthropic 提出的构建 MCP 服务器的最佳实践，允许与任何 MCP 兼容的客户端无缝集成。

功能

服务器提供三个基本的记忆管理工具：
save_memory：使用语义索引将任何信息存储在长期记忆中
get_all_memories：检索所有存储的记忆以获得全面的上下文
search_memories：使用语义搜索查找相关记忆

先决条件

Python 3.12+
Supabase 或任何 PostgreSQL 数据库（用于记忆的向量存储）
您选择的 LLM 提供商的 API 密钥（OpenAI、OpenRouter 或 Ollama）
如果将 MCP 服务器作为容器运行，建议使用 Docker

安装

### Using uv

1. Install uv if you don't have it:
   ```bash
   pip install uv
   ```

2. Clone this repository:
   ```bash
   git clone https://github.com/coleam00/mcp-mem0.git
   cd mcp-mem0
   ```

3. Install dependencies:
   ```bash
   uv pip install -e .
   ```

4. Create a `.env` file based on `.env.example`:
   ```bash
   cp .env.example .env
   ```

5. Configure your environment variables in the `.env` file (see Configuration section)

### Using Docker (Recommended)

1. Build the Docker image:
   ```bash
   docker build -t mcp/mem0 --build-arg PORT=8050 .
   ```

2. Create a `.env` file based on `.env.example` and configure your environment variables

## Configuration

The following environment variables can be configured in your `.env` file:

| Variable | Description | Example |
|----------|-------------|----------|
| `TRANSPORT` | Transport protocol (sse or stdio) | `sse` |
| `HOST` | Host to bind to when using SSE transport | `0.0.0.0` |
| `PORT` | Port to listen on when using SSE transport | `8050` |
| `LLM_PROVIDER` | LLM provider (openai, openrouter, or ollama) | `openai` |
| `LLM_BASE_URL` | Base URL for the LLM API | `https://api.openai.com/v1` |
| `LLM_API_KEY` | API key for the LLM provider | `sk-...` |
| `LLM_CHOICE` | LLM model to use | `gpt-4o-mini` |
| `EMBEDDING_MODEL_CHOICE` | Embedding model to use | `text-embedding-3-small` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:port/db` |

## Running the Server

### Using uv

#### SSE Transport

```bash
# Set TRANSPORT=sse in .env then:
uv run src/main.py
```

The MCP server will essentially be run as an API endpoint that you can then connect to with config shown below.

#### Stdio Transport

With stdio, the MCP client iself can spin up the MCP server, so nothing to run at this point.

### Using Docker

#### SSE Transport

```bash
docker run --env-file .env -p:8050:8050 mcp/mem0
```

The MCP server will essentially be run as an API endpoint within the container that you can then connect to with config shown below.

#### Stdio Transport

With stdio, the MCP client iself can spin up the MCP server container, so nothing to run at this point.

## Integration with MCP Clients

### SSE Configuration

Once you have the server running with SSE transport, you can connect to it using this configuration:

```json
{
  "mcpServers": {
    "mem0": {
      "transport": "sse",
      "url": "http://localhost:8050/sse"
    }
  }
}
```

> **Note for Windsurf users**: Use `serverUrl` instead of `url` in your configuration:
> ```json
> {
>   "mcpServers": {
>     "mem0": {
>       "transport": "sse",
>       "serverUrl": "http://localhost:8050/sse"
>     }
>   }
> }
> ```

> **Note for n8n users**: Use host.docker.internal instead of localhost since n8n has to reach outside of it's own container to the host machine:
> 
> So the full URL in the MCP node would be: http://host.docker.internal:8050/sse

Make sure to update the port if you are using a value other than the default 8050.

### Python with Stdio Configuration

Add this server to your MCP configuration for Claude Desktop, Windsurf, or any other MCP client:

```json
{
  "mcpServers": {
    "mem0": {
      "command": "your/path/to/mcp-mem0/.venv/Scripts/python.exe",
      "args": ["your/path/to/mcp-mem0/src/main.py"],
      "env": {
        "TRANSPORT": "stdio",
        "LLM_PROVIDER": "openai",
        "LLM_BASE_URL": "https://api.openai.com/v1",
        "LLM_API_KEY": "YOUR-API-KEY",
        "LLM_CHOICE": "gpt-4o-mini",
        "EMBEDDING_MODEL_CHOICE": "text-embedding-3-small",
        "DATABASE_URL": "YOUR-DATABASE-URL"
      }
    }
  }
}
```

### Docker with Stdio Configuration

```json
{
  "mcpServers": {
    "mem0": {
      "command": "docker",
      "args": ["run", "--rm", "-i", 
               "-e", "TRANSPORT", 
               "-e", "LLM_PROVIDER", 
               "-e", "LLM_BASE_URL", 
               "-e", "LLM_API_KEY", 
               "-e", "LLM_CHOICE", 
               "-e", "EMBEDDING_MODEL_CHOICE", 
               "-e", "DATABASE_URL", 
               "mcp/mem0"],
      "env": {
        "TRANSPORT": "stdio",
        "LLM_PROVIDER": "openai",
        "LLM_BASE_URL": "https://api.openai.com/v1",
        "LLM_API_KEY": "YOUR-API-KEY",
        "LLM_CHOICE": "gpt-4o-mini",
        "EMBEDDING_MODEL_CHOICE": "text-embedding-3-small",
        "DATABASE_URL": "YOUR-DATABASE-URL"
      }
    }
  }
}
```

## Building Your Own Server

This template provides a foundation for building more complex MCP servers. To build your own:

1. Add your own tools by creating methods with the `@mcp.tool()` decorator
2. Create your own lifespan function to add your own dependencies (clients, database connections, etc.)
3. Modify the `utils.py` file for any helper functions you need for your MCP server
4. Feel free to add prompts and resources as well  with `@mcp.resource()` and `@mcp.prompt()`
