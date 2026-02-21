# main.py COMPLETO
import os
import shutil
import json
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field # <--- AGREGA ESTO EN TUS IMPORTS ARRIBA
# --- TUS MÓDULOS PROPIOS ---
# Asegúrate de que estos archivos existan y tengan las funciones
from database import engine, get_db
import models
from servicios_ia import transcribir_sesion, generar_reporte_clinico, generar_plan_asistente_mentor

# ==========================================
# 1. CONFIGURACIÓN DE BASE DE DATOS
# ==========================================
# ⚠️ IMPORTANTE: Dejamos 'drop_all' activo una vez para reiniciar la tabla
# con las nuevas columnas. En el futuro, comenta esa línea.
models.Base.metadata.drop_all(bind=engine) 
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Configuración de CORS (Para que Flutter pueda hablar con Python)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# 2. ENDPOINTS (LAS FUNCIONES)
# ==========================================

@app.post("/analyze_audio")
async def analyze_audio(file: UploadFile = File(...), db: Session = Depends(get_db)):
    print(f"📥 Recibiendo archivo: {file.filename}")
    
    # A. Guardar archivo temporal
    ruta_temporal = f"temp_{file.filename}"
    with open(ruta_temporal, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        # B. Transcribir (Whisper)
        texto_transcrito = transcribir_sesion(ruta_temporal)
        
        if not texto_transcrito:
            return {"error": "No se pudo transcribir el audio."}

        # C. Analizar (DeepSeek)
        # OJO: Aquí obtenemos la respuesta cruda
        reporte_json = generar_reporte_clinico(texto_transcrito)

        # === PARCHE DE SEGURIDAD: Convertir Texto a JSON si es necesario ===
        if isinstance(reporte_json, str):
            print("⚠️ Alerta: La IA devolvió texto. Convirtiendo a JSON...")
            try:
                # Limpieza de etiquetas markdown ```json
                json_limpio = reporte_json.replace("```json", "").replace("```", "").strip()
                reporte_json = json.loads(json_limpio)
            except Exception as e_json:
                print(f"❌ Error fatal convirtiendo JSON: {e_json}")
                # Diccionario de emergencia
                reporte_json = {
                    "motivo_consulta": "Error de formato IA",
                    "diagnostico_tecnico": "La IA no devolvió un JSON válido.",
                    "resumen_sesion": str(reporte_json),
                    "recomendaciones": [],
                    "oportunidades_omitidas": []
                }
        # ===================================================================

        # D. Guardar en Base de Datos
        try:
            # Serializar listas a String para SQL
            recomendaciones_str = json.dumps(reporte_json.get("recomendaciones", []))
            oportunidades_str = json.dumps(reporte_json.get("oportunidades_omitidas", []))

            nuevo_reporte = models.Reporte(
                motivo_consulta=reporte_json.get("motivo_consulta"),
                emocion_base=reporte_json.get("emocion_base"),
                organo_afectado=reporte_json.get("organo_afectado"),
                conflicto_biologico=reporte_json.get("conflicto_biologico"),
                diagnostico_tecnico=reporte_json.get("diagnostico_tecnico"),
                
                # Campos Nuevos
                hallazgos_clinicos=reporte_json.get("hallazgos_clinicos", "Sin hallazgos."),
                oportunidades_omitidas=oportunidades_str,
                
                recomendaciones=recomendaciones_str,
                resumen_sesion=reporte_json.get("resumen_sesion")
            )

            db.add(nuevo_reporte)
            db.commit()
            db.refresh(nuevo_reporte)
            print(f"✅ Reporte guardado con ID: {nuevo_reporte.id}")
            
            # Agregamos el ID al JSON de respuesta
            reporte_json["id"] = nuevo_reporte.id
            
        except Exception as e_db:
            print(f"⚠️ Error guardando en DB: {e_db}")
            # No detenemos el programa, el usuario recibirá su reporte igual

        # E. Devolver respuesta final al Frontend
        return {
            "estado": "exito",
            "nombre_archivo": file.filename,
            "transcripcion": texto_transcrito,
            "analisis_ia": reporte_json 
        }
        
    except Exception as e:
        print(f"❌ ERROR CRÍTICO: {str(e)}")
        return {"error": str(e)}
        
    finally:
        # F. Limpieza
        if os.path.exists(ruta_temporal):
            os.remove(ruta_temporal)


@app.get("/historial")
def leer_historial(db: Session = Depends(get_db)):
    print("📖 Consultando historial...")
    reportes = db.query(models.Reporte).order_by(models.Reporte.created_at.desc()).all()
    
    lista_resultado = []
    for rep in reportes:
        # Convertir Objeto DB a Diccionario
        rep_dict = {
            "id": rep.id,
            "fecha": str(rep.created_at),
            "motivo_consulta": rep.motivo_consulta,
            "emocion_base": rep.emocion_base,
            "organo_afectado": rep.organo_afectado,
            "conflicto_biologico": rep.conflicto_biologico,
            "diagnostico_tecnico": rep.diagnostico_tecnico,
            "hallazgos_clinicos": rep.hallazgos_clinicos,
            "resumen_sesion": rep.resumen_sesion,
            "recomendaciones": [],
            "oportunidades_omitidas": []
        }
        
        # Parsear Strings JSON a Listas
        try:
            if rep.recomendaciones:
                rep_dict["recomendaciones"] = json.loads(rep.recomendaciones)
        except:
            pass
            
        try:
            if rep.oportunidades_omitidas:
                rep_dict["oportunidades_omitidas"] = json.loads(rep.oportunidades_omitidas)
        except:
            pass
            
        lista_resultado.append(rep_dict)

    return lista_resultado

# ==========================================
# ENDPOINT PARA TEXTO (NUEVO)
# ==========================================

# Definimos el formato del paquete que nos enviará Flutter
class ConsultaTexto(BaseModel):
    texto: str

@app.post("/analyze_text")
async def analyze_text(consulta: ConsultaTexto, db: Session = Depends(get_db)):
    print(f"📝 Recibiendo consulta de texto (Longitud: {len(consulta.texto)} caracteres)")
    
    try:
        # A. Analizar Directamente (Sin Whisper)
        # Usamos el mismo cerebro que para el audio
        reporte_json = generar_reporte_clinico(consulta.texto)

        # B. Parche de Seguridad (Igual que en audio)
        if isinstance(reporte_json, str):
            try:
                json_limpio = reporte_json.replace("```json", "").replace("```", "").strip()
                reporte_json = json.loads(json_limpio)
            except:
                reporte_json = {
                    "motivo_consulta": "Texto directo",
                    "diagnostico_tecnico": "Error de formato JSON en texto.",
                    "resumen_sesion": str(reporte_json),
                    "recomendaciones": [],
                    "oportunidades_omitidas": []
                }

        # C. Guardar en Base de Datos (Igual que en audio)
        try:
            recomendaciones_str = json.dumps(reporte_json.get("recomendaciones", []))
            oportunidades_str = json.dumps(reporte_json.get("oportunidades_omitidas", []))

            nuevo_reporte = models.Reporte(
                motivo_consulta=reporte_json.get("motivo_consulta"),
                emocion_base=reporte_json.get("emocion_base"),
                organo_afectado=reporte_json.get("organo_afectado"),
                conflicto_biologico=reporte_json.get("conflicto_biologico"),
                diagnostico_tecnico=reporte_json.get("diagnostico_tecnico"),
                hallazgos_clinicos=reporte_json.get("hallazgos_clinicos", "Análisis de texto directo."),
                oportunidades_omitidas=oportunidades_str,
                recomendaciones=recomendaciones_str,
                resumen_sesion=reporte_json.get("resumen_sesion")
            )

            db.add(nuevo_reporte)
            db.commit()
            db.refresh(nuevo_reporte)
            
            # Agregamos ID para el frontend
            reporte_json["id"] = nuevo_reporte.id
            
        except Exception as e_db:
            print(f"⚠️ Error guardando texto en DB: {e_db}")

        # D. Devolver respuesta
        return {
            "estado": "exito",
            "tipo": "texto",
            "analisis_ia": reporte_json 
        }

    except Exception as e:
        print(f"❌ Error en endpoint de texto: {str(e)}")
        return {"error": str(e)}

class PlanAsistenteRequest(BaseModel):
    descripcion: str
    contexto: dict = Field(default_factory=dict)


@app.post("/design_assistant")
async def design_assistant(payload: PlanAsistenteRequest):
    print("🚀 Diseñando asistente-mentor para terapeuta...")

    datos_terapeuta = {
        "descripcion": payload.descripcion,
        "contexto": payload.contexto,
    }

    plan = generar_plan_asistente_mentor(datos_terapeuta)

    if not plan or plan.get("error"):
        raise HTTPException(status_code=502, detail=plan.get("error", "No se pudo generar el plan"))

    return {"estado": "exito", "plan": plan}
