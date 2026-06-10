from fastapi import APIRouter, Depends, HTTPException
from prisma import Prisma
from typing import List
from uuid import uuid4
from datetime import datetime
from app.database import get_db
from app.security import get_current_user, require_roles
from app.schemas.schemas import CertificadoCreate, CertificadoOut

router = APIRouter()


@router.get("/", response_model=List[CertificadoOut], summary="Listar todos los certificados DDS")
def listar_certificados(
    db: Prisma = Depends(get_db),
    current_user: dict = Depends(require_roles("SUPER_ADMIN", "TENANT_ADMIN", "AUDITOR_INTERNO")),
):
    return db.certificado.find_many()


@router.post("/", response_model=CertificadoOut, status_code=201, summary="Generar certificado DDS")
def generar_certificado(
    data: CertificadoCreate,
    db: Prisma = Depends(get_db),
    current_user: dict = Depends(require_roles("SUPER_ADMIN", "TENANT_ADMIN", "AUDITOR_INTERNO")),
):
    if not db.expediente.find_first(where={"id": data.expediente_id}):
        raise HTTPException(status_code=404, detail="Expediente no encontrado")

    if not db.auditoria.find_first(where={"expediente_id": data.expediente_id, "resultado": "APROBADO"}):
        raise HTTPException(
            status_code=400,
            detail="El expediente requiere una auditoría GEE con resultado APROBADO para emitir el certificado",
        )

    generado_por = data.generado_por if data.generado_por else current_user.get("sub", "sistema")
    codigo = f"DDS-{datetime.utcnow().year}-{uuid4().hex[:8].upper()}"

    certificado = db.certificado.create(data={
        **data.model_dump(),
        "codigo_certificado": codigo,
        "generado_por": generado_por,
    })
    db.historial.create(data={
        "expediente_id": data.expediente_id,
        "accion": "Certificado DDS generado",
        "descripcion": f"Código: {codigo}. Generado por: {generado_por}.",
        "usuario": current_user.get("sub", "sistema"),
    })
    return certificado


@router.get("/expediente/{expediente_id}", response_model=List[CertificadoOut], summary="Obtener certificados de un expediente")
def certificados_por_expediente(
    expediente_id: str,
    db: Prisma = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not db.expediente.find_first(where={"id": expediente_id}):
        raise HTTPException(status_code=404, detail="Expediente no encontrado")
    return db.certificado.find_many(where={"expediente_id": expediente_id})


@router.get("/{certificado_id}", response_model=CertificadoOut, summary="Obtener certificado por ID")
def obtener_certificado(
    certificado_id: str,
    db: Prisma = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    certificado = db.certificado.find_first(where={"id": certificado_id})
    if not certificado:
        raise HTTPException(status_code=404, detail="Certificado no encontrado")
    return certificado


@router.patch("/{certificado_id}/revocar", response_model=CertificadoOut, summary="Revocar certificado DDS")
def revocar_certificado(
    certificado_id: str,
    db: Prisma = Depends(get_db),
    current_user: dict = Depends(require_roles("SUPER_ADMIN", "TENANT_ADMIN")),
):
    if not db.certificado.find_first(where={"id": certificado_id}):
        raise HTTPException(status_code=404, detail="Certificado no encontrado")
    return db.certificado.update(where={"id": certificado_id}, data={"estado": "REVOCADO"})
