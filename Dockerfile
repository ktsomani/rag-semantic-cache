FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN pip install uv

# 1. Install CPU-only PyTorch FIRST (prevents the 4GB CUDA download)
RUN uv pip install --system torch --index-url https://download.pytorch.org/whl/cpu

# 2. Install the rest of your dependencies
RUN uv pip install --system fastapi uvicorn groq redis redisvl sentence-transformers numpy pydantic

# 3. Copy your code
COPY . .

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]