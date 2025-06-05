FROM python:3.11-slim

# Install system dependencies (Tesseract OCR + libs)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pour l’entrée : python main.py
CMD ["python", "/app/main.py"]