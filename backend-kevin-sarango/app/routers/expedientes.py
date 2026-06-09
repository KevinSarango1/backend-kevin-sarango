from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID, uuid4
from app.database import get_db
from app.models.models import Expediente, HistorialTrazabilidad, DatoAgroambiental
from app.schemas.schemas import (
    ExpedienteCreate, ExpedienteOut, ExpedienteUpdate,
    HistorialCreate, HistorialOut
)

router = APIRouter()

def generar_eudr_id() -> str:
    return f"uuidv4-{uuid4().hex[:8].upper()}-{uuid4().hex[:5].upper()}"

# ─── EXPEDIENTES ─────────────────────────────────────────────

@router.get("/", response_model=List[ExpedienteOut], summary="Listar todos los expedientes")
def listar_expedientes(
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    organizacion: Optional[str] = Query(None, description="Filtrar por organización"),
    db: Session = Depends(get_db)
):
    query = db.query(Expediente)
    if estado:
        query = query.filter(Expediente.estado == estado)
    if organizacion:
        query = query.filter(Expediente.organizacion_inquilino == organizacion)
    return query.all()

@router.post("/", response_model=ExpedienteOut, status_code=201, summary="Crear nuevo expediente")
def crear_expediente(data: ExpedienteCreate, db: Session = Depends(get_db)):
    expediente = Expediente(
        eudr_id=generar_eudr_id(),
        **data.model_dump(exclude={"datos_agroambientales"})
    )
    db.add(expediente)
    db.flush()

    # Si vienen datos agroambientales, guardarlos también
    if data.datos_agroambientales:
        dato = DatoAgroambiental(
            expediente_id=expediente.id,
            **data.datos_agroambientales.model_dump()
        )
        db.add(dato)

    # Registrar en trazabilidad
    historial = HistorialTrazabilidad(
        expediente_id=expediente.id,
        accion="Expediente creado",
        descripcion=f"Registro inicial del productor {data.nombre_completo} - Finca {data.nombre_finca}",
        usuario="sistema"
    )
    db.add(historial)
    db.commit()
    db.refresh(expediente)
    return expediente

@router.get("/{expediente_id}", response_model=ExpedienteOut, summary="Obtener expediente por ID")
def obtener_expediente(expediente_id: UUID, db: Session = Depends(get_db)):
    exp = db.query(Expediente).filter(Expediente.id == expediente_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Expediente no encontrado")
    return exp

@router.get("/eudr/{eudr_id}", response_model=ExpedienteOut, summary="Buscar por EUDR ID")
def buscar_por_eudr(eudr_id: str, db: Session = Depends(get_db)):
    exp = db.query(Expediente).filter(Expediente.eudr_id == eudr_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Expediente no encontrado")
    return exp

@router.patch("/{expediente_id}", response_model=ExpedienteOut, summary="Actualizar expediente")
def actualizar_expediente(expediente_id: UUID, data: ExpedienteUpdate, db: Session = Depends(get_db)):
    exp = db.query(Expediente).filter(Expediente.id == expediente_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Expediente no encontrado")

    cambios = data.model_dump(exclude_unset=True)
    for campo, valor in cambios.items():
        setattr(exp, campo, valor)

    # Registrar cambio en trazabilidad
    historial = HistorialTrazabilidad(
        expediente_id=expediente_id,
        accion="Expediente actualizado",
        descripcion=f"Campos modificados: {', '.join(cambios.keys())}",
        usuario="sistema"
    )
    db.add(historial)
    db.commit()
    db.refresh(exp)
    return exp

@router.delete("/{expediente_id}", summary="Eliminar expediente")
def eliminar_expediente(expediente_id: UUID, db: Session = Depends(get_db)):
    exp = db.query(Expediente).filter(Expediente.id == expediente_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Expediente no encontrado")
    db.delete(exp)
    db.commit()
    return {"message": "Expediente eliminado"}

# ─── TRAZABILIDAD ────────────────────────────────────────────

@router.get("/{expediente_id}/historial", response_model=List[HistorialOut], summary="Ver historial de trazabilidad")
def ver_historial(expediente_id: UUID, db: Session = Depends(get_db)):
    exp = db.query(Expediente).filter(Expediente.id == expediente_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Expediente no encontrado")
    return exp.historial

@router.post("/{expediente_id}/historial", response_model=HistorialOut, status_code=201, summary="Agregar evento al historial")
def agregar_historial(expediente_id: UUID, data: HistorialCreate, db: Session = Depends(get_db)):
    exp = db.query(Expediente).filter(Expediente.id == expediente_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Expediente no encontrado")
    historial = HistorialTrazabilidad(expediente_id=expediente_id, **data.model_dump())
    db.add(historial)
    db.commit()
    db.refresh(historial)
    return historial
