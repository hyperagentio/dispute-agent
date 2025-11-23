FROM python:3.10-slim

WORKDIR /build

# Install git and build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Clone and install hiero-sdk-python (required dependency)
RUN git clone https://github.com/hiero-ledger/hiero-sdk-python.git && \
    cd hiero-sdk-python && \
    pip install --upgrade pip && \
    pip install -e . && \
    python generate_proto.py

# Clone and install hedera-agent-kit-py
RUN git clone https://github.com/hashgraph/hedera-agent-kit-py.git && \
    cd hedera-agent-kit-py/python && \
    pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev

# Now set up our application
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install our app dependencies (with ollama group by default)
RUN uv sync --frozen --no-dev --group ollama

# Copy application code
COPY . .

# Expose port
EXPOSE 4021

# Run the application using uv run (which uses the venv)
CMD ["uv", "run", "python", "main.py"]
