FROM dailyco/pipecat-base:latest

# Set working directory
WORKDIR /app

# Enable bytecode compilation for better performance
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Copy dependency files first for better Docker layer caching
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project --no-dev

# Copy application code and custom services
COPY bot_production.py ./
COPY bot_cartesia_openai.py ./
COPY cohere_llm_service.py ./
COPY bot_cartesia_cohere_direct.py ./

# Set environment variables for production
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV NODE_ENV=production

# Expose the port that the app runs on
EXPOSE 7860

# Use production bot as default
CMD ["uv", "run", "bot_production.py"]
