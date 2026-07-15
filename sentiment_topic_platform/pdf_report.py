from weasyprint import HTML
import google.generativeai as genai
from datetime import datetime

def generar_agente_pdf_ia(instruccion_usuario, datos_completos_csv):
    # 1. Obtenemos la fecha actual
    fecha_actual = datetime.now().strftime("%d de %B de %Y")
    
    # 2. El Prompt: Le pedimos a Gemini que analice y nos devuelva SÓLO el texto para rellenar la plantilla
    prompt_agente = f"""
    Eres un Científico de Datos experto. Base de datos:
    {datos_completos_csv}
    
    Petición del usuario: "{instruccion_usuario}"
    
    Analiza los datos y redacta el informe en formato HTML. 
    REGLA ESTRICTA: Devuelve ÚNICAMENTE este bloque HTML rellenado con tu análisis. No cambies las clases CSS (class="..."), solo cambia el texto en español por tus conclusiones reales:
    
    <div class="main-title">Informe Ejecutivo - [Inserta el Título Aquí]</div>
    
    <div class="box box-blue">
        <div class="box-header"><div class="num num-blue">1</div><div class="title title-blue">Introducción</div></div>
        <p>[Escribe un párrafo introductorio sobre lo que encontraste en los datos]</p>
    </div>
    
    <div class="box box-red">
        <div class="box-header"><div class="num num-red">2</div><div class="title title-red">Hallazgos Clave</div></div>
        <p>Se han identificado los siguientes aspectos:</p>
        [Escribe 5 líneas usando <div class="list-item">🏷️ <strong>[Aspecto]:</strong> [Descripción]</div>]
        
        <div class="tags-container">
            <p style="font-size:9pt; font-weight:bold;">Palabras emergentes clave:</p>
            [Escribe 5 palabras usando <span class="tag">[Palabra]</span>]
        </div>
    </div>
    
    <div class="box box-green">
        <div class="box-header"><div class="num num-green">3</div><div class="title title-green">Recomendaciones</div></div>
        <table class="rec-table">
            <tr>
                <td class="rec-td"><h4>🎯 1. [Título Rec 1]</h4><ul><li>[Punto 1]</li><li>[Punto 2]</li></ul></td>
                <td class="rec-td"><h4>📏 2. [Título Rec 2]</h4><ul><li>[Punto 1]</li><li>[Punto 2]</li></ul></td>
                <td class="rec-td"><h4>✨ 3. [Título Rec 3]</h4><ul><li>[Punto 1]</li><li>[Punto 2]</li></ul></td>
            </tr>
        </table>
    </div>
    """
    
    # 3. Procesamiento con Gemini
    model = genai.GenerativeModel('gemini-2.5-flash')
    respuesta_ia = model.generate_content(prompt_agente).text
    
    # 4. Inyectamos la respuesta de la IA dentro de nuestro diseño maestro CSS
    plantilla_html = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
    <meta charset="UTF-8">
    <style>
        @page {{ size: A4; margin: 15mm; background-color: #ffffff; }}
        body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; color: #333; line-height: 1.4; }}
        * {{ box-sizing: border-box; }}
        .header {{ background-color: #092140; color: white; padding: 30px 20px; margin: -15mm -15mm 20px -15mm; }}
        .header h1 {{ margin: 0 0 5px 0; font-size: 20pt; text-transform: uppercase; }}
        .header p {{ margin: 0; font-size: 11pt; font-style: italic; color: #a9b5c2; }}
        .main-title {{ color: #b71c1c; font-size: 18pt; font-weight: bold; margin-bottom: 10px; }}
        .meta {{ display: table; width: 100%; margin-bottom: 20px; font-size: 10pt; font-weight: bold; }}
        .meta-cell {{ display: table-cell; }}
        .box {{ border-radius: 10px; padding: 15px; margin-bottom: 20px; page-break-inside: avoid; }}
        .box-blue {{ border: 2px solid #1976d2; }}
        .box-red {{ border: 2px solid #d32f2f; }}
        .box-green {{ border: 2px solid #388e3c; }}
        .box-header {{ font-size: 14pt; font-weight: bold; margin-bottom: 10px; display: table; }}
        .box-header .num {{ display: table-cell; color: white; padding: 4px 10px; border-radius: 5px; text-align: center; }}
        .box-header .title {{ display: table-cell; vertical-align: middle; padding-left: 10px; }}
        .num-blue {{ background-color: #1976d2; }} .title-blue {{ color: #1976d2; }}
        .num-red {{ background-color: #d32f2f; }} .title-red {{ color: #d32f2f; }}
        .num-green {{ background-color: #388e3c; }} .title-green {{ color: #388e3c; }}
        .list-item {{ margin-bottom: 8px; font-size: 10.5pt; }}
        .tags-container {{ border: 1px dashed #d32f2f; border-radius: 8px; padding: 10px; margin-top: 15px; background-color: #fff9f9; }}
        .tag {{ display: inline-block; border: 1px solid #d32f2f; color: #d32f2f; border-radius: 12px; padding: 3px 10px; margin: 3px; font-size: 9pt; font-weight: bold; background-color: white; }}
        .rec-table {{ width: 100%; border-spacing: 10px; border-collapse: separate; margin: -10px; }}
        .rec-td {{ width: 33.33%; border: 1px solid #388e3c; border-radius: 8px; padding: 12px; vertical-align: top; background-color: #f1f8e9; }}
        .rec-td h4 {{ color: #2e7d32; margin: 0 0 10px 0; font-size: 11pt; text-align: center; }}
        .rec-td ul {{ padding-left: 15px; margin: 0; font-size: 9.5pt; }}
        .footer-box {{ background-color: #092140; color: white; border-radius: 10px; padding: 20px; margin-top: 20px; page-break-inside: avoid; }}
    </style>
    </head>
    <body>
        <div class="header">
            <h1>REPORTE INTELIGENTE DE SENTIMIENTO Y TÓPICOS</h1>
            <p>Plataforma avanzada en la nube para análisis de reseñas</p>
        </div>
        
        <div class="meta">
            <div class="meta-cell">📅 Fecha del Informe: {fecha_actual}</div>
            <div class="meta-cell" style="text-align:right;">👤 Analista: IA Autónomo</div>
        </div>
        
        <!-- AQUI INYECTAMOS LA RESPUESTA DE LA IA CON LOS DATOS REALES -->
        {respuesta_ia}
        
        <div class="footer-box">
            <h3 style="margin: 0 0 5px 0;">⭐ Conclusión General</h3>
            <p style="margin: 0; font-size: 10pt; color: #cfd8dc;">Este documento fue generado dinámicamente mediante el procesamiento de lenguaje natural y análisis de sentimiento, extrayendo patrones clave para facilitar la toma de decisiones estratégicas de negocio.</p>
        </div>
    </body>
    </html>
    """
    
    # 5. Weasyprint convierte el HTML super-estilizado a PDF en milisegundos
    pdf_bytes = HTML(string=plantilla_html).write_pdf()
    
    return pdf_bytes