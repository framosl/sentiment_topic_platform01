from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from src.pipeline import ReviewPipeline
import re

router = APIRouter()
pipeline = ReviewPipeline(lang="es")

def deducir_categoria(texto):
    texto = str(texto).lower()
    reglas = {
        'Electrónica y Tecnología': ['batería', 'cable', 'pantalla', 'móvil', 'auriculares', 'pc', 'bluetooth', 'fuerza'],
        'Ropa y Accesorios': ['talla', 'descosido', 'tela', 'zapatos', 'pantalón', 'camisa', 'tirantes', 'cremallera'],
        'Hogar y Cocina': ['sartén', 'cuchillo', 'mueble', 'mesa', 'madera', 'manchas', 'plástico'],
        'Salud, Belleza y Cuidado': ['champú', 'crema', 'piel', 'gel', 'pelo', 'aceite', 'sabor', 'olor'],
        'Deportes y Aire Libre': ['bicicleta', 'balón', 'pesas', 'gimnasio', 'entrenamiento', 'zapatillas'],
        'Libros y Entretenimiento': ['página', 'autor', 'leer', 'lectura', 'historia', 'novela', 'papel']
    }
    for cat, palabras in reglas.items():
        if any(p in texto for p in palabras): return cat
    return 'Otras Categorías / General'

class ReviewRequest(BaseModel):
    text: str

class ReviewResponse(BaseModel):
    original_text: str
    clean_text: str
    sentiment: str
    rating: int
    confidence: float
    predicted_category: str
    reason: str  # <--- IMPORTANTE: Agregamos este campo

@router.post("/analyze", response_model=ReviewResponse)
def analyze_review(request: ReviewRequest):
    # 1. FILTRO DE SEGURIDAD
    texto_solo_letras = re.sub(r'[^a-zA-ZáéíóúÁÉÍÓÚñÑ\s]', '', request.text).strip()
    if len(texto_solo_letras) < 3:
        return {
            "original_text": request.text, "clean_text": "", "sentiment": "neutral",
            "rating": 0, "confidence": 0.0, "predicted_category": "Entrada Inválida", "reason": "Entrada demasiado corta"
        }
    
    try:
        # 2. Lógica del Pipeline
        result = pipeline.process_single(request.text)
        
        # 3. Lógica de corrección y EXPLICABILIDAD (XAI)
        palabras_negativas_clave = ['aburrida', 'pesada', 'decepcionado', 'malo', 'pésimo', 'timo', 'infierno', 'desconectan']
        palabras_encontradas = [p for p in palabras_negativas_clave if p in request.text.lower()]
        
        if palabras_encontradas:
            result["sentiment"] = "negativo"
            result["confidence"] = 0.99
            result["rating"] = 1
            result["reason"] = f"Se detectaron marcadores de insatisfacción: {', '.join(palabras_encontradas)}"
        else:
            result["reason"] = "Análisis basado en modelo de lenguaje natural (Transformer)"
        
        # 4. Inyectar categoría
        result["predicted_category"] = deducir_categoria(request.text)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))