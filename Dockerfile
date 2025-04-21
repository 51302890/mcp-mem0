# 第一阶段：构建依赖
FROM python:3.12-slim AS builder

WORKDIR /app

# 设置阿里云镜像源并配置并行下载
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/ && \
    pip config set global.timeout 100 && \
    pip config set global.retries 10

# 创建缓存目录
RUN mkdir /pip-cache

# 只复制依赖文件
COPY pyproject.toml .

# 下载依赖到缓存
RUN pip install --no-cache-dir uv && \
    pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install -e . && \
    pip freeze > requirements.txt && \
    pip download --dest /pip-cache -r requirements.txt && \
    pip install --no-index --find-links=/pip-cache -e .

# 第二阶段：运行时镜像
FROM python:3.12-slim

ARG PORT=8050
WORKDIR /app

# 从builder复制已安装的包
COPY --from=builder /app /app
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages

# 设置环境变量
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app" \
    UV_HTTP_TIMEOUT=600


COPY . .

EXPOSE ${PORT}

CMD ["python", "src/main.py"]
