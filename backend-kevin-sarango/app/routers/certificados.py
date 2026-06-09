from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID, uuid4
from datetime import datetime
from app.database import get_db
from app.models.models import CertificadoDDS, Expediente, AuditoriaGEE, HistorialTrazabilidad, EstadoCertificadoEnum
from app.schemas.schemas import CertificadoCreate, CertificadoOut

router = APIRouter()


@router.get("/", response_model=List[CertificadoOut], summary="Listar todos los certificados DDS")
def listar_certificados(db: Session = Depends(get_db)):
    return db.query(CertificadoDDS).all()


@router.post("/", response_model=CertificadoOut, status_code=201, summary="Generar certificado DDS")
def generar_certificado(data: CertificadoCreate, db: Session = Depends(get_db)):
    exp = db.query(Expediente).filter(Expediente.id == data.expediente_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Expediente no encontrado")

    # Verificar auditoría GEE aprobada
    auditoria_aprobada = db.query(AuditoriaGEE).filter(
        AuditoriaGEE.expediente_id == data.expediente_id,
        AuditoriaGEE.resultado == "APROBADO"
    ).first()
    if not auditoria_aprobada:
        raise HTTPException(
            status_code=400,
            detail="El expediente requiere una auditoría GEE con resultado APROBADO para emitir el certificado"
        )

    # Generar código único con formato DDS-{año}-{uuid corto}
    codigo = f"DDS-{datetime.utcnow().year}-{uuid4().hex[:8].upper()}"

    certificado = CertificadoDDS(
        **data.model_dump(),
        codigo_certificado=codigo
    )
    db.add(certificado)
    db.flush()

    # Registrar en historial de trazabilidad
    historial = HistorialTrazabilidad(
        expediente_id=data.expediente_id,
        accion="Certificado DDS generado",
        descripcion=f"Código: {codigo}. Generado por: {data.generado_por or 'sistema'}.",
        usuario=data.generado_por or "sistema"
    )
    db.add(historial)
    db.commit()
    db.refresh(certificado)
    return certificado


@router.get("/expediente/{expediente_id}", response_model=List[CertificadoOut], summary="Obtener certificados de un expediente")
def certificados_por_expediente(expediente_id: UUID, db: Session = Depends(get_db)):
    exp = db.query(Expediente).filter(Expediente.id == expediente_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Expediente no encontrado")
    return db.query(CertificadoDDS).filter(CertificadoDDS.expediente_id == expediente_id).all()


@router.get("/{certificado_id}", response_model=CertificadoOut, summary="Obtener certificado por ID")
def obtener_certificado(certificado_id: UUID, db: Session = Depends(get_db)):
    certificado = db.query(CertificadoDDS).filter(CertificadoDDS.id == certificado_id).first()
    if not certificado:
        raise HTTPException(status_code=404, detail="Certificado no encontrado")
    return certificado


@router.patch("/{certificado_id}/revocar", response_model=CertificadoOut, summary="Revocar certificado DDS")
def revocar_certificado(certificado_id: UUID, db: Session = Depends(get_db)):
    certificado = db.query(CertificadoDDS).filter(CertificadoDDS.id == certificado_id).first()
    if not certificado:
        raise HTTPException(status_code=404, detail="Certificado no encontrado")

    certificado.estado = EstadoCertificadoEnum.revocado
    db.commit()
    db.refresh(certificado)
    return certificado
