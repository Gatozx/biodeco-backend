import os
from dotenv import load_dotenv
from openai import OpenAI
import replicate  # <--- IMPORTAMOS LA NUEVA LIBRERÍA

# 1. CARGAMOS LAS VARIABLES
load_dotenv()

# --- CONFIGURACIÓN DE LOS CLIENTES ---

# Cliente A: EL CEREBRO (DeepSeek)
client_deepseek = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

# Nota: Replicate se configura solo automáticamente al leer 
# la variable REPLICATE_API_TOKEN del archivo .env

# --- MEMORIA DEL TERAPEUTA ---
SYSTEM_PROMPT = """
Eres un terapeuta experto en Biodecodificación. Tu objetivo es dialogar,
hacer preguntas cortas para indagar y encontrar el conflicto emocional.
Sé cálido y empático.
"""
historial = [{"role": "system", "content": SYSTEM_PROMPT}]

# --- FUNCIONES ---

def transcribir_audio_replicate(ruta_archivo):
    print("🎤 Conectando con Replicate para buscar la última versión de Whisper...")
    try:
        input_audio = open(ruta_archivo, "rb")
        
        # 1. BUSCAMOS LA VERSIÓN MÁS RECIENTE AUTOMÁTICAMENTE
        # En lugar de pegar el código raro, le pedimos a Replicate:
        # "¿Cuál es la última versión de openai/whisper?"
        model = replicate.models.get("openai/whisper")
        latest_version = model.versions.list()[0] # Tomamos la primera de la lista (la más nueva)
        
        print(f"   (Usando versión: {latest_version.id[:10]}...)")

        # 2. EJECUTAMOS ESA VERSIÓN
        output = replicate.run(
            f"openai/whisper:{latest_version.id}", # Usamos el ID que acabamos de encontrar
            input={
                "audio": input_audio,
                "model": "large-v3",
                "language": "es",    
                "translate": False,
                "temperature": 0
            }
        )
        
        # 3. PROCESAMOS EL RESULTADO
        texto_detectado = ""
        if isinstance(output, dict) and "text" in output:
             texto_detectado = output["text"]
        else:
             texto_detectado = str(output)

        print(f"📝 El paciente dijo: {texto_detectado}")
        return texto_detectado

    except Exception as e:
        print(f"❌ Error en Replicate: {e}")
        return ""
    
def pensar_respuesta(texto_usuario):
    print("🧠 Analizando conflicto (DeepSeek)...")
    
    # Agregamos lo que dijo el usuario a la memoria
    historial.append({"role": "user", "content": texto_usuario})
    
    try:
        response = client_deepseek.chat.completions.create(
            model="deepseek-chat",
            messages=historial,
            temperature=0.7
        )
        respuesta = response.choices[0].message.content
        
        # Agregamos la respuesta de la IA a la memoria
        historial.append({"role": "assistant", "content": respuesta})
        return respuesta
    except Exception as e:
        return f"Error pensando: {e}"

# --- EJECUCIÓN ---
if __name__ == "__main__":
    print("--- SISTEMA: REPLICATE (OÍDO) + DEEPSEEK (CEREBRO) ---")
    
    archivo_audio = "prueba.mp3" 
    
    # Verificamos que tengas el archivo listo
    if os.path.exists(archivo_audio):
        
        # 1. El paciente habla (Audio -> Texto)
        texto_transcrito = transcribir_audio_replicate(archivo_audio)
        
        if texto_transcrito:
            # 2. El terapeuta piensa (Texto -> Texto)
            respuesta = pensar_respuesta(texto_transcrito)
            
            print(f"\n👩‍⚕️ Terapeuta IA: {respuesta}")
            
            # (Aquí iría el paso 3: ElevenLabs para convertir la respuesta en voz)
    else:
        print(f"⚠️ ATENCIÓN: No encontré '{archivo_audio}'.")
        print("Graba una nota de voz con tu celular, pásala a esta carpeta y llámala 'prueba.mp3'")