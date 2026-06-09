from fastapi import APIRouter, Depends, HTTPException
from prisma import Prisma
from typing import List
from app.database import get_db
from app.security import get_current_user, require_roles
from app.schemas.schemas import DatoAgroambientalCreate, DatoAgroambientalOut

router = APIRouter()


@router.get("/{expediente_id}", response_model=List[DatoAgroambientalOut], summary="Obtener datos agroambientales de un expediente")
def obtener_datos(
    expediente_id: str,
    db: Prisma = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not db.expediente.find_first(where={"id": expediente_id}):
        raise HTTPException(status_code=404, detail="Expediente no encontrado")
    return db.dato.find_many(where={"expediente_id": expediente_id})


@router.post("/{expediente_id}", response_model=DatoAgroambientalOut, status_code=201, summary="Agregar datos agroambientales")
def crear_datos(
    expediente_id: str,
    data: DatoAgroambientalCreate,
    db: Prisma = Depends(get_db),
    current_user: dict = Depends(require_roles("SUPER_ADMIN", "TENANT_ADMIN", "TECNICO_CAMPO", "AUDITOR_INTERNO")),
):
    if not db.expediente.find_first(where={"id": expediente_id}):
        raise HTTPException(status_code=404, detail="Expediente no encontrado")
    dato = db.dato.create(data={"expediente_id": expediente_id, **data.model_dump()})
    db.historial.create(data={
        "expediente_id": expediente_id,
        "accion": "Datos agroambientales registrados",
        "descripcion": "Se registraron índices de biodiversidad, uso de suelo y stock de carbono.",
        "usuario": current_user.get("sub", "sistema"),
    })
    return dato


@router.put("/{expediente_id}/{dato_id}", response_model=DatoAgroambientalOut, summary="Actualizar datos agroambientales")
def actualizar_datos(
    expediente_id: str,
    dato_id: str,
    data: DatoAgroambientalCreate,
    db: Prisma = Depends(get_db),
    current_user: dict = Depends(require_roles("SUPER_ADMIN", "TENANT_ADMIN", "TECNICO_CAMPO", "AUDITOR_INTERNO")),
):
    dato = db.dato.find_first(where={"id": dato_id, "expediente_id": expediente_id})
    if not dato:
        raise HTTPException(status_code=404, detail="Dato agroambiental no encontrado")
    return db.dato.update(where={"id": dato_id}, data=data.model_dump(exclude_unset=True))


@router.get("/resumen/carbono", summary="Resumen de stock de carbono por expediente")
def resumen_carbono(
    db: Prisma = Depends(get_db),
    current_user: dict = Depends(require_roles("SUPER_ADMIN", "TENANT_ADMIN", "TECNICO_CAMPO", "AUDITOR_INTERNO")),
):
    datos = db.dato.find_many(include={"expediente": True})
    return [
        {
            "nombre_finca": d.expediente.nombre_finca,
            "eudr_id": d.expediente.eudr_id,
            "total_stock_carbono_tC_ha": d.total_stock_carbono,
        }
        for d in datos
        if d.total_stock_carbono is not None
    ]
