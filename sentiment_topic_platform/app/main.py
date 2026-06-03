from fastapi import FastAPI
from app.api.routes import router

app = FastAPI(
    title="Sentiment & Topics API",
    description="API para análisis de sentimiento y NLP",
    version="1.0.0"
)

# registrar rutas
app.include_router(router)


@app.get("/")
def root():
    return {
        "message": "API funcionando correctamente 🚀",
        "docs": "/docs"
    }