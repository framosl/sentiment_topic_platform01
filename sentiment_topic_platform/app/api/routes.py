from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from src.pipeline import ReviewPipeline

router = APIRouter()

# -----------------------------
# Pipeline (se carga una sola vez)
# -----------------------------
pipeline = ReviewPipeline(lang="es")


# -----------------------------
# MODELOS
# -----------------------------
class ReviewRequest(BaseModel):
    text: str


class ReviewResponse(BaseModel):
    original_text: str
    clean_text: str
    sentiment: str
    rating: int
    confidence: float


# -----------------------------
# ENDPOINT PRINCIPAL
# -----------------------------
@router.post("/analyze", response_model=ReviewResponse)
def analyze_review(request: ReviewRequest):
    try:
        result = pipeline.process_single(request.text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------
# HEALTH CHECK
# -----------------------------
@router.get("/health")
def health():
    return {
        "status": "ok",
        "message": "API funcionando correctamente"
    }