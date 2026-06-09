from fastapi import APIRouter, Depends, HTTPException, Query
from prisma import Prisma
from typing import List, Optional
from app.database import get_db
from app.security import get_current_user, require_roles
from app.schemas.schemas import FincaCreate, FincaOut, FincaUpdate

router = APIRouter()


@router.get("/", response_model=List[FincaOut], summary="Listar fincas")
def listar_fincas(
    provincia: Optional[str] = Query(None),
    canton: Optional[str] = Query(None),
    db: Prisma = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    where: dict = {}
    if provincia:
        where["provincia"] = provincia
    if canton:
        where["canton"] = canton
    return db.finca.find_many(where=where)


@router.post("/", response_model=FincaOut, status_code=201, summary="Crear nueva finca")
def crear_finca(
    data: FincaCreate,
    db: Prisma = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return db.finca.create(data=data.model_dump())


@router.get("/{finca_id}", response_model=FincaOut, summary="Obtener finca por ID")
def obtener_finca(
    finca_id: str,
    db: Prisma = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    finca = db.finca.find_first(where={"id": finca_id})
    if not finca:
        raise HTTPException(status_code=404, detail="Finca no encontrada")
    return finca


@router.patch("/{finca_id}", response_model=FincaOut, summary="Actualizar datos de la finca")
def actualizar_finca(
    finca_id: str,
    data: FincaUpdate,
    db: Prisma = Depends(get_db),
    current_user: dict = Depends(require_roles("SUPER_ADMIN", "TENANT_ADMIN", "TECNICO_CAMPO")),
):
    if not db.finca.find_first(where={"id": finca_id}):
        raise HTTPException(status_code=404, detail="Finca no encontrada")
    return db.finca.update(where={"id": finca_id}, data=data.model_dump(exclude_unset=True))


@router.delete("/{finca_id}", summary="Eliminar finca")
def eliminar_finca(
    finca_id: str,
    db: Prisma = Depends(get_db),
    current_user: dict = Depends(require_roles("SUPER_ADMIN", "TENANT_ADMIN")),
):
    if not db.finca.find_first(where={"id": finca_id}):
        raise HTTPException(status_code=404, detail="Finca no encontrada")
    db.finca.delete(where={"id": finca_id})
    return {"message": "Finca eliminada correctamente"}
