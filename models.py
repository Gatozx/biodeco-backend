from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from database import Base

class Reporte(Base):
    __tablename__ = "reportes"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Campos que vienen de tu JSON de DeepSeek
    motivo_consulta = Column(String)
    emocion_base = Column(String)
    organo_afectado = Column(String)
    conflicto_biologico = Column(String)
    diagnostico_tecnico = Column(String)
    
    # Como 'recomendaciones' es una lista, la guardaremos como texto largo 
    # (podríamos usar JSONB, pero texto es más simple por ahora)
    recomendaciones = Column(Text) 
    
    resumen_sesion = Column(Text)