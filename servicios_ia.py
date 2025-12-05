import os
import replicate
from dotenv import load_dotenv
from openai import OpenAI  # Usamos la librería de OpenAI para conectar con DeepSeek

# Cargar variables de entorno (.env)
load_dotenv()

# Configuración del cliente DeepSeek
# Asegúrate de que tu .env tenga DEEPSEEK_API_KEY
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"), 
    base_url="https://api.deepseek.com"
)

def formatear_transcripcion(salida_replicate):
    """
    Función auxiliar para convertir la salida compleja de la IA (JSON)
    en un texto legible tipo guion de teatro.
    """
    texto_formateado = ""
    
    # Verificamos si la salida tiene segmentos (estructura habitual de WhisperX/Diarization)
    # Nota: La estructura puede variar, pero generalmente es una lista de segmentos bajo 'segments'
    try:
        segments = salida_replicate.get('segments', [])
        
        for segment in segments:
            # Replicate suele devolver 'SPEAKER_00', 'SPEAKER_01'. 
            # Tomamos el nombre del hablante y el texto.
            speaker = segment.get('speaker', 'Desconocido')
            text = segment.get('text', '')
            
            # Limpiamos espacios extra
            texto_formateado += f"{speaker}: {text.strip()}\n"
            
        return texto_formateado
        
    except Exception as e:
        print(f"Advertencia al formatear: {e}")
        # Si falla el formato, intentamos devolver la salida cruda convertida a string
        return str(salida_replicate)

def transcribir_sesion(ruta_audio):
    """
    Sube el audio a Replicate usando WHISPER DIARIZATION (Versión Estable ThomasMol).
    """
    print("🎤 Iniciando transcripción con detección de hablantes...")
    
    try:
        # MODELO: thomasmol/whisper-diarization
        # VERSIÓN CONFIRMADA: 1495a9cd... (Es la versión estable más reciente)
        output = replicate.run(
            "thomasmol/whisper-diarization:1495a9cddc83b2203b0d8d3516e38b80fd1572ebc4bc5700ac1da56a9b3ed886",
            input={
                "file": open(ruta_audio, "rb"), # ESTE MODELO USA 'file', NO 'audio'
                "num_speakers": 2,
                "prompt": "Diálogo de terapia en español."
            }
        )
        
        # El modelo devuelve un objeto JSON, lo convertimos a texto plano
        texto_final = formatear_transcripcion(output)
        
        print("✅ Transcripción completada.")
        return texto_final

    except Exception as e:
        print(f"❌ Error en Replicate: {str(e)}")
        raise e

def generar_reporte_clinico(texto_transcrito):
    """
    Envía el texto a DeepSeek V3 para análisis.
    """
    print("🧠 Enviando a DeepSeek V3 (Chat) para análisis clínico...")
    
    prompt_sistema = """
    ACTÚA COMO: Supervisor Clínico Senior y Experto en Nueva Medicina Germánica (NMG) con capacidad de razonamiento deductivo profundo.

TU OBJETIVO: Generar un informe clínico y de auditoría basado en el texto proporcionado (que puede ser una transcripción de sesión o una consulta escrita).

TIENES PROHIBIDO RESPONDER DE INMEDIATO. Debes realizar el siguiente PROCESO MENTAL INTERNO antes de generar el JSON final:

FASE 1: ANÁLISIS PROFUNDO DEL PACIENTE
- Lee todo el texto de manera integral. Identifica el síntoma físico exacto y su capa embrionaria (Endodermo, Mesodermo, Ectodermo).
- Detecta la emoción visceral subyacente (no la que dice el paciente, sino la que siente biológicamente: miedo a morir, pérdida de territorio, separación). Usa pistas contextuales.
- Cruza el síntoma identificado con la Ley de Hierro del Cáncer para encontrar el Conflicto Biológico preciso.

FASE 2: AUDITORÍA DE LA INTERACCIÓN (EL "OJO CLÍNICO")
- Si hay un terapeuta en el texto: Analiza sus intervenciones. ¿Usó escucha activa? ¿Identificó las pistas clave?
- REFLEXIONA: ¿El terapeuta captó la pista más importante o la dejó pasar?
- BUSCA HUECOS: ¿El paciente soltó una frase clave (ej: "desde que murió mi perro...") que fue ignorada?
- Si es solo una consulta escrita: REFLEXIONA sobre qué información falta para completar el cuadro clínico riguroso.

FASE 3: GENERACIÓN DE ESTRATEGIA
- Define recomendaciones prácticas específicas y ejecutables.
- Sugiere actos de psicomagia relevantes al conflicto biológico identificado.

---
FORMATO DE SALIDA OBLIGATORIO:
Tu respuesta debe ser UNICAMENTE un objeto JSON válido. NO uses bloques de código markdown (```json). Solo el texto plano del JSON.

Estructura del JSON:
{
  "motivo_consulta": "Síntoma o queja principal",
  "emocion_base": "La emoción biológica raíz",
  "organo_afectado": "Órgano específico y capa embrionaria",
  "conflicto_biologico": "Definición técnica del conflicto",
  "diagnostico_tecnico": "Explicación breve basada en las 5 Leyes Biológicas",
  "hallazgos_clinicos": "Tu reflexión profunda. Conexiones que la IA detectó entre eventos del pasado y el síntoma actual.",
  "oportunidades_omitidas": [
      "Lista de pistas que el terapeuta pasó por alto.",
      "Temas que el paciente mencionó y requieren indagación profunda.",
      "Preguntas clave que NO se hicieron."
  ],
  "recomendaciones": ["Acción 1", "Acción 2"],
  "resumen_sesion": "Resumen ejecutivo de la interacción."
}
"""

    try:
        response = client.chat.completions.create(
            model="deepseek-chat", # Este modelo apunta automáticamente a DeepSeek-V3
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": f"Analiza esta sesión:\n\n{texto_transcrito}"}
            ],
            stream=False,
            temperature=0.5, # V3 es muy creativo, bajamos la temperatura para asegurar el JSON
            max_tokens=1500
        )
        
        contenido = response.choices[0].message.content
        
        # Limpieza extra por si V3 decide ser amable y poner markdown
        contenido = contenido.replace("```json", "").replace("```", "").strip()
        
        return contenido

    except Exception as e:
        print(f"❌ Error en DeepSeek: {str(e)}")
        # Devolvemos un JSON de error válido para que la App no explote
        return """
        {
            "motivo_consulta": "Error en el análisis",
            "emocion_base": "N/A",
            "organo_afectado": "N/A",
            "conflicto_biologico": "Error de conexión con la IA",
            "diagnostico_tecnico": "No se pudo procesar la solicitud.",
            "recomendaciones": ["Intenta subir el audio nuevamente."],
            "resumen_sesion": "Ocurrió un error técnico."
        }
        """

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": prompt_sistema},
                {"role": "user", "content": f"Analiza esta sesión:\n\n{texto_transcrito}"}
            ],
            stream=False,
            temperature=0.7
        )
        
        contenido = response.choices[0].message.content
        
        # Limpieza de seguridad por si la IA devuelve bloques de código markdown
        contenido = contenido.replace("```json", "").replace("```", "").strip()
        
        return contenido

    except Exception as e:
        print(f"❌ Error en DeepSeek: {str(e)}")
        return "Error generando el reporte."
    

    # ACTUALIZACION FORZADA V3 - SOLICITUD DE JSON