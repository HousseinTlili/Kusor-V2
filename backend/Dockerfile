FROM python:3.11-slim

WORKDIR /app

# Dépendances système nécessaires (OCR, compilation de certains packages Python)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-fra \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Installe torch en version CPU-only AVANT le reste, pour éviter que pip
# ne tire automatiquement les paquets CUDA/GPU (des centaines de Mo inutiles
# ici, puisque le conteneur tourne sans GPU).
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

RUN pip install --no-cache-dir -r requirements.txt

# Modèle spaCy français (si utilisé pour le NER — adapte si besoin)
RUN python -m spacy download fr_core_news_md || true

COPY . .

EXPOSE 5000

CMD ["python", "app.py"]