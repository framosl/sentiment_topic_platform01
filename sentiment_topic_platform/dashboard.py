import plotly.graph_objects as go 
import re
from pptx import Presentation
from ppt_report import generar_ppt_ejecutivo
import io
import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

import logging
logging.getLogger("transformers").setLevel(logging.ERROR)

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
from pptx.util import Inches, Pt
from wordcloud import WordCloud
import requests
from bertopic import BERTopic
import google.generativeai as genai
from fpdf import FPDF
from pdf_report import generar_agente_pdf_ia
from pdf_report import *

# Configuramos la IA leyendo la clave secreta de forma segura
#try:
#    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
#except Exception as e:
#    st.error(f"🚨 Error de configuración: {e}") # <-- Agrega esta línea
#    st.warning("⚠️ El sistema de IA Generativa está en pausa. Configura tu GEMINI_API_KEY en .streamlit/secrets.toml")

# Configuramos la IA buscando primero en los secretos de Streamlit, 
# y si no, buscamos en las variables de entorno de Railway
api_key = st.secrets.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")

if api_key:
    genai.configure(api_key=api_key)
else:
    st.error("❌ Error de configuración: No se encontró la clave de la API.")
    st.warning("⚠️ El sistema de IA Generativa está en pausa. Configura tu GEMINI_API_KEY en Railway.")
    st.stop() # Detiene la ejecución del dashboard para que no intente usar la IA
# -----------------------------
# CONFIGURACIÓN Y ESTILOS
# -----------------------------
st.set_page_config(
    page_title="Sentimientos y Analisis de Reseñas",
    layout="wide",
    page_icon="📊"
)

st.markdown("""
    <style>
    div[data-testid="stMetricValue"] { font-size: 28px; font-weight: 600; color: #1976d2; }
    .stAlert { padding: 10px; }
    </style>
""", unsafe_allow_html=True)

st.title("📊 Sentimientos y Análisis de Reseñas")
st.caption("Plataforma Avanzada de Inteligencia de Negocios | NLP + BERTopic")

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
            break

    if df is None:
        return None

    df.columns = df.columns.str.lower().str.strip()

    if "review" not in df.columns:
        possible_text_cols = ["text", "review_body", "review_text", "comentario", "comentarios"]
        for col in possible_text_cols:
            if col in df.columns:
                df.rename(columns={col: "review"}, inplace=True)
                break

    if "sentiment" not in df.columns:
        if "stars" in df.columns:
            def map_sentiment(x):
                try: x = float(x)
                except: return "neutral"
                if x <= 2: return "negativo"
                elif x == 3: return "neutral"
                else: return "positivo"
            df["sentiment"] = df["stars"].apply(map_sentiment)
        else:
            df["sentiment"] = "neutral"

    df["sentiment"] = df["sentiment"].astype(str).str.lower().str.strip()

    def normalize_sentiment(val):
        if val in ["0", "1", "0.0", "1.0"]: return "negativo"
        elif val in ["3", "4", "3.0", "4.0"]: return "positivo"
        elif val in ["2", "2.0"]: return "neutral"
        return val 
    df["sentiment"] = df["sentiment"].apply(normalize_sentiment)
    
    if "topic" in df.columns:
        def limpiar_topico(valor):
            val_str = str(valor).replace("np.int64(", "").replace("np.float32(", "").replace(")", "")
            match_dict = re.search(r"topic_id['\"]?\s*:\s*(-?\d+)", val_str)
            if match_dict: return match_dict.group(1)
            match_suelto = re.search(r"(-?\d+)", val_str.strip())
            if match_suelto: return match_suelto.group(1)
            return val_str

        df["topic_limpio"] = df["topic"].apply(limpiar_topico).astype(str).str.strip()
        
        diccionario_tematicas = {
            "0": "Relación Calidad-Precio", 
            "1": "Experiencia de Uso",    
            "2": "Funcionamiento y Problemas Técnicos",
            "3": "Cumplimiento de Expectativas",
            "4": "Envío y Empaque",
            "-1": "Comentarios Generales"
        }
        df["tematica_resena"] = df["topic_limpio"].apply(
            lambda x: diccionario_tematicas.get(str(x), "Otras Temáticas")
        )
        
    return df

df = load_data()

if df is None or df.empty:
    st.error("❌ No se encontró dataset")
    st.stop()

# -----------------------------
# SIDEBAR
# -----------------------------
st.sidebar.header("⚙️ Panel de Control")

with st.sidebar.expander("🔍 Filtros de Segmentación", expanded=True):
    if "product_category" in df.columns:
        lista_categorias = ["Todas las categorías"] + sorted(df["product_category"].dropna().unique().tolist())
        categoria_seleccionada = st.selectbox("📦 Categoría:", options=lista_categorias)
        if categoria_seleccionada != "Todas las categorías":
            df = df[df["product_category"] == categoria_seleccionada]

    lista_tematicas = ["Todas"] + list(df["tematica_resena"].unique())
    tematica_seleccionada = st.selectbox("🛍️ Temática NLP:", options=lista_tematicas)
    if tematica_seleccionada != "Todas":
        df = df[df["tematica_resena"] == tematica_seleccionada]

with st.sidebar.expander("🎭 Filtro de Polaridad", expanded=True):
    sentiments = df["sentiment"].dropna().unique()
    selected = st.multiselect("Filtrar sentimiento:", sentiments, default=sentiments)
    df = df[df["sentiment"].isin(selected)]

if df.empty:
    st.warning("No hay datos con esos filtros combinados.")
    st.stop()

# -----------------------------
# KPIs
# -----------------------------
total = len(df)
pos = (df["sentiment"] == "positivo").sum()
neg = (df["sentiment"] == "negativo").sum()
neu = ((df["sentiment"] == "neutral").sum() + (df["sentiment"] == "neutro").sum())

with st.container(border=True):
    st.subheader("📋 Módulo de Control de Muestras")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("📄 Total Reviews", total)
    c2.metric("😊 Positivas", pos)
    c3.metric("😡 Negativas", neg)
    c4.metric("😐 Neutrales", neu)

st.write("") 

# -----------------------------
# TABS REORGANIZADAS
# -----------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Distribución General", 
    "🔥 Análisis Multidimensional (BI)", 
    "🧠 Minería de Texto", 
    "🤖 Pruebas de API e Historial"
])

# -----------------------------
# TAB 1: DISTRIBUCIÓN GENERAL
# -----------------------------
with tab1:
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("#### 🎯 Composición Relativa del Sentimiento")
        fig_pie = px.pie(
            df, names="sentiment", hole=0.4,
            color="sentiment",
            color_discrete_map={"positivo": "#2e7b32", "negativo": "#d32f2f", "neutral": "#1976d2"}
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, width="stretch") 

    with col2:
        st.write("#### 📊 Desglose de Temáticas por Sentimiento")
        fig_bar_stack = px.bar(
            df, 
            x="sentiment", 
            color="tematica_resena",
            title="Distribución de Tópicos dentro de cada Polaridad (👇 Haz clic para auditar)",
            labels={"sentiment": "Polaridad", "count": "Cantidad de Reseñas", "tematica_resena": "Temática NLP"},
            barmode="stack"
        )
        # Habilitamos la captura de eventos interactivos en la barra
        evento_clic = st.plotly_chart(
            fig_bar_stack, 
            width="stretch",
            on_select="rerun",
            selection_mode="points"
        )

    # --- NUEVA SECCIÓN DE AUDITORÍA DINÁMICA CON ANALÍTICA PRESCRIPTIVA ---
    st.write("")
    if evento_clic and len(evento_clic.get("selection", {}).get("points", [])) > 0:
        sentimiento_tocado = evento_clic["selection"]["points"][0]["x"]
        
        # En lugar de solo sacar el texto, sacamos el DataFrame filtrado para tener todos los datos
        df_filtrado = df[df["sentiment"] == sentimiento_tocado].dropna(subset=["review"])
        cantidad_kpi = len(df_filtrado)
        
        st.divider()
        st.markdown(f"### 🔍 Visor de Auditoría: Segmento **{sentimiento_tocado.upper()}** ({cantidad_kpi} registros)")
        
        # Diccionario de Analítica Prescriptiva (Reglas de Negocio)
        def obtener_recomendacion(tematica):
            recomendaciones = {
                "Relación Calidad-Precio": "💰 Sugerencia: Evaluar política de precios frente a la competencia o resaltar mejor el valor agregado en marketing.",
                "Experiencia de Uso": "📖 Sugerencia: Mejorar el manual de usuario o incluir un código QR en la caja con un tutorial en video.",
                "Funcionamiento y Problemas Técnicos": "⚙️ Sugerencia: Escalar reporte a Control de Calidad (QA) y pausar temporalmente el lote de fabricación actual.",
                "Cumplimiento de Expectativas": "🔍 Sugerencia: Auditar y ajustar la descripción del producto en Amazon/Web para no generar expectativas irreales.",
                "Envío y Empaque": "📦 Sugerencia: Levantar un ticket con el proveedor de logística y reforzar el material de embalaje protector."
            }
            return recomendaciones.get(tematica, "📞 Sugerencia: Contactar al cliente directamente para investigar el caso a profundidad.")

        # Contenedor elegante con altura fija y scroll dinámico
        with st.container(height=400, border=True):
            for i, row in df_filtrado.reset_index().iterrows():
                reseña_texto = row["review"]
                tematica_asociada = row.get("tematica_resena", "Comentarios Generales")
                
                with st.expander(f"📋 Reseña #{i+1} | Tópico detectado: {tematica_asociada}"):
                    if sentimiento_tocado == "positivo":
                        st.success(reseña_texto)
                    elif sentimiento_tocado == "negativo":
                        st.error(reseña_texto)
                        # --- AQUÍ INYECTAMOS LA RECOMENDACIÓN ---
                        recomendacion = obtener_recomendacion(tematica_asociada)
                        st.warning(f"**Acción Correctiva Automatizada:**\n\n{recomendacion}")
                    else:
                        st.info(reseña_texto)

    # --- NUEVO: GRÁFICO CONDICIONAL "PANORAMA MACRO" INTERACTIVO ---
    if "product_category" in df.columns and categoria_seleccionada == "Todas las categorías":
        st.divider()
        st.write("#### 🏆 Rendimiento Global por Categoría de Producto (👇 Haz clic en una barra para auditar)")
        st.caption("Volumen de polaridad comparado entre todos los departamentos.")
        
        # Agrupamos los datos para que Plotly los maneje perfecto al hacer clic
        df_grouped = df.groupby(["product_category", "sentiment"]).size().reset_index(name="cantidad")
        
        fig_cat = px.bar(
            df_grouped, 
            y="product_category", 
            x="cantidad",
            color="sentiment",
            barmode="group",
            orientation="h",
            color_discrete_map={"positivo": "#2e7b32", "negativo": "#d32f2f", "neutral": "#1976d2"}
        )
        
        fig_cat.update_layout(
            yaxis={'categoryorder':'total ascending'},
            xaxis_title="Cantidad de Reseñas",
            yaxis_title="Categoría del Producto",
            height=450
        )
        
        # Capturamos el evento interactivo
        evento_clic_cat = st.plotly_chart(
            fig_cat, 
            width="stretch",
            on_select="rerun",
            selection_mode="points"
        )

        # Desglose de la información al hacer clic
        if evento_clic_cat and len(evento_clic_cat.get("selection", {}).get("points", [])) > 0:
            punto_tocado = evento_clic_cat["selection"]["points"][0]
            categoria_tocada = punto_tocado["y"]
            
            # Extraemos la polaridad basada en la curva tocada
            # Plotly Express guarda el nombre de la variable (positivo/negativo) en curveNumber o legendgroup
            if "legendgroup" in punto_tocado:
                sentimiento_real = punto_tocado["legendgroup"]
            else:
                sentimiento_real = "negativo" # Fallback por defecto si Plotly cambia la estructura
                
            st.markdown(f"### 📦 Auditoría Focalizada: **{categoria_tocada}** | Polaridad: **{sentimiento_real.upper()}**")
            
            reseñas_cat_filtradas = df[(df["product_category"] == categoria_tocada) & (df["sentiment"] == sentimiento_real)]["review"].dropna().tolist()
            
            with st.container(height=300, border=True):
                if not reseñas_cat_filtradas:
                    st.info("No se encontraron detalles para esta selección.")
                for i, res in enumerate(reseñas_cat_filtradas):
                    with st.expander(f"📋 Reseña #{i+1}"):
                        if sentimiento_real == "positivo": st.success(res)
                        elif sentimiento_real == "negativo": st.error(res)
                        else: st.info(res)

# -----------------------------
# TAB 2: ANÁLISIS MULTIDIMENSIONAL Y REPORTE GERENCIAL IA
# -----------------------------
with tab2:
    st.subheader("🗺️ Matriz de Correlación Semántica (Heatmap)")
    
    heatmap_data = pd.crosstab(df['tematica_resena'], df['sentiment'])
    fig_heat = px.imshow(
        heatmap_data, 
        labels=dict(x="Polaridad del Sentimiento", y="Tópicos Detectados (BERTopic)", color="Frecuencia"),
        color_continuous_scale='YlOrRd',
        text_auto=True,
        aspect="auto"
    )
    st.plotly_chart(fig_heat, width="stretch")

    st.divider()
    
    col_bi1, col_bi2 = st.columns(2)
    
    with col_bi1:
        st.subheader("🔲 Vista Jerárquica (Sunburst Chart)")
        st.caption("Estructura concéntrica interactiva: Temática Principal ➡️ Sentimiento Asociado")
        fig_sunburst = px.sunburst(
            df, 
            path=['tematica_resena', 'sentiment'], 
            color='sentiment',
            color_discrete_map={"positivo": "#2e7b32", "negativo": "#d32f2f", "neutral": "#1976d2", "(❓)": "#757575"}
        )
        st.plotly_chart(fig_sunburst, width="stretch")
        
    with col_bi2:
        if "confidence" in df.columns:
            st.subheader("📊 Densidad de Confianza por Sentimiento")
            st.caption("Distribución del nivel de certidumbre del clasificador Transformers.")
            fig_conf = px.histogram(
                df, x="confidence", color="sentiment",
                marginal="box",
                nbins=25,
                color_discrete_map={"positivo": "#2e7b32", "negativo": "#d32f2f", "neutral": "#1976d2"},
                barmode="overlay"
            )
            fig_conf.update_layout(xaxis_title="Confianza (0.0 a 1.0)", yaxis_title="Conteo de Ingerencias")
            st.plotly_chart(fig_conf, width="stretch")
    
    # --- NUEVO: REPORTE ESTRATÉGICO GENERATIVO EN LA NUBE ---
    st.divider()
    st.subheader("🚀 Reporte Estratégico Consolidado (Motor Generativo)")
    st.caption("Generación dinámica de planes de acción macro basados en la extracción de tópicos de insatisfacción.")

    if "product_category" in df.columns:
        # 1. Filtramos solo lo que está mal (Negativos)
        df_negativos = df[df["sentiment"] == "negativo"]
        
        if not df_negativos.empty:
            # 2. Agrupamos para ver qué departamento tiene más problemas
            alertas = df_negativos.groupby("product_category").size().reset_index(name="quejas").sort_values(by="quejas", ascending=False)
            
            st.write("🎯 **Focos Rojos Detectados (Prioridad de Inversión y Mejoras):**")
            
            # 3. Generamos las interfaces agrupadas
            for index, row in alertas.iterrows():
                cat = row["product_category"]
                quejas = row["quejas"]
                
                # Extraemos los tópicos específicos de ESA categoría
                top_topicos = df_negativos[df_negativos["product_category"] == cat]["tematica_resena"].value_counts().head(3)
                topicos_str = ", ".join([f"{t} ({c} quejas)" for t, c in top_topicos.items()])

                # Diseño ejecutivo en cajas expansibles
                with st.expander(f"🔴 DEPARTAMENTO: {cat.upper()} ⚠️ ({quejas} clientes insatisfechos)"):
                    
                    st.write("**Principales puntos de fricción extraídos por BERTopic:**")
                    for topico, count in top_topicos.items():
                        st.markdown(f"- 📉 *{topico}* (Mencionado {count} veces)")
                    
                    st.write("---")
                    
                    # Botón individual para llamar a la IA solo cuando el usuario lo pide
                    # Usamos 'key' para que Streamlit no confunda los botones de cada categoría
                    btn_generar = st.button(f"🤖 Generar Estrategia IA para {cat}", key=f"btn_ia_{cat}")
                    
                    if btn_generar:
                        with st.spinner("Conectando con el motor LLM en la nube..."):
                            try:
                                model = genai.GenerativeModel('gemini-2.5-flash')
                                
                                # Prompt inyectando los datos matemáticos reales
                                prompt = f"""
                                Eres un Consultor de Inteligencia de Negocios. El departamento de '{cat}' 
                                tiene {quejas} clientes insatisfechos. 
                                
                                Nuestro modelo de Machine Learning agrupó las quejas en estos tópicos principales:
                                {topicos_str}
                                
                                Redacta un plan de acción ejecutivo de máximo 3 viñetas. 
                                Dile al equipo de operaciones y marketing qué deben investigar y corregir 
                                basándote estrictamente en los tópicos mencionados.
                                """
                                
                                respuesta_ia = model.generate_content(prompt)
                                st.info(f"💡 **Plan de Mitigación Generado por IA:**\n\n{respuesta_ia.text}")
                                
                            except Exception as e:
                                st.error("🚨 Error de conexión con la API de IA. Verifica tu API Key.")
        else:
            st.success("🎉 ¡Excelente! No se registran reseñas negativas consolidadas en este dataset.")
    else:
        st.info("No se encontró la columna de categorías para generar el reporte gerencial.")
    

st.divider()

# Usamos un contenedor con borde para separar el informe del resto del dashboard
with st.container(border=True):
    col_desc, col_btn = st.columns([2, 1])
    
    with col_desc:
        st.subheader("📊 Generador de Informe (PPTX)")
        st.write("Obtén un reporte ejecutivo automatizado basado en los filtros aplicados actualmente. El documento integra métricas, diagnósticos de IA y planes de acción priorizados.")
        
        # Lista estilizada con iconos
        st.markdown("""
        **Contenido del informe:**
        * 🎯 **Resumen y KPIs:** Estado de situación global.
        * 📉 **Análisis Visual:** Distribución y hallazgos por categorías.
        * 🤖 **Diagnóstico IA:** Problemas, fortalezas y recomendaciones estratégicas.
        * 📋 **Plan de Acción:** Matriz de ejecución para el equipo.
        """)

    with col_btn:
        st.write("### 📥 Descargar")
        st.caption("Archivo listo para presentación")
        
        # Generamos el informe solo al hacer clic para no sobrecargar el servidor
        if "ppt_data" not in st.session_state:
            st.session_state["ppt_data"] = None

        if st.button("Generar PPTX Ejecutivo", type="primary", use_container_width=True):
            with st.spinner("Procesando auditoría y generando diapositivas..."):
                # Aquí llamamos a la función con el dataframe filtrado 'df'
                st.session_state["ppt_data"] = generar_ppt_ejecutivo(df)
        
        # Botón de descarga real una vez generado
        if st.session_state["ppt_data"]:
            st.download_button(
                label="✅ Descargar Presentación",
                data=st.session_state["ppt_data"],
                file_name="Informe_Ejecutivo_Auditoria.pptx",
                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                use_container_width=True
            )

# -----------------------------
# Generador de PDF con IA
# -----------------------------
# --- INYECCIÓN DE DISEÑO CSS (TEMA OSCURO) ---
st.markdown("""
<style>
    /* Estilo premium para el botón (Azul brillante que resalta en fondo oscuro) */
    div.stButton > button {
        background-color: #1976d2; 
        color: white;
        border-radius: 8px;
        border: none;
        padding: 10px 24px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    /* Efecto al pasar el mouse por el botón */
    div.stButton > button:hover {
        background-color: #42a5f5; /* Azul más claro y llamativo */
        box-shadow: 0 4px 12px rgba(66, 165, 245, 0.5);
        transform: translateY(-2px);
        color: white;
    }
    /* Estilo para la caja de texto (Fondo oscuro, borde sutil y letra blanca) */
    div.stTextArea > div > div > textarea {
        border-radius: 8px;
        border: 1px solid #4a5a6a;
        background-color: #1e2532; 
        color: #ffffff !important; 
    }
    /* Letra del label de la caja de texto (Gris claro para perfecta legibilidad) */
    .stTextArea label {
        font-weight: bold !important;
        color: #e0e0e0 !important; 
    }
</style>
""", unsafe_allow_html=True)

# --- INTERFAZ DEL AGENTE IA ---
st.markdown("---")

# Usamos un contenedor para agrupar visualmente la sección
with st.container():
    # Título en celeste pastel para que brille sobre el fondo oscuro
    st.markdown("<h3 style='color: #90caf9;'>🤖 Agente Analista IA con Exportación PDF</h3>", unsafe_allow_html=True)
    st.write("Escribe qué necesitas saber de la base de datos y la IA filtrará las categorías para armar tu documento corporativo.")
    
    st.write("") # Espacio en blanco
    
    # Dividimos la pantalla en dos columnas
    col1, col2 = st.columns([3, 1])
    
    with col1:
        instruccion = st.text_area(
            "📝 Instrucciones para el Agente Autónomo:",
            placeholder="Ej: Dame un informe de todas las reseñas negativas de la categoría libros y propón soluciones.",
            height=120
        )
        
    with col2:
        st.write("") 
        st.write("")
        st.write("")
        st.write("")
        # Botón alineado a la derecha
        btn_generar = st.button("🚀 Generar Reporte IA", use_container_width=True)

# --- LÓGICA DE GENERACIÓN CON MANEJO DE ERRORES ---
if btn_generar:
    if instruccion:
        with st.spinner("Procesando la base de datos y maquetando el PDF..."):
            
            # Tomamos una muestra para no exceder el límite de la API
            cantidad_muestra = min(150, len(df))
            datos_csv = df.sample(cantidad_muestra).to_csv(index=False)
            
            try:
                # Intentamos llamar a tu función de PDF
                pdf_bytes = generar_agente_pdf_ia(instruccion, datos_csv)
                
                st.success("¡Análisis completado y PDF generado con éxito!")
                
                # Colocamos el botón de descarga centrado
                _, col_center, _ = st.columns([1, 2, 1])
                with col_center:
                    st.download_button(
                        label="📥 Descargar Documento Final",
                        data=bytes(pdf_bytes),
                        file_name="Agente_Inteligente_Reporte.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                    
            except Exception as e:
                # Si ocurre un error, lo atrapamos aquí en la variable 'e'
                error_str = str(e)
                
                # Verificamos si es el error de cuota de Gemini (429 ResourceExhausted)
                if "429" in error_str or "Quota exceeded" in error_str:
                    
                    # Buscamos el texto exacto de los segundos en el mensaje de Google
                    match = re.search(r'Please retry in (\d+\.?\d*)s', error_str)
                    
                    if match:
                        # Extraemos el número, lo convertimos a entero para redondearlo
                        segundos = int(float(match.group(1))) + 1
                        st.warning(f"⏳ **¡Modo de enfriamiento activo!** La IA ha procesado muchas peticiones seguidas. Por favor, espera **{segundos} segundos** y vuelve a dar clic al botón.")
                    else:
                        st.warning("⏳ **¡Modo de enfriamiento activo!** Límite de consultas rápidas alcanzado. Por favor, espera un minuto y vuelve a intentar.")
                
                else:
                    # Si es otro tipo de error diferente al de la cuota, lo mostramos normal
                    st.error(f"❌ Ocurrió un error inesperado al generar el reporte: {error_str}")
                    
    else:
        st.warning("Por favor, dale una instrucción al agente antes de comenzar.")

# -----------------------------
# TAB 3: MINERÍA DE TEXTO
# -----------------------------
@st.cache_resource
def load_topic_model():
    return BERTopic(language="multilingual", verbose=False)

topic_model = load_topic_model()

with tab3:
    st.subheader("☁️ Extracción de Características Estáticas")
    stop_words_es = [
        "el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del", "a", "al", 
        "en", "y", "o", "que", "es", "son", "se", "por", "para", "con", "como", "no", 
        "este", "esta", "estos", "estas", "pero", "más", "muy", "mi", "me", "su", "lo"
    ]
    texto_total = " ".join(df["review"].dropna().astype(str))
    palabras_filtradas = [
        palabra for palabra in texto_total.lower().split() 
        if palabra not in stop_words_es and len(palabra) > 2
    ]
    text_limpio = " ".join(palabras_filtradas)

    if text_limpio.strip():
        wc = WordCloud(width=1000, height=250, background_color="white", colormap="plasma").generate(text_limpio)
        fig, ax = plt.subplots(figsize=(15, 3))
        ax.imshow(wc, interpolation="bilinear")
        ax.axis("off")
        st.pyplot(fig)
    else:
        st.warning("No hay suficiente texto para generar la nube")

    st.divider()
    st.subheader("🧠 Agrupamiento Semántico Espacial (BERTopic)")
    docs = df["review"].dropna().astype(str).tolist()[:150]
    
    if len(docs) < 10:
        st.warning("Se requieren más documentos para modelar tópicos.")
    else:
        with st.spinner("Procesando embeddings vectoriales..."):
            topics, probs = topic_model.fit_transform(docs)
            info = topic_model.get_topic_info()
        st.dataframe(info, width="stretch")

# -----------------------------
# TAB 4: EVALUADOR IA Y DATOS CRUDOS
# -----------------------------
with tab4:
    st.subheader("🔍 Simulación de Inferencia y Generación de Soluciones (GenAI)")
    
    # 1. Función para limpiar el texto en la memoria de Streamlit
    def limpiar_texto():
        st.session_state["texto_resena"] = ""

    # 2. Inicializamos la variable en la memoria si no existe
    if "texto_resena" not in st.session_state:
        st.session_state["texto_resena"] = ""

    # 3. La caja de texto conectada a la memoria usando 'key'
    user_text = st.text_area(
        "Ingresa el texto de una reseña:", 
        height=90, 
        key="texto_resena"
    )

    # 4. Botones alineados horizontalmente
    col_btn1, col_btn2 = st.columns([1, 5])
    
    with col_btn1:
        btn_analizar = st.button("Analizar con Pipeline Híbrido", type="primary")
    with col_btn2:
        st.button("🧹 Limpiar", on_click=limpiar_texto)

    # 5. Ejecución del análisis
    if btn_analizar:
        if user_text.strip():
            try:
                # Backend procesa el sentimiento y el tópico
                response = requests.post("http://127.0.0.1:8000/analyze", json={"text": user_text})
                result = response.json()
                
                with st.container(border=True):
                    c1, c2 = st.columns([1, 1])
                    with c1:
                        st.write("### Diagnóstico del Sistema")
                        st.metric("Sentimiento Detectado", result["sentiment"].upper())
                        st.write(f"**Categoría Asignada:** {result.get('predicted_category', 'General')}")
                        
                        # Alertas visuales dinámicas
                        if result["sentiment"] == "negativo":
                            st.error("🚨 Atención: Alta probabilidad de insatisfacción del cliente.")
                        elif result["sentiment"] == "positivo":
                            st.success("✅ Excelente: Cliente altamente satisfecho con el producto.")
                        else:
                            st.info("ℹ️ Observación: El cliente tiene una postura neutral o mixta.")
                            
                        # Generación de Estrategia con IA Generativa
                        with st.spinner("🤖 La IA está redactando una estrategia de negocio..."):
                            try:
                                model = genai.GenerativeModel('gemini-2.5-flash')
                                
                                prompt = f"""
                                Eres un Director de Producto experto. Un cliente dejó esta reseña con sentimiento {result['sentiment']}:
                                "{user_text}"
                                
                                Categoría del producto: {result.get('predicted_category', 'General')}.
                                
                                Escribe una recomendación ejecutiva de máximo 2 oraciones.
                                - Si es negativo: di qué acción correctiva tomar.
                                - Si es positivo: sugiere cómo usar este feedback para marketing o ventas.
                                - Si es neutral: sugiere cómo mejorar el producto para convencer al cliente.
                                """
                                
                                respuesta_ia = model.generate_content(prompt)
                                st.warning(f"💡 **Estrategia Generada por IA:**\n\n{respuesta_ia.text}")
                                
                            except Exception as e:
                                st.warning("💡 Sugerencia: Revisa tu API Key de Gemini o tu conexión a internet.")
                                    
                    with c2:
                        fig = go.Figure(go.Indicator(
                            mode = "gauge+number",
                            value = result["confidence"] * 100,
                            title = {'text': "Confianza de Inferencia (%)"},
                            gauge = {'axis': {'range': [0, 100]},
                                     'bar': {'color': "#1976d2"},
                                     'steps': [
                                         {'range': [0, 50], 'color': "#ffcdd2"},
                                         {'range': [50, 85], 'color': "#fff9c4"},
                                         {'range': [85, 100], 'color': "#c8e6c9"}]}
                        ))
                        st.plotly_chart(fig, width="stretch")
            except Exception as e:
                st.error("❌ API fuera de línea. Comprueba que tu servidor FastAPI (Uvicorn) esté corriendo.")
        else:
            st.warning("Por favor, ingresa texto válido antes de analizar.")

    st.divider()
    with st.expander("🗄️ Explorador de Persistencia de Datos (Historial de Consultas)"):
        st.dataframe(df.head(100), width="stretch")


