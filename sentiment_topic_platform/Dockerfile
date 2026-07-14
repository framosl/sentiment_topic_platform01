FROM python:3.10-slim

WORKDIR /app

# 1. Instalar dependencias del sistema operativo para que BERTopic y Transformers no fallen
RUN apt-get update && apt-get install -y \
    build-essential \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# 2. Instalar las librerías de Python
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 3. Encender el Backend en segundo plano (8000) y el Frontend en primer plano con el puerto dinámico de Railway
CMD uvicorn app.main:app --host 127.0.0.1 --port 8000 & streamlit run dashboard.py --server.port $PORT --server.address 0.0.0.0
