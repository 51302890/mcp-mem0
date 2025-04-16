FROM python:3.12-slim

ARG PORT=8050

WORKDIR /app

# 设置阿里云镜像源（更稳定）
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/

# 创建虚拟环境并设置超时
RUN python -m venv .venv
ENV PATH="/app/.venv/bin:$PATH"

# 关键：增加下载超时
ENV UV_HTTP_TIMEOUT=600

# 先复制依赖声明文件
COPY pyproject.toml .

# 安装依赖（包含 ollama 和超时设置）
RUN pip install --no-cache-dir uv ollama && \
    pip install --timeout=1000 -e .

COPY . .

EXPOSE ${PORT}

CMD ["uv", "run", "src/main.py"]
