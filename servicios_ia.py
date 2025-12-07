import os
import json
import re
from openai import OpenAI

# Configuración del Cliente
client = OpenAI(
    api_key=os.environ.get("DEEPSEEK_API_KEY"), 
    base_url="https://api.deepseek.com" 
)

def transcribir_sesion(ruta_audio):
    """
    AQUÍ VA TU CÓDIGO DE WHISPER (REPLICATE).
    Pégalo tal cual lo tenías antes.
    """
    pass 

def generar_reporte_clinico(texto_transcrito):
    """
    AGENTE CLINICO ECLÉCTICO (SUPERVISOR DE TERAPEUTAS)
    Usa el Prompt del "Consultor Clínico Ecléctico".
    """
    print("🧠 Iniciando SUPERVISOR CLÍNICO (Enfoque Ecléctico)...")
    
    # ---------------------------------------------------------
    # FASE 1: EXTRACCIÓN DE EVIDENCIA (Para alimentar al supervisor)
    # ---------------------------------------------------------
    print("🔍 Fase 1: Recopilando evidencia de la sesión...")
    prompt_extraccion = """
    Actúa como un Secretario Clínico Meticuloso.
    Lee la transcripción y extrae los siguientes datos crudos en JSON:
    {
      "paciente": {
        "frases_creencias": ["Citas textuales donde P se define a sí mismo o al mundo"],
        "metaforas_fisicas": ["Menciones de cuerpo/síntomas"],
        "historia_familiar": ["Menciones a padres/abuelos/pareja"]
      },
      "terapeuta": {
        "mejores_preguntas": ["Intervenciones que abrieron tema"],
        "momentos_ignorados": ["Temas que P sacó y T no siguió"],
        "contradicciones_no_vistas": ["Incoherencias de P que T dejó pasar"]
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
        raw_extraccion = response1.choices[0].message.content
        datos_fase_1 = _limpiar_y_parsear_json(raw_extraccion)
        print("✅ Fase 1 Completada.")
        
    except Exception as e:
        print(f"❌ Error Fase 1: {e}")
        datos_fase_1 = {}

    # ---------------------------------------------------------
    # FASE 2: ANÁLISIS DEL SUPERVISOR (TU PROMPT EXACTO)
    # ---------------------------------------------------------
    print("❤️ Fase 2: Análisis del Consultor Ecléctico...")
    
    # AQUI ESTÁ TU PROMPT MAESTRO INTEGRADO
    prompt_analisis = """
    # IDENTIDAD: Eres el "Consultor Clínico Ecléctico", una IA especializada en supervisión. Tu cliente es el TERAPEUTA.

    # CONTEXTO: Analiza la transcripción y los datos extraídos.

    ## OBJETIVOS DEL INFORME:
    1. SINTETIZAR el núcleo del caso (Integrativo).
    2. EVALUAR la intervención de T.
    3. SUGERIR líneas de acción.

    ## ESTRUCTURA OBLIGATORIA DE TU RESPUESTA (Genera un texto detallado):

    ### SECCIÓN 1: SÍNTESIS DIAGNÓSTICA
    - Tema Central: (Asunto no resuelto).
    - Creencias Nucleares: (Frases clave del guion de vida).
    - Conexión Simbólica: (Interpretación metafórica del síntoma, NO médica).
    - Origen Sistémico: (Patrones familiares).

    ### SECCIÓN 2: ANÁLISIS DE LA INTERVENCIÓN
    - Puntos Fuertes: (Qué hizo bien T).
    - Puntos Ciegos / Crítica Constructiva: (Temas evitados, contradicciones no señaladas, recursos no aprovechados).

    ### SECCIÓN 3: PROPUESTAS (LÍNEAS DE INVESTIGACIÓN)
    - Línea A (Profundización Emocional).
    - Línea B (Reencuadre Narrativo).
    - Línea C (Tarea Psicomágica).

    ### SECCIÓN 4: INSIGHT TEÓRICO
    - Un breve dato de contexto (Apego, Gestalt, NMG, etc) para educar al terapeuta.

    ---
    DATOS PREVIOS: {datos}
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
        print("✅ Fase 2 Completada (Análisis Generado).")
        
    except Exception as e:
        print(f"❌ Error Fase 2: {e}")
        analisis_texto_fase_2 = "Error en análisis."

    # ---------------------------------------------------------
    # FASE 3: MAPEO A JSON (Adaptación a la App)
    # ---------------------------------------------------------
    print("📊 Fase 3: Formateando para la App...")
    
    prompt_final = """
    Actúa como Traductor de Datos.
    Toma el INFORME DEL CONSULTOR (Fase 2) y vuélcalo en este JSON estricto.

    MAPEO DE CAMPOS:
    - 'motivo_consulta' -> Pon el "Tema Central".
    - 'emocion_base' -> Pon la emoción predominante o atmósfera.
    - 'organo_afectado' -> Pon la "Conexión Simbólica" (Metáfora del cuerpo).
    - 'conflicto_biologico' -> Pon las "Creencias Nucleares".
    - 'hallazgos_clinicos' -> Pon la "Síntesis Diagnóstica" completa (Sistémico + Narrativa).
    - 'diagnostico_tecnico' -> Pon la "SECCIÓN 4: INSIGHT TEÓRICO".
    
    - 'oportunidades_omitidas' -> Pon TODO el contenido de la "SECCIÓN 2: ANÁLISIS DE INTERVENCIÓN" (Puntos ciegos, crítica).
    
    - 'recomendaciones' -> Pon las "Líneas de Investigación" (A, B y C) de la SECCIÓN 3.
    
    - 'resumen_sesion' -> Resumen ejecutivo breve.

    INFORME A PROCESAR:
    {analisis}

    Genera solo el JSON.
    """
    
    try:
        response3 = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "Eres un generador de JSON estricto."},
                {"role": "user", "content": prompt_final.format(
                    analisis=analisis_texto_fase_2
                )}
            ],
            temperature=0.1,
            response_format={ "type": "json_object" }
        )
        
        raw_final = response3.choices[0].message.content
        json_final = _limpiar_y_parsear_json(raw_final)
        print("✅ Reporte Ecléctico Listo.")
        return json_final

    except Exception as e:
        print(f"❌ Error Fase 3: {e}")
        return {"error": "Fallo final", "detalle": str(e)}

def _limpiar_y_parsear_json(texto):
    try:
        texto = re.sub(r'```json\s*|\s*```', '', texto).strip()
        return json.loads(texto)
    except:
        return {}