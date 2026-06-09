from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.database import get_db
from app.models.models import AuditoriaGEE, Expediente, HistorialTrazabilidad, EstadoExpedienteEnum
from app.schemas.schemas import AuditoriaCreate, AuditoriaOut

router = APIRouter()


@router.get("/", response_model=List[AuditoriaOut], summary="Listar todas las auditorías GEE")
def listar_auditorias(db: Session = Depends(get_db)):
    return db.query(AuditoriaGEE).all()


@router.post("/", response_model=AuditoriaOut, status_code=201, summary="Registrar resultado de auditoría GEE")
def crear_auditoria(data: AuditoriaCreate, db: Session = Depends(get_db)):
    exp = db.query(Expediente).filter(Expediente.id == data.expediente_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Expediente no encontrado")

    auditoria = AuditoriaGEE(**data.model_dump())
    db.add(auditoria)
    db.flush()

    # Actualizar estado del expediente según resultado
    exp.estado = (
        EstadoExpedienteEnum.aprobado
        if data.resultado == "APROBADO"
        else EstadoExpedienteEnum.rechazado
    )

    # Registrar en historial de trazabilidad
    historial = HistorialTrazabilidad(
        expediente_id=data.expediente_id,
        accion="Auditoría GEE ejecutada",
        descripcion=f"Resultado: {data.resultado}. Deforestación detectada: {data.deforestacion_detectada}.",
        usuario=data.ejecutado_por or "sistema"
    )
    db.add(historial)
    db.commit()
    db.refresh(auditoria)
    return auditoria


@router.get("/expediente/{expediente_id}", response_model=List[AuditoriaOut], summary="Obtener auditorías de un expediente")
def auditorias_por_expediente(expediente_id: UUID, db: Session = Depends(get_db)):
    exp = db.query(Expediente).filter(Expediente.id == expediente_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Expediente no encontrado")
    return db.query(AuditoriaGEE).filter(AuditoriaGEE.expediente_id == expediente_id).all()


@router.get("/{auditoria_id}", response_model=AuditoriaOut, summary="Obtener auditoría por ID")
def obtener_auditoria(auditoria_id: UUID, db: Session = Depends(get_db)):
    auditoria = db.query(AuditoriaGEE).filter(AuditoriaGEE.id == auditoria_id).first()
    if not auditoria:
        raise HTTPException(status_code=404, detail="Auditoría no encontrada")
    return auditoria
