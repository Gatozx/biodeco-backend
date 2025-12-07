import os
import json
import re
import replicate
from openai import OpenAI

# 1. Configuración de Clientes
# Asegúrate de tener las API KEYS en tu archivo .env
client = OpenAI(
    api_key=os.environ.get("DEEPSEEK_API_KEY"), 
    base_url="https://api.deepseek.com" 
)

# 2. FUNCIÓN PARA ESCUCHAR (Recuperada)
# En servicios_ia.py

def transcribir_sesion(ruta_audio):
    print(f"🎧 Transcribiendo audio con Replicate (Modelo Oficial)...")
    try:
        # Usamos el modelo OFICIAL de OpenAI (Whisper Large v3)
        # Es mucho más estable y robusto.
        output = replicate.run(
            "openai/whisper:4d50797290df275329f202e48c76360b3f22b08d28c196cbc54649553200524c",
            input={
                "audio": open(ruta_audio, "rb"), # OJO: Aquí se llama 'audio', no 'file'
                "model": "large-v3",
                "language": "es",
                "translate": False,
                "temperature": 0,
                "transcription": "plain text"
            }
        )
        
        # El modelo oficial suele devolver un diccionario con el campo 'text' o 'transcription'
        # Vamos a asegurar que obtenemos el texto sin importar el formato
        texto_final = ""
        
        if isinstance(output, dict):
            # A veces viene como {'text': 'Hola...'} o {'transcription': 'Hola...'}
            texto_final = output.get('transcription') or output.get('text') or str(output)
        else:
            # Si viene directo
            texto_final = str(output)
             
        print("✅ Transcripción completada.")
        return texto_final.strip()
        
    except Exception as e:
        print(f"❌ Error crítico en Whisper: {e}")
        # Retornamos None para que el frontend sepa que falló
        return None

# 3. FUNCIÓN PARA PENSAR (Supervisor Ecléctico)
def generar_reporte_clinico(texto_transcrito):
    print("🧠 Iniciando SUPERVISOR CLÍNICO (Enfoque Ecléctico)...")
    
    # --- FASE 1: EXTRACCIÓN ---
    print("🔍 Fase 1: Recopilando evidencia...")
    prompt_extraccion = """
    Actúa como un Secretario Clínico. Extrae datos crudos en JSON:
    {
      "paciente": {
        "frases_creencias": ["Citas textuales"],
        "metaforas_fisicas": ["Menciones de síntomas"],
        "historia_familiar": ["Menciones a familia"]
      },
      "terapeuta": {
        "mejores_preguntas": ["Intervenciones clave"],
        "momentos_ignorados": ["Temas no seguidos"]
      }
    }
    Transcripción:
    """
    try:
        response1 = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "Eres un extractor de datos objetivo."},
                {"role": "user", "content": prompt_extraccion + texto_transcrito[:6000]}
            ],
            temperature=0.0,
        )
        datos_fase_1 = _limpiar_y_parsear_json(response1.choices[0].message.content)
        print("✅ Fase 1 Completada.")
    except Exception as e:
        print(f"❌ Error Fase 1: {e}")
        datos_fase_1 = {}

    # --- FASE 2: ANÁLISIS DEL SUPERVISOR ---
    print("❤️ Fase 2: Análisis del Consultor Ecléctico...")
    prompt_analisis = """
    # IDENTIDAD: Consultor Clínico Ecléctico. Cliente: TERAPEUTA.
    
    ## OBJETIVOS:
    1. SINTETIZAR el núcleo del caso (Narrativo/Sistémico).
    2. EVALUAR la intervención de T.
    3. SUGERIR líneas de acción.

    ## ESTRUCTURA RESPUESTA:
    ### SECCIÓN 1: SÍNTESIS DIAGNÓSTICA
    - Tema Central (Asunto no resuelto).
    - Creencias Nucleares (Guion de vida).
    - Conexión Simbólica (Metáfora del síntoma).
    - Origen Sistémico (Patrones familiares).

    ### SECCIÓN 2: ANÁLISIS DE INTERVENCIÓN
    - Puntos Fuertes.
    - Puntos Ciegos / Crítica (Temas evitados, contradicciones).

    ### SECCIÓN 3: PROPUESTAS
    - Línea A (Profundización Emocional).
    - Línea B (Reencuadre Narrativo).
    - Línea C (Tarea Psicomágica).

    ### SECCIÓN 4: INSIGHT TEÓRICO
    - Dato breve de contexto teórico.

    ---
    DATOS: {datos}
    """
    try:
        response2 = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "Eres un Supervisor Clínico Senior."},
                {"role": "user", "content": prompt_analisis.format(datos=json.dumps(datos_fase_1))}
            ],
            temperature=0.4, 
        )
        analisis_texto_fase_2 = response2.choices[0].message.content
        print("✅ Fase 2 Completada.")
    except Exception as e:
        print(f"❌ Error Fase 2: {e}")
        analisis_texto_fase_2 = "Error en análisis."

    # --- FASE 3: MAPEO A JSON ---
    print("📊 Fase 3: Formateando para la App...")
    prompt_final = """
    Vuelca el INFORME (Fase 2) en este JSON estricto:
    {{
      "motivo_consulta": "Pon el Tema Central",
      "emocion_base": "Emoción predominante",
      "organo_afectado": "Pon la Conexión Simbólica",
      "conflicto_biologico": "Pon las Creencias Nucleares",
      "hallazgos_clinicos": "Pon la Síntesis Diagnóstica completa",
      "diagnostico_tecnico": "Pon la SECCIÓN 4 (Insight Teórico)",
      "oportunidades_omitidas": "Pon TODO el contenido de la SECCIÓN 2 (Análisis Intervención)",
      "recomendaciones": "Pon las Líneas de Investigación (SECCIÓN 3)",
      "resumen_sesion": "Resumen breve"
    }}
    INFORME: {analisis}
    """
    try:
        response3 = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "Eres un generador JSON."},
                {"role": "user", "content": prompt_final.format(analisis=analisis_texto_fase_2)}
            ],
            temperature=0.1,
            response_format={ "type": "json_object" }
        )
        json_final = _limpiar_y_parsear_json(response3.choices[0].message.content)
        print("✅ Reporte Listo.")
        return json_final
    except Exception as e:
        print(f"❌ Error Fase 3: {e}")
        return {"error": str(e)}

def _limpiar_y_parsear_json(texto):
    try:
        texto = re.sub(r'```json\s*|\s*```', '', texto).strip()
        return json.loads(texto)
    except:
        return {}