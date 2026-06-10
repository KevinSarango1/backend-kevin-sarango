from fastapi import APIRouter, Depends, HTTPException
from prisma import Prisma
from typing import List
from app.database import get_db
from app.security import get_current_user, require_roles
from app.schemas.schemas import RolCreate, RolOut

router = APIRouter()


@router.get("/", response_model=List[RolOut], summary="Listar todos los roles")
def listar_roles(
    db: Prisma = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    return db.rol.find_many()


@router.post("/", response_model=RolOut, status_code=201, summary="Crear nuevo rol")
def crear_rol(
    data: RolCreate,
    db: Prisma = Depends(get_db),
    current_user: dict = Depends(require_roles("SUPER_ADMIN")),
):
    if db.rol.find_first(where={"nombre": data.nombre}):
        raise HTTPException(status_code=400, detail="El rol ya existe")
    return db.rol.create(data=data.model_dump())


@router.get("/{rol_id}", response_model=RolOut, summary="Obtener rol por ID")
def obtener_rol(
    rol_id: str,
    db: Prisma = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    rol = db.rol.find_first(where={"id": rol_id})
    if not rol:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    return rol


@router.delete("/{rol_id}", summary="Eliminar rol")
def eliminar_rol(
    rol_id: str,
    db: Prisma = Depends(get_db),
    current_user: dict = Depends(require_roles("SUPER_ADMIN")),
):
    if not db.rol.find_first(where={"id": rol_id}):
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    db.rol.delete(where={"id": rol_id})
    return {"message": "Rol eliminado correctamente"}
