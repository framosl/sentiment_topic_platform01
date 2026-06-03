FROM python:3.10

WORKDIR /app
COPY . .

RUN pip install -r requirements.txt
RUN python -m spacy download es_core_news_sm

CMD uvicorn api:app --host 0.0.0.0 --port ${PORT:-8000}
