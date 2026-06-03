id="34w4o0"
from datasets import load_dataset
import pandas as pd
from src.pipeline import ReviewPipeline
from deep_translator import GoogleTranslator

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
    # 1. Cargar dataset
    # -----------------------------
    print("\n1. Cargando dataset de reseñas en español...")

    dataset = load_dataset("SetFit/amazon_reviews_multi_es")

    df = dataset['train'].to_pandas()

    print(f"   ✅ Reseñas cargadas: {len(df)}")

    # -----------------------------
    # 2. Preparar datos
    # -----------------------------
    print("\n2. Preparando datos...")

    print("\n📌 Columnas disponibles:")
    print(df.columns)

    # Seleccionar columnas correctas
    df = df[['text', 'label_text']]

    # Eliminar nulos
    df = df.dropna()

    # Renombrar columnas
    df.rename(columns={
        'text': 'review',
        'label_text': 'sentiment'
    }, inplace=True)

    # Reducir tamaño para pruebas
    df = df.sample(50, random_state=42)

    # -----------------------------
    # 3. Traducir reseñas
    # -----------------------------
    print("\n🌐 Traduciendo reseñas... (puede tardar)")

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
