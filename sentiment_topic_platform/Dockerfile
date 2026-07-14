FROM python:3.10-slim

WORKDIR /app

# 1. Instalar dependencias del sistema operativo
RUN apt-get update && apt-get install -y \
    build-essential \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# 2. Instalar las librerías de Python (Aquí se instalará python-pptx)
RUN pip install --no-cache-dir -r requirements.txt

# 3. !! NUEVO: Descargar el modelo de lenguaje en español para spaCy !!
RUN python -m spacy download es_core_news_sm

COPY . .

# 4. Encender el Backend y Frontend juntos
CMD uvicorn app.main:app --host 127.0.0.1 --port 8000 & streamlit run dashboard.py --server.port $PORT --server.address 0.0.0.0