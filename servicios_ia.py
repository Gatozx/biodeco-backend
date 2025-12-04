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
    Eres un Asistente Clínico experto en Biodecodificación y Nueva Medicina Germánica (NMG).
    Estás conectado a un sistema que REQUIERE una respuesta en formato JSON estricto.
    
    TU MISIÓN:
    1. Analiza el diálogo. Identifica al PACIENTE (quien cuenta el síntoma).
    2. Ignora saludos o charla trivial.
    3. Extrae: Síntoma, Emoción Oculta, Conflicto Biológico y Fase del Conflicto.
    4. Genera Recomendaciones prácticas (psicomagia o toma de conciencia).
    
    FORMATO DE SALIDA (JSON PURO):
    {
        "motivo_consulta": "Texto breve",
        "emocion_base": "Texto breve",
        "organo_afectado": "Texto breve",
        "conflicto_biologico": "Texto técnico",
        "diagnostico_tecnico": "Explicación de la fase (Activa/Reparación) y sentido biológico.",
        "recomendaciones": ["Acción 1", "Acción 2", "Frase sanadora"],
        "resumen_sesion": "Resumen ejecutivo."
    }
    
    IMPORTANTE: NO escribas nada fuera del JSON. NO uses bloques de código markdown (```json). Solo el JSON crudo.
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