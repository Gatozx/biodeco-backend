import os
import shutil
from fastapi import FastAPI, UploadFile, File
from servicios_ia import transcribir_sesion, generar_reporte_clinico
from fastapi.middleware.cors import CORSMiddleware # <--- IMPORTAR ESTO
from sqlalchemy.orm import Session
from fastapi import Depends
import models
from database import engine, get_db
import json # Lo necesitaremos para convertir la lista de recomendaciones a string

# Esto crea las tablas en la base de datos automáticamente al iniciar
models.Base.metadata.create_all(bind=engine)

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

@app.post("/analyze_audio")
async def analyze_audio(file: UploadFile = File(...), db: Session = Depends(get_db)): # <--- OJO: Agregamos db aquí
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

    # ==========================================
        # === INICIO DEL CÓDIGO NUEVO DE BASE DE DATOS ===
        # ==========================================
        try:
            # Convertimos la lista de recomendaciones a texto para guardarla
            recomendaciones_str = json.dumps(reporte.get("recomendaciones", []))

            nuevo_reporte = models.Reporte(
                motivo_consulta=reporte.get("motivo_consulta"),
                emocion_base=reporte.get("emocion_base"),
                organo_afectado=reporte.get("organo_afectado"),
                conflicto_biologico=reporte.get("conflicto_biologico"),
                diagnostico_tecnico=reporte.get("diagnostico_tecnico"),
                recomendaciones=recomendaciones_str,
                resumen_sesion=reporte.get("resumen_sesion")
            )

            db.add(nuevo_reporte)
            db.commit()
            db.refresh(nuevo_reporte)
            print(f"✅ Reporte guardado en DB con ID: {nuevo_reporte.id}")
            
            # Opcional: Agregamos el ID al reporte que devolvemos al frontend
            reporte["id_db"] = nuevo_reporte.id
            
        except Exception as e_db:
            print(f"⚠️ Error guardando en Base de Datos (pero el análisis sí funcionó): {e_db}")
        # ==========================================
        # === FIN DEL CÓDIGO NUEVO ===
        # ==========================================
    
        # 4. Devolver respuesta
        return {
            "estado": "exito",
            "nombre_archivo": file.filename,
            "transcripcion": texto_transcrito,
            "analisis_ia": reporte
        }
        
    except Exception as e:
        print(f"❌ ERROR CRÍTICO EN EL SERVIDOR: {str(e)}") # Esto saldrá en la terminal negra
        return {
            "estado": "error",
            "nombre_archivo": file.filename,
            "transcripcion": "No se pudo transcribir debido a un error.",
            # AQUÍ ESTÁ EL TRUCO: Devolvemos siempre 'analisis_ia', aunque sea con el error
            "analisis_ia": f"⚠️ Ocurrió un error procesando tu solicitud:\n\n{str(e)}\n\nPor favor revisa la terminal del backend para más detalles."
        }
        
    finally:
        # 5. Limpieza
        if os.path.exists(ruta_temporal):
            os.remove(ruta_temporal)
            print("🧹 Archivo temporal eliminado.")

 # --- ENDPOINT NUEVO PARA LEER HISTORIAL ---           
@app.get("/historial")
def leer_historial(db: Session = Depends(get_db)):
    # Obtiene todos los reportes, ordenados del más reciente al más antiguo
    reportes = db.query(models.Reporte).order_by(models.Reporte.created_at.desc()).all()
    
    # Necesitamos convertir 'recomendaciones' de string a lista de nuevo para que el frontend no sufra
    lista_resultado = []
    for rep in reportes:
        rep_dict = rep.__dict__
        # Limpieza de SQLAlchemy
        if "_sa_instance_state" in rep_dict:
            del rep_dict["_sa_instance_state"]
            
        # Parsear el string JSON de vuelta a lista
        try:
            if rep.recomendaciones:
                rep_dict["recomendaciones"] = json.loads(rep.recomendaciones)
            else:
                rep_dict["recomendaciones"] = []
        except:
            rep_dict["recomendaciones"] = []
            
        lista_resultado.append(rep_dict)

    return lista_resultado