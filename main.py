import os
import shutil
from fastapi import FastAPI, UploadFile, File
from servicios_ia import transcribir_sesion, generar_reporte_clinico
from fastapi.middleware.cors import CORSMiddleware # <--- IMPORTAR ESTO

# Creamos la APP (El servidor)
app = FastAPI(
    title="Biodeco AI API",
    description="API para analizar sesiones de terapia con IA",
    version="1.0"
)

# AGREGAR ESTO: Permisos para que la App hable con el Servidor
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # "*" significa "permitir a todo el mundo" (para pruebas)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Creamos una carpeta temporal para guardar los audios que suban
os.makedirs("temp_uploads", exist_ok=True)

@app.get("/")
def home():
    return {"mensaje": "El servidor de Biodecodificación está ACTIVO 🟢"}

@app.post("/analizar-sesion/")
async def analizar_audio(file: UploadFile = File(...)):
    """
    Endpoint principal:
    1. Recibe el archivo de audio de la App.
    2. Lo transcribe con Whisper (Replicate).
    3. Lo analiza con DeepSeek.
    4. Devuelve el reporte JSON.
    """
    print(f"📥 Recibiendo archivo: {file.filename}")
    
    # 1. Guardar el archivo temporalmente en el servidor
    ruta_temporal = f"temp_uploads/{file.filename}"
    
    with open(ruta_temporal, "wb") as buffer:
        # Copiamos el archivo que llega por internet a tu disco duro
        shutil.copyfileobj(file.file, buffer)
        
    try:
        # 2. Transcribir (Usando tu función importada)
        texto_transcrito = transcribir_sesion(ruta_temporal)
        
        if not texto_transcrito:
            return {"error": "No se pudo transcribir el audio."}

        # 3. Analizar (Usando tu función importada)
        reporte = generar_reporte_clinico(texto_transcrito)
        
        # 4. Devolver respuesta
        return {
            "estado": "exito",
            "nombre_archivo": file.filename,
            "transcripcion": texto_transcrito,
            "analisis_ia": reporte
        }
        
    except Exception as e:
        return {"error": str(e)}
        
    finally:
        # 5. Limpieza: Borrar el archivo de audio para no llenar el disco
        if os.path.exists(ruta_temporal):
            os.remove(ruta_temporal)
            print("🧹 Archivo temporal eliminado.")