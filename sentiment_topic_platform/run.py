from datasets import load_dataset
import pandas as pd
from src.pipeline import ReviewPipeline
from deep_translator import GoogleTranslator
import numpy as np

# -----------------------------
# 🌐 Traductor
# -----------------------------
translator = GoogleTranslator(source='auto', target='es')

def translate_text(text):
    try:
        return translator.translate(text)
    except:
        return text

# -----------------------------
# 🚀 MAIN
# -----------------------------
def main():

    print("=== INICIANDO PIPELINE DE ANÁLISIS ===")
    # -----------------------------
    # -----------------------------
    # 1. Cargar dataset
    # -----------------------------
    print("\n1. Cargando dataset de reseñas en español...")
    # Volvemos a tu dataset seguro y estable
    dataset = load_dataset("SetFit/amazon_reviews_multi_es")
    df = dataset['train'].to_pandas()
    print(f"   ✅ Reseñas cargadas: {len(df)}")

    # -----------------------------
    # 2. Preparar datos y generar metadatos
    # -----------------------------
    # 2. Preparando datos y estructurando categorías
    df = df[['text', 'label_text']]
    df = df.dropna()
    df = df.sample(1000, random_state=42)
    df.rename(columns={'text': 'review', 'label_text': 'sentiment'}, inplace=True)

    def deducir_categoria(texto):
        texto = str(texto).lower()
        reglas = {
            'Electrónica y Tecnología': ['batería', 'cable', 'pantalla', 'móvil', 'auriculares', 'pc', 'bluetooth', 'fuerza'],
            'Ropa y Accesorios': ['talla', 'descosido', 'tela', 'zapatos', 'pantalón', 'camisa', 'tirantes', 'cremallera'],
            'Hogar y Cocina': ['sartén', 'cuchillo', 'mueble', 'mesa', 'madera', 'manchas', 'plástico'],
            'Salud, Belleza y Cuidado': ['champú', 'crema', 'piel', 'gel', 'pelo', 'aceite', 'olor'],
            'Deportes y Aire Libre': ['bicicleta', 'balón', 'pesas', 'gimnasio', 'entrenamiento', 'zapatillas'],
            'Libros y Entretenimiento': ['página', 'autor', 'leer', 'historia', 'novela', 'papel']
        }
        for cat, palabras in reglas.items():
            if any(p in texto for p in palabras): return cat
        return 'Otras Categorías / General'

    df['product_category'] = df['review'].apply(deducir_categoria)
    df['product_id'] = ['PROD-' + str(np.random.randint(100, 999)) for _ in range(len(df))]

    # ---> EL CAMBIO CLAVE ESTÁ AQUÍ <---
    # --- NUEVA LÓGICA DE MUESTREO SEGURO ---
    # Aumentamos la muestra a 1000 para que BERTopic tenga suficiente 
    # # volumen de texto y pueda formar clústeres reales en lugar de solo ruido (-1)
    
    df = df.sample(1000, random_state=42)
    
    # -----------------------------
    # 3. Traducir reseñas
    # -----------------------------
    print("\n🌐 Traduciendo reseñas... (puede tardar unos minutos)")

    df['review_es'] = df['review'].apply(translate_text)

    # Usar texto traducido
    df['review'] = df['review_es']

    # -----------------------------
    # 4. Inicializar pipeline
    # -----------------------------
    print("\n3. Inicializando pipeline...")

    pipeline = ReviewPipeline(
        lang='es',
        n_topics=5
    )

    # -----------------------------
    # 5. Entrenar tópicos
    # -----------------------------
    print("\n4. Entrenando modelo de tópicos...")

    pipeline.train_topics(
        df['review'].tolist()
    )

    # -----------------------------
    # 6. Procesar reseñas
    # -----------------------------
    print("\n5. Procesando reseñas...")

    results_df = pipeline.batch_process(
        df['review'].tolist()
    )

    # -----------------------------
    # 7. Unir resultados
    # -----------------------------
    df_final = pd.concat(
        [df.reset_index(drop=True), results_df],
        axis=1
    )

    # -----------------------------
    # 8. Guardar resultados
    # -----------------------------
    output_path = "data/processed/test.csv"

    df_final.to_csv(
        output_path,
        index=False
    )

    print(f"\n✅ Resultados guardados en: {output_path}")

# -----------------------------
# Ejecutar programa
# -----------------------------
if __name__ == "__main__":
    main()

