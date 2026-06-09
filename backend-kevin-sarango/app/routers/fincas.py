from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from app.database import get_db
from app.models.models import Finca
from app.schemas.schemas import FincaCreate, FincaOut, FincaUpdate

router = APIRouter()


@router.get("/", response_model=List[FincaOut], summary="Listar fincas")
def listar_fincas(
    provincia: Optional[str] = Query(None, description="Filtrar por provincia"),
    canton: Optional[str] = Query(None, description="Filtrar por cantón"),
    db: Session = Depends(get_db)
):
    query = db.query(Finca)
    if provincia:
        query = query.filter(Finca.provincia == provincia)
    if canton:
        query = query.filter(Finca.canton == canton)
    return query.all()


@router.post("/", response_model=FincaOut, status_code=201, summary="Crear nueva finca")
def crear_finca(data: FincaCreate, db: Session = Depends(get_db)):
    finca = Finca(**data.model_dump())
    db.add(finca)
    db.commit()
    db.refresh(finca)
    return finca


@router.get("/{finca_id}", response_model=FincaOut, summary="Obtener finca por ID")
def obtener_finca(finca_id: UUID, db: Session = Depends(get_db)):
    finca = db.query(Finca).filter(Finca.id == finca_id).first()
    if not finca:
        raise HTTPException(status_code=404, detail="Finca no encontrada")
    return finca


@router.patch("/{finca_id}", response_model=FincaOut, summary="Actualizar datos de la finca")
def actualizar_finca(finca_id: UUID, data: FincaUpdate, db: Session = Depends(get_db)):
    finca = db.query(Finca).filter(Finca.id == finca_id).first()
    if not finca:
        raise HTTPException(status_code=404, detail="Finca no encontrada")

    for campo, valor in data.model_dump(exclude_unset=True).items():
        setattr(finca, campo, valor)

    db.commit()
    db.refresh(finca)
    return finca


@router.delete("/{finca_id}", summary="Eliminar finca")
def eliminar_finca(finca_id: UUID, db: Session = Depends(get_db)):
    finca = db.query(Finca).filter(Finca.id == finca_id).first()
    if not finca:
        raise HTTPException(status_code=404, detail="Finca no encontrada")
    db.delete(finca)
    db.commit()
    return {"message": "Finca eliminada correctamente"}
