from fastapi import APIRouter, Depends, HTTPException, Query
from prisma import Prisma
from typing import List, Optional
from uuid import uuid4
from app.database import get_db
from app.security import get_current_user, require_roles
from app.schemas.schemas import (
    ExpedienteCreate, ExpedienteOut, ExpedienteUpdate,
    HistorialCreate, HistorialOut,
)

router = APIRouter()

_INCLUDE = {"datos_agroambientales": {"include": {"variables": True}}, "historial": True}


def generar_eudr_id() -> str:
    return f"uuidv4-{uuid4().hex[:8].upper()}-{uuid4().hex[:5].upper()}"


# ─── EXPEDIENTES ─────────────────────────────────────────────

@router.get("/", response_model=List[ExpedienteOut], summary="Listar todos los expedientes")
def listar_expedientes(
    estado: Optional[str] = Query(None),
    organizacion: Optional[str] = Query(None),
    db: Prisma = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    where: dict = {}
    if estado:
        where["estado"] = estado
    if organizacion:
        where["organizacion_inquilino"] = organizacion
    return db.expediente.find_many(where=where, include=_INCLUDE)


@router.post("/", response_model=ExpedienteOut, status_code=201, summary="Crear nuevo expediente")
def crear_expediente(
    data: ExpedienteCreate,
    db: Prisma = Depends(get_db),
    current_user: dict = Depends(require_roles("SUPER_ADMIN", "TENANT_ADMIN", "TECNICO_CAMPO")),
):
    dato_nested = data.datos_agroambientales
    create_data = data.model_dump(exclude={"datos_agroambientales"})
    create_data["eudr_id"] = generar_eudr_id()
    create_data["historial"] = {
        "create": [{
            "accion": "Expediente creado",
            "descripcion": f"Registro inicial del productor {data.nombre_completo} - Finca {data.nombre_finca}",
            "usuario": current_user.get("sub", "sistema"),
        }]
    }
    variables_pendientes = []
    if dato_nested:
        dato_data = dato_nested.model_dump(exclude={"variables"})
        create_data["datos_agroambientales"] = {"create": [dato_data]}
        variables_pendientes = dato_nested.variables or []

    expediente = db.expediente.create(data=create_data, include=_INCLUDE)

    if variables_pendientes and expediente.datos_agroambientales:
        dato_id = expediente.datos_agroambientales[0].id
        for v in variables_pendientes:
            db.variabledinamica.create(data={"dato_id": dato_id, **v.model_dump()})
        return db.expediente.find_first(
            where={"id": expediente.id},
            include={"datos_agroambientales": {"include": {"variables": True}}, "historial": True},
        )

    return expediente


@router.get("/eudr/{eudr_id}", response_model=ExpedienteOut, summary="Buscar por EUDR ID")
def buscar_por_eudr(
    eudr_id: str,
    db: Prisma = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    exp = db.expediente.find_first(where={"eudr_id": eudr_id}, include=_INCLUDE)
    if not exp:
        raise HTTPException(status_code=404, detail="Expediente no encontrado")
    return exp


@router.get("/{expediente_id}", response_model=ExpedienteOut, summary="Obtener expediente por ID")
def obtener_expediente(
    expediente_id: str,
    db: Prisma = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    exp = db.expediente.find_first(where={"id": expediente_id}, include=_INCLUDE)
    if not exp:
        raise HTTPException(status_code=404, detail="Expediente no encontrado")
    return exp


@router.patch("/{expediente_id}", response_model=ExpedienteOut, summary="Actualizar expediente")
def actualizar_expediente(
    expediente_id: str,
    data: ExpedienteUpdate,
    db: Prisma = Depends(get_db),
    current_user: dict = Depends(require_roles("SUPER_ADMIN", "TENANT_ADMIN", "TECNICO_CAMPO")),
):
    if not db.expediente.find_first(where={"id": expediente_id}):
        raise HTTPException(status_code=404, detail="Expediente no encontrado")
    cambios = data.model_dump(exclude_unset=True)
    db.expediente.update(where={"id": expediente_id}, data=cambios)
    db.historial.create(data={
        "expediente_id": expediente_id,
        "accion": "Expediente actualizado",
        "descripcion": f"Campos modificados: {', '.join(cambios.keys())}",
        "usuario": current_user.get("sub", "sistema"),
    })
    return db.expediente.find_first(where={"id": expediente_id}, include=_INCLUDE)


@router.delete("/{expediente_id}", summary="Eliminar expediente")
def eliminar_expediente(
    expediente_id: str,
    db: Prisma = Depends(get_db),
    current_user: dict = Depends(require_roles("SUPER_ADMIN", "TENANT_ADMIN")),
):
    if not db.expediente.find_first(where={"id": expediente_id}):
        raise HTTPException(status_code=404, detail="Expediente no encontrado")
    db.expediente.delete(where={"id": expediente_id})
    return {"message": "Expediente eliminado"}


# ─── TRAZABILIDAD ────────────────────────────────────────────

@router.get("/{expediente_id}/historial", response_model=List[HistorialOut], summary="Ver historial de trazabilidad")
def ver_historial(
    expediente_id: str,
    db: Prisma = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not db.expediente.find_first(where={"id": expediente_id}):
        raise HTTPException(status_code=404, detail="Expediente no encontrado")
    return db.historial.find_many(where={"expediente_id": expediente_id})


@router.post("/{expediente_id}/historial", response_model=HistorialOut, status_code=201, summary="Agregar evento al historial")
def agregar_historial(
    expediente_id: str,
    data: HistorialCreate,
    db: Prisma = Depends(get_db),
    current_user: dict = Depends(require_roles("SUPER_ADMIN", "TENANT_ADMIN", "TECNICO_CAMPO")),
):
    if not db.expediente.find_first(where={"id": expediente_id}):
        raise HTTPException(status_code=404, detail="Expediente no encontrado")
    payload = data.model_dump()
    payload.setdefault("usuario", current_user.get("sub", "sistema"))
    return db.historial.create(data={"expediente_id": expediente_id, **payload})
