from fastapi import APIRouter, Depends, HTTPException
from prisma import Prisma
from typing import List
from passlib.context import CryptContext
from app.database import get_db
from app.security import require_roles
from app.schemas.schemas import UsuarioCreate, UsuarioOut, UsuarioUpdate

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Todos los endpoints de usuarios son exclusivos del ADMIN
_admin = Depends(require_roles("ADMIN"))


@router.get("/", response_model=List[UsuarioOut], summary="Listar todos los usuarios")
def listar_usuarios(db: Prisma = Depends(get_db), current_user: dict = _admin):
    return db.usuario.find_many()


@router.post("/", response_model=UsuarioOut, status_code=201, summary="Crear nuevo usuario")
def crear_usuario(data: UsuarioCreate, db: Prisma = Depends(get_db), current_user: dict = _admin):
    if db.usuario.find_first(where={"email": data.email}):
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    return db.usuario.create(data={
        "nombre": data.nombre,
        "email": data.email,
        "password_hash": pwd_context.hash(data.password),
        "rol_id": data.rol_id,
    })


@router.get("/{usuario_id}", response_model=UsuarioOut, summary="Obtener usuario por ID")
def obtener_usuario(usuario_id: str, db: Prisma = Depends(get_db), current_user: dict = _admin):
    usuario = db.usuario.find_first(where={"id": usuario_id})
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario


@router.patch("/{usuario_id}", response_model=UsuarioOut, summary="Actualizar rol o estado del usuario")
def actualizar_usuario(usuario_id: str, data: UsuarioUpdate, db: Prisma = Depends(get_db), current_user: dict = _admin):
    if not db.usuario.find_first(where={"id": usuario_id}):
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return db.usuario.update(where={"id": usuario_id}, data=data.model_dump(exclude_unset=True))


@router.delete("/{usuario_id}", summary="Desactivar usuario (no elimina el registro)")
def desactivar_usuario(usuario_id: str, db: Prisma = Depends(get_db), current_user: dict = _admin):
    if not db.usuario.find_first(where={"id": usuario_id}):
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    db.usuario.update(where={"id": usuario_id}, data={"activo": False})
    return {"message": "Usuario desactivado correctamente"}
