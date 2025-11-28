import os
from dotenv import load_dotenv
from openai import OpenAI
import replicate

# 1. CONFIGURACIÓN
load_dotenv()

client_deepseek = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

# 2. PROMPT DEL SUPERVISOR (El que definimos arriba)
SYSTEM_PROMPT_SUPERVISOR = """
ACTÚA COMO: Un Supervisor Clínico Senior experto en Biodecodificación, NMG y PNL.
TU TAREA: Analizar la transcripción de texto de una sesión de terapia.

OBJETIVOS DEL ANÁLISIS:
1. RESUMEN DEL SÍNTOMA: Identifica el malestar físico o emocional principal.
2. HIPÓTESIS DEL CONFLICTO: Según la Biodecodificación, ¿cuál es el conflicto biológico probable?
3. PUNTOS CIEGOS: ¿Qué dijo el paciente que podría ser clave y requiere más indagación?
4. SUGERENCIAS: Sugiere 2 preguntas clave para profundizar.

FORMATO DE RESPUESTA:
Responde en formato reporte profesional para el terapeuta.
Usa los encabezados: [RESUMEN], [HIPÓTESIS], [PUNTOS CIEGOS], [SUGERENCIAS].
"""

# 3. FUNCIÓN DE OÍDO (Reutilizamos la que ya arreglamos)
def transcribir_sesion(ruta_archivo):
    print("⚡ Iniciando transcripción de alta velocidad (Incredibly Fast Whisper)...")
    try:
        input_audio = open(ruta_archivo, "rb")
        
        # 1. BUSCAMOS EL MODELO MÁS RÁPIDO DEL MERCADO
        # "vaibhavs10/incredibly-fast-whisper" está optimizado para archivos largos.
        model = replicate.models.get("vaibhavs10/incredibly-fast-whisper")
        latest_version = model.versions.list()[0]
        
        print(f"   (Conectando a versión: {latest_version.id[:10]}...)")

        # 2. EJECUTAMOS CON PARÁMETROS DE VELOCIDAD
        output = replicate.run(
            f"vaibhavs10/incredibly-fast-whisper:{latest_version.id}",
            input={
                "audio": input_audio,
                "task": "transcribe",
                "language": "spanish",
                "batch_size": 24,
                # CAMBIO AQUÍ: El modelo nos pidió "chunk" o "word".
                # Usamos "chunk" para que procese por bloques.
                "timestamp": "chunk" 
            }
        )
        
        # 3. LIMPIEZA DE DATOS (Este modelo devuelve las cosas un poco diferente)
        texto_detectado = ""
        
        # A veces devuelve un string directo, a veces un diccionario
        if isinstance(output, str):
            texto_detectado = output
        elif isinstance(output, dict) and "text" in output:
             texto_detectado = output["text"]
        elif isinstance(output, list):
            # A veces devuelve una lista de segmentos, los unimos
            texto_detectado = " ".join([seg.get("text", "") for seg in output])
            
        print(f"✅ Transcripción lista. Se procesaron {len(texto_detectado)} caracteres.")
        return texto_detectado

    except Exception as e:
        print(f"❌ Error en la transcripción: {e}")
        return ""

# 4. FUNCIÓN DE CEREBRO (SUPERVISOR)
def generar_reporte_clinico(texto_sesion):
    print("🧠 Generando reporte clínico (DeepSeek)...")
    
    try:
        response = client_deepseek.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_SUPERVISOR},
                {"role": "user", "content": f"Aquí tienes la transcripción de la sesión:\n\n{texto_sesion}"}
            ],
            temperature=0.5 # Bajamos la temperatura para que sea más analítico y menos "creativo"
        )
        
        reporte = response.choices[0].message.content
        return reporte

    except Exception as e:
        return f"Error en el análisis: {e}"

# --- EJECUCIÓN ---
if __name__ == "__main__":
    print("--- ASISTENTE DE TERAPIA: ANÁLISIS DE SESIÓN ---")
    
    # TIP DE MENTOR:
    # Para probar esto bien, graba un audio donde TÚ simules ser el paciente.
    # Ejemplo: "Hola, vengo porque tengo una dermatitis en los brazos... 
    # empezó cuando mi pareja se fue de viaje..."
    
    archivo_sesion = "prueba.mp3"
    
    if os.path.exists(archivo_sesion):
        # Paso 1: Transcribir
        transcripcion = transcribir_sesion(archivo_sesion)
        
        if transcripcion:
            print("\n--- TEXTO DE LA SESIÓN ---")
            print(transcripcion)
            
            # Paso 2: Analizar
            reporte = generar_reporte_clinico(transcripcion)
            
            print("\n" + "="*40)
            print("REPORTE CONFIDENCIAL PARA EL TERAPEUTA")
            print("="*40 + "\n")
            print(reporte)
    else:
        print("⚠️ No encontré 'prueba.mp3'. Graba una simulación de paciente para analizar.")