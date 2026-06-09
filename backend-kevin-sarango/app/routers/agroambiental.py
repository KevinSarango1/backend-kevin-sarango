from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from app.database import get_db
from app.models.models import DatoAgroambiental, Expediente, HistorialTrazabilidad
from app.schemas.schemas import DatoAgroambientalCreate, DatoAgroambientalOut

router = APIRouter()

@router.get("/{expediente_id}", response_model=List[DatoAgroambientalOut], summary="Obtener datos agroambientales de un expediente")
def obtener_datos(expediente_id: UUID, db: Session = Depends(get_db)):
    exp = db.query(Expediente).filter(Expediente.id == expediente_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Expediente no encontrado")
    return exp.datos_agroambientales

@router.post("/{expediente_id}", response_model=DatoAgroambientalOut, status_code=201, summary="Agregar datos agroambientales")
def crear_datos(expediente_id: UUID, data: DatoAgroambientalCreate, db: Session = Depends(get_db)):
    exp = db.query(Expediente).filter(Expediente.id == expediente_id).first()
    if not exp:
        raise HTTPException(status_code=404, detail="Expediente no encontrado")

    dato = DatoAgroambiental(expediente_id=expediente_id, **data.model_dump())
    db.add(dato)

    # Trazabilidad
    historial = HistorialTrazabilidad(
        expediente_id=expediente_id,
        accion="Datos agroambientales registrados",
        descripcion="Se registraron índices de biodiversidad, uso de suelo y stock de carbono.",
        usuario="sistema"
    )
    db.add(historial)
    db.commit()
    db.refresh(dato)
    return dato

@router.put("/{expediente_id}/{dato_id}", response_model=DatoAgroambientalOut, summary="Actualizar datos agroambientales")
def actualizar_datos(expediente_id: UUID, dato_id: UUID, data: DatoAgroambientalCreate, db: Session = Depends(get_db)):
    dato = db.query(DatoAgroambiental).filter(
        DatoAgroambiental.id == dato_id,
        DatoAgroambiental.expediente_id == expediente_id
    ).first()
    if not dato:
        raise HTTPException(status_code=404, detail="Dato agroambiental no encontrado")

    for campo, valor in data.model_dump(exclude_unset=True).items():
        setattr(dato, campo, valor)

    db.commit()
    db.refresh(dato)
    return dato

@router.get("/resumen/carbono", summary="Resumen de stock de carbono por expediente")
def resumen_carbono(db: Session = Depends(get_db)):
    """Retorna el total de carbono almacenado por finca - útil para reportes EUDR."""
    resultados = db.query(
        Expediente.nombre_finca,
        Expediente.eudr_id,
        DatoAgroambiental.total_stock_carbono
    ).join(DatoAgroambiental).all()

    return [
        {
            "nombre_finca": r[0],
            "eudr_id": r[1],
            "total_stock_carbono_tC_ha": r[2]
        }
        for r in resultados
    ]
