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
    print(f"🎧 Transcribiendo audio con Replicate (Whisper Large-v3)...")
    try:
        # ID ACTUALIZADO Y VERIFICADO (Whisper Large v3)
        # Este es el ID correcto para el modelo oficial de OpenAI en Replicate
        model_version = "openai/whisper:e39e354773466b955265e969568deb7da217804d8e771ea8c9cd0cef6591f8bc"
        
        output = replicate.run(
            model_version,
            input={
                "audio": open(ruta_audio, "rb"),
                "model": "large-v2",
                "language": "es",
                "translate": False,
                "temperature": 0,
                "transcription": "plain text"
            }
        )
        
        # Procesar respuesta
        texto_final = ""
        if isinstance(output, dict):
            texto_final = output.get('transcription') or output.get('text') or str(output)
        else:
            texto_final = str(output)
             
        print("✅ Transcripción completada.")
        return texto_final.strip()
        
    except Exception as e:
        print(f"❌ Error crítico en Whisper: {e}")
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


def generar_plan_asistente_mentor(datos_terapeuta):
    print("🧭 Generando plan de Asistente + Mentor para terapeuta...")
    prompt = """
    Diseña un plan accionable para un asistente de IA para terapeutas.

    OBJETIVO:
    - Debe funcionar como asistente operativo (prospectos, recordatorios, seguimiento).
    - Debe ayudar a crear contenido para redes y educación.
    - Debe actuar como mentor del terapeuta, mejorando su criterio sesión a sesión.

    REGLAS:
    - Enfatiza confidencialidad y consentimiento informado.
    - No inventes diagnósticos médicos.
    - Entrega respuestas concretas y accionables.

    Devuelve SOLO JSON con esta estructura:
    {
      "vision_producto": "string",
      "modulos_priorizados": [
        {
          "nombre": "string",
          "problema_que_resuelve": "string",
          "mvp_en_2_semanas": ["string"],
          "kpi": "string"
        }
      ],
      "flujo_terapeuta_asistente": ["string"],
      "protocolo_mentor": {
        "antes_sesion": ["string"],
        "durante_sesion": ["string"],
        "despues_sesion": ["string"]
      },
      "motor_contenido": {
        "pilares": ["string"],
        "cadencia_semanal": ["string"],
        "ideas_iniciales": ["string"]
      },
      "riesgos_y_mitigaciones": ["string"],
      "primeros_30_dias": ["string"]
    }

    CONTEXTO TERAPEUTA:
    {datos}
    """

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "system",
                    "content": "Eres un arquitecto de producto para asistentes clínicos con foco ético.",
                },
                {
                    "role": "user",
                    "content": prompt.format(datos=json.dumps(datos_terapeuta, ensure_ascii=False)),
                },
            ],
            temperature=0.3,
            response_format={"type": "json_object"},
        )
        return _limpiar_y_parsear_json(response.choices[0].message.content)
    except Exception as e:
        print(f"❌ Error generando plan asistente-mentor: {e}")
        return {"error": str(e)}

def _limpiar_y_parsear_json(texto):
    try:
        texto = re.sub(r'```json\s*|\s*```', '', texto).strip()
        return json.loads(texto)
    except:
        return {}
