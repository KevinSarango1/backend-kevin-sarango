from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.database import get_db
from app.models.models import Rol
from app.schemas.schemas import RolCreate, RolOut

router = APIRouter()


@router.get("/", response_model=List[RolOut], summary="Listar todos los roles")
def listar_roles(db: Session = Depends(get_db)):
    return db.query(Rol).all()


@router.post("/", response_model=RolOut, status_code=201, summary="Crear nuevo rol")
def crear_rol(data: RolCreate, db: Session = Depends(get_db)):
    existente = db.query(Rol).filter(Rol.nombre == data.nombre).first()
    if existente:
        raise HTTPException(status_code=400, detail="El rol ya existe")

    rol = Rol(**data.model_dump())
    db.add(rol)
    db.commit()
    db.refresh(rol)
    return rol


@router.get("/{rol_id}", response_model=RolOut, summary="Obtener rol por ID")
def obtener_rol(rol_id: UUID, db: Session = Depends(get_db)):
    rol = db.query(Rol).filter(Rol.id == rol_id).first()
    if not rol:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    return rol


@router.delete("/{rol_id}", summary="Eliminar rol")
def eliminar_rol(rol_id: UUID, db: Session = Depends(get_db)):
    rol = db.query(Rol).filter(Rol.id == rol_id).first()
    if not rol:
        raise HTTPException(status_code=404, detail="Rol no encontrado")
    db.delete(rol)
    db.commit()
    return {"message": "Rol eliminado correctamente"}
