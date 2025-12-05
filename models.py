from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from database import Base

class Reporte(Base):
    __tablename__ = "reportes"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Campos Clásicos
    motivo_consulta = Column(String)
    emocion_base = Column(String)
    organo_afectado = Column(String)
    conflicto_biologico = Column(String)
    diagnostico_tecnico = Column(String)
    
    # --- LOS NUEVOS CEREBROS DEL SISTEMA ---
    hallazgos_clinicos = Column(Text)       # <--- ¡NUEVO!
    oportunidades_omitidas = Column(Text)   # <--- ¡NUEVO!
    # ---------------------------------------

    recomendaciones = Column(Text)
    resumen_sesion = Column(Text)