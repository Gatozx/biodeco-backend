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

## --- BLOQUE 1: REINICIO DE TABLAS ---
models.Base.metadata.drop_all(bind=engine)  # Esta línea borra la tabla vieja
models.Base.metadata.create_all(bind=engine) # Esta crea la nueva
# --------------------------------------------------------


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
        reporte_json = generar_reporte_clinico(texto_transcrito)


# === PARCHE DE SEGURIDAD: Convertir String a Diccionario ===
        if isinstance(reporte_json, str):
            print("⚠️ Alerta: La IA devolvió texto crudo. Convirtiendo a JSON...")
            try:
                # Limpiamos posibles etiquetas de código que pone la IA (```json ... ```)
                json_limpio = reporte_json.replace("```json", "").replace("```", "").strip()
                reporte_json = json.loads(json_limpio)
            except Exception as e_json:
                print(f"❌ Error fatal convirtiendo JSON: {e_json}")
                # Si falla todo, creamos un diccionario de emergencia para que no explote la DB
                reporte_json = {
                    "motivo_consulta": "Error de formato IA",
                    "diagnostico_tecnico": "La IA no devolvió un JSON válido.",
                    "resumen_sesion": str(reporte_json) # Guardamos lo que haya mandado
                }
    # ==========================================
        # === INICIO DEL CÓDIGO NUEVO DE BASE DE DATOS ===
        # ==========================================
        try:
            # 1. Convertimos las listas a TEXTO para poder guardarlas
            recomendaciones_str = json.dumps(reporte_json.get("recomendaciones", []))
            oportunidades_str = json.dumps(reporte_json.get("oportunidades_omitidas", [])) # <--- NUEVO

            # 2. Rellenamos la ficha médica
            nuevo_reporte = models.Reporte(
                motivo_consulta=reporte_json.get("motivo_consulta"),
                emocion_base=reporte_json.get("emocion_base"),
                organo_afectado=reporte_json.get("organo_afectado"),
                conflicto_biologico=reporte_json.get("conflicto_biologico"),
                diagnostico_tecnico=reporte_json.get("diagnostico_tecnico"),
                
                # AQUI ESTAN LOS CAMPOS NUEVOS:
                hallazgos_clinicos=reporte_json.get("hallazgos_clinicos", "Sin hallazgos."),
                oportunidades_omitidas=oportunidades_str,
                
                recomendaciones=recomendaciones_str,
                resumen_sesion=reporte_json.get("resumen_sesion")
            )

            db.add(nuevo_reporte)
            db.commit()
            db.refresh(nuevo_reporte)
            print(f"✅ Reporte guardado con ID: {nuevo_reporte.id}")
            
            # Agregamos el ID a la respuesta
            reporte_json["id"] = nuevo_reporte.id
            
        except Exception as e_db:
            print(f"⚠️ Error guardando en DB: {e_db}")

        # ==========================================
        # === FIN DEL CÓDIGO NUEVO ===
        # ==========================================
    
        # 4. Devolver respuesta
        return {
            "estado": "exito",
            "nombre_archivo": file.filename,
            "transcripcion": texto_transcrito,
            "analisis_ia": reporte_json  # <--- ✅ AHORA SÍ (Dice 'reporte_json')
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

 # --- BLOQUE 3: LEER HISTORIAL ---
@app.get("/historial")
def leer_historial(db: Session = Depends(get_db)):
    reportes = db.query(models.Reporte).order_by(models.Reporte.created_at.desc()).all()
    
    lista_resultado = []
    for rep in reportes:
        # Convertimos el objeto de DB a Diccionario básico
        rep_dict = {
            "id": rep.id,
            "fecha": rep.created_at,
            "motivo_consulta": rep.motivo_consulta,
            "emocion_base": rep.emocion_base,
            "organo_afectado": rep.organo_afectado,
            "conflicto_biologico": rep.conflicto_biologico,
            "diagnostico_tecnico": rep.diagnostico_tecnico,
            "hallazgos_clinicos": rep.hallazgos_clinicos, # <--- NUEVO
            "resumen_sesion": rep.resumen_sesion,
            "recomendaciones": [],
            "oportunidades_omitidas": [] # <--- NUEVO
        }
        
        # Convertir texto JSON a Listas reales
        try:
            if rep.recomendaciones:
                rep_dict["recomendaciones"] = json.loads(rep.recomendaciones)
        except:
            pass

        try: # <--- NUEVA LÓGICA PARA OPORTUNIDADES
            if rep.oportunidades_omitidas:
                rep_dict["oportunidades_omitidas"] = json.loads(rep.oportunidades_omitidas)
        except:
            pass
            
        lista_resultado.append(rep_dict)

    return lista_resultado