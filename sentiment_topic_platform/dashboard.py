import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

import logging
logging.getLogger("transformers").setLevel(logging.ERROR)

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
from wordcloud import WordCloud
import requests
from bertopic import BERTopic

# -----------------------------
# CONFIG
# -----------------------------
st.set_page_config(
    page_title="Sentiment Analytics PRO",
    layout="wide",
    page_icon="📊"
)

st.title("📊 Sentiment Analytics PRO")
st.caption("NLP + Sentimiento + BERTopic + API en tiempo real")

# -----------------------------
# LOAD DATA
# -----------------------------
@st.cache_data
def load_data():

    paths = [
        "data/processed/resultados.csv",
        "data/processed/test.csv",
        "data/raw/resenas_sinteticas.csv"
    ]

    df = None

    for path in paths:
        if os.path.exists(path):
            df = pd.read_csv(path)
            st.success(f"Dataset cargado: {path}")
            break

    if df is None:
        return None

    # normalizar columnas
    df.columns = df.columns.str.lower().str.strip()

    # detectar texto
    if "review" not in df.columns:

        possible_text_cols = [
            "text",
            "review_body",
            "review_text",
            "comentario",
            "comentarios"
        ]

        for col in possible_text_cols:
            if col in df.columns:
                df.rename(columns={col: "review"}, inplace=True)
                break

    # crear sentimiento automático
    if "sentiment" not in df.columns:

        if "stars" in df.columns:

            def map_sentiment(x):
                try:
                    x = float(x)
                except:
                    return "neutral"

                if x <= 2:
                    return "negativo"
                elif x == 3:
                    return "neutral"
                else:
                    return "positivo"

            df["sentiment"] = df["stars"].apply(map_sentiment)

        else:
            # fallback inteligente
            df["sentiment"] = "neutral"

    # limpiar
    df["sentiment"] = (
        df["sentiment"]
        .astype(str)
        .str.lower()
        .str.strip()
    )

    return df


df = load_data()

if df is None or df.empty:
    st.error("❌ No se encontró dataset")
    st.stop()

# -----------------------------
# SIDEBAR
# -----------------------------
st.sidebar.header("⚙️ Filtros")

sentiments = df["sentiment"].dropna().unique()

selected = st.sidebar.multiselect(
    "Filtrar sentimiento",
    sentiments,
    default=sentiments
)

df = df[df["sentiment"].isin(selected)]

if df.empty:
    st.warning("No hay datos")
    st.stop()

# -----------------------------
# KPIs
# -----------------------------
total = len(df)

pos = (df["sentiment"] == "positivo").sum()
neg = (df["sentiment"] == "negativo").sum()

neu = (
    (df["sentiment"] == "neutral").sum()
    +
    (df["sentiment"] == "neutro").sum()
)

c1, c2, c3, c4 = st.columns(4)

c1.metric("📄 Total Reviews", total)
c2.metric("😊 Positivas", pos)
c3.metric("😡 Negativas", neg)
c4.metric("😐 Neutrales", neu)

st.divider()

# -----------------------------
# TABS
# -----------------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Sentimientos",
    "☁️ WordCloud",
    "🧠 BERTopic",
    "📋 Dataset",
    "🔍 API Analyzer"
])

# -----------------------------
# TAB 1
# -----------------------------
with tab1:

    st.subheader("Distribución de sentimientos")

    fig = px.pie(
        df,
        names="sentiment",
        hole=0.45,
        title="Distribución"
    )

    st.plotly_chart(fig, width="stretch")

    bar = px.bar(
        x=df["sentiment"].value_counts().index,
        y=df["sentiment"].value_counts().values,
        labels={"x": "Sentimiento", "y": "Cantidad"},
        title="Cantidad por sentimiento"
    )

    st.plotly_chart(bar, width="stretch")

# -----------------------------
# TAB 2
# -----------------------------
with tab2:

    st.subheader("Nube de palabras")

    text = " ".join(
        df["review"]
        .dropna()
        .astype(str)
    )

    if text.strip():

        wc = WordCloud(
            width=1200,
            height=500,
            background_color="white",
            colormap="viridis"
        ).generate(text)

        fig, ax = plt.subplots(figsize=(15, 5))

        ax.imshow(wc, interpolation="bilinear")
        ax.axis("off")

        st.pyplot(fig)

    else:
        st.warning("No hay suficiente texto")

# -----------------------------
# TAB 3
# -----------------------------
@st.cache_resource
def load_topic_model():
    return BERTopic(
        language="multilingual",
        verbose=False
    )

topic_model = load_topic_model()

with tab3:

    st.subheader("Modelado de tópicos")

    docs = (
        df["review"]
        .dropna()
        .astype(str)
        .tolist()
    )

    docs = docs[:150]

    if len(docs) < 10:

        st.warning("Muy pocos datos")

    else:

        with st.spinner("Analizando tópicos..."):

            topics, probs = topic_model.fit_transform(docs)

            info = topic_model.get_topic_info()

        st.success("Tópicos generados")

        st.dataframe(info, width="stretch")

# -----------------------------
# TAB 4
# -----------------------------
with tab4:

    st.subheader("Vista del dataset")

    st.dataframe(df.head(100), width="stretch")

    st.write("Columnas detectadas:")

    st.write(df.columns.tolist())

# -----------------------------
# TAB 5
# -----------------------------
with tab5:

    st.subheader("Analizador en tiempo real")

    user_text = st.text_area(
        "Escribe una reseña"
    )

    if st.button("Analizar reseña"):

        if user_text.strip():

            try:

                response = requests.post(
                    "http://127.0.0.1:8000/analyze",
                    json={"text": user_text}
                )

                result = response.json()

                st.success("Análisis completado")

                st.json(result)

            except Exception as e:

                st.error("❌ API no disponible")

                st.code(str(e))

        else:

            st.warning("Escribe texto primero")