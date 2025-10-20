FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for PaddleOCR (optional)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

# Optional: Install PaddlePaddle GPU version (uncomment if GPU available)
# For CUDA 12.6:
# RUN pip install --no-cache-dir paddlepaddle-gpu==3.2.0 -i https://www.paddlepaddle.org.cn/packages/stable/cu126/
# For CPU only (lighter):
# RUN pip install --no-cache-dir paddlepaddle==3.2.0 -i https://pypi.tuna.tsinghua.edu.cn/simple

COPY . .

ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
