from fastapi import APIRouter, Depends, HTTPException
from prisma import Prisma
from typing import List
from app.database import get_db
from app.security import get_current_user, require_roles
from app.schemas.schemas import AuditoriaCreate, AuditoriaOut

router = APIRouter()


@router.get("/", response_model=List[AuditoriaOut], summary="Listar todas las auditorías GEE")
def listar_auditorias(
    db: Prisma = Depends(get_db),
    current_user: dict = Depends(require_roles("SUPER_ADMIN", "TENANT_ADMIN", "AUDITOR_INTERNO")),
):
    return db.auditoria.find_many()


@router.post("/", response_model=AuditoriaOut, status_code=201, summary="Registrar resultado de auditoría GEE")
def crear_auditoria(
    data: AuditoriaCreate,
    db: Prisma = Depends(get_db),
    current_user: dict = Depends(require_roles("SUPER_ADMIN", "TENANT_ADMIN", "AUDITOR_INTERNO")),
):
    if not db.expediente.find_first(where={"id": data.expediente_id}):
        raise HTTPException(status_code=404, detail="Expediente no encontrado")

    # Usar sub del token si no se especificó ejecutado_por
    create_data = data.model_dump()
    if not create_data.get("ejecutado_por"):
        create_data["ejecutado_por"] = current_user.get("sub")

    auditoria = db.auditoria.create(data=create_data)

    nuevo_estado = "APROBADO" if data.resultado == "APROBADO" else "RECHAZADO"
    db.expediente.update(where={"id": data.expediente_id}, data={"estado": nuevo_estado})

    db.historial.create(data={
        "expediente_id": data.expediente_id,
        "accion": "Auditoría GEE ejecutada",
        "descripcion": f"Resultado: {data.resultado}. Deforestación detectada: {data.deforestacion_detectada}.",
        "usuario": current_user.get("sub", "sistema"),
    })
    return auditoria


@router.get("/expediente/{expediente_id}", response_model=List[AuditoriaOut], summary="Obtener auditorías de un expediente")
def auditorias_por_expediente(
    expediente_id: str,
    db: Prisma = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not db.expediente.find_first(where={"id": expediente_id}):
        raise HTTPException(status_code=404, detail="Expediente no encontrado")
    return db.auditoria.find_many(where={"expediente_id": expediente_id})


@router.get("/{auditoria_id}", response_model=AuditoriaOut, summary="Obtener auditoría por ID")
def obtener_auditoria(
    auditoria_id: str,
    db: Prisma = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    auditoria = db.auditoria.find_first(where={"id": auditoria_id})
    if not auditoria:
        raise HTTPException(status_code=404, detail="Auditoría no encontrada")
    return auditoria
