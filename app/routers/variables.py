from fastapi import APIRouter, Depends, HTTPException
from prisma import Prisma
from typing import List
from app.database import get_db
from app.security import get_current_user, require_roles
from app.schemas.schemas import VariableDinamicaCreate, VariableDinamicaUpdate, VariableDinamicaOut

router = APIRouter()

_editor = Depends(require_roles("SUPER_ADMIN", "TENANT_ADMIN", "TECNICO_CAMPO", "AUDITOR_INTERNO"))


@router.get("/{dato_id}", response_model=List[VariableDinamicaOut], summary="Listar variables dinámicas de un dato agroambiental")
def listar_variables(
    dato_id: str,
    db: Prisma = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if not db.dato.find_first(where={"id": dato_id}):
        raise HTTPException(status_code=404, detail="Dato agroambiental no encontrado")
    return db.variabledinamica.find_many(where={"dato_id": dato_id})


@router.post("/{dato_id}", response_model=VariableDinamicaOut, status_code=201, summary="Agregar variable dinámica a un dato agroambiental")
def crear_variable(
    dato_id: str,
    data: VariableDinamicaCreate,
    db: Prisma = Depends(get_db),
    current_user: dict = _editor,
):
    if not db.dato.find_first(where={"id": dato_id}):
        raise HTTPException(status_code=404, detail="Dato agroambiental no encontrado")
    return db.variabledinamica.create(data={"dato_id": dato_id, **data.model_dump()})


@router.patch("/{dato_id}/{variable_id}", response_model=VariableDinamicaOut, summary="Actualizar variable dinámica")
def actualizar_variable(
    dato_id: str,
    variable_id: int,
    data: VariableDinamicaUpdate,
    db: Prisma = Depends(get_db),
    current_user: dict = _editor,
):
    if not db.variabledinamica.find_first(where={"id": variable_id, "dato_id": dato_id}):
        raise HTTPException(status_code=404, detail="Variable dinámica no encontrada")
    return db.variabledinamica.update(
        where={"id": variable_id},
        data=data.model_dump(exclude_unset=True),
    )


@router.delete("/{dato_id}/{variable_id}", summary="Eliminar variable dinámica")
def eliminar_variable(
    dato_id: str,
    variable_id: int,
    db: Prisma = Depends(get_db),
    current_user: dict = _editor,
):
    if not db.variabledinamica.find_first(where={"id": variable_id, "dato_id": dato_id}):
        raise HTTPException(status_code=404, detail="Variable dinámica no encontrada")
    db.variabledinamica.delete(where={"id": variable_id})
    return {"message": "Variable eliminada correctamente"}
