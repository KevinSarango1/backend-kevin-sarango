from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from enum import Enum

# ─── Enums existentes ─────────────────────────────────────────

class TenenciaEnum(str, Enum):
    propia = "Propia con escritura"
    posesion = "Posesión de hecho / Sin título"
    arrendamiento = "Arrendamiento legal"

class GeneroEnum(str, Enum):
    masculino = "Masculino"
    femenino = "Femenino"
    otro = "Otro / Prefiero no decir"

class EstadoEnum(str, Enum):
    pendiente = "Pendiente"
    en_proceso = "En Proceso"
    aprobado = "Aprobado"
    rechazado = "Rechazado"

# ─── Enums nuevos ─────────────────────────────────────────────

class RolNombreEnum(str, Enum):
    admin = "ADMIN"
    auditor = "AUDITOR"
    cliente = "CLIENTE"

class ResultadoAuditoriaEnum(str, Enum):
    aprobado = "APROBADO"
    rechazado = "RECHAZADO"

class EstadoCertificadoEnum(str, Enum):
    vigente = "VIGENTE"
    vencido = "VENCIDO"
    revocado = "REVOCADO"

# ─── Agroambiental ───────────────────────────────────────────

class DatoAgroambientalBase(BaseModel):
    indice_shannon: Optional[float] = None
    indice_simpson: Optional[float] = None
    uso_suelo: Optional[str] = None
    cobertura_forestal: Optional[str] = None
    sistema_produccion: Optional[str] = None
    biomasa_arboles: Optional[float] = None
    biomasa_cafe: Optional[float] = None
    hojarasca_mantillo: Optional[float] = None
    carbono_organico_suelo: Optional[float] = None
    total_stock_carbono: Optional[float] = None

class DatoAgroambientalCreate(DatoAgroambientalBase):
    pass

class DatoAgroambientalOut(DatoAgroambientalBase):
    id: UUID
    expediente_id: UUID
    creado_en: datetime

    class Config:
        from_attributes = True

# ─── Historial / Trazabilidad ────────────────────────────────

class HistorialCreate(BaseModel):
    accion: str
    descripcion: Optional[str] = None
    usuario: Optional[str] = None

class HistorialOut(HistorialCreate):
    id: UUID
    expediente_id: UUID
    fecha: datetime

    class Config:
        from_attributes = True

# ─── Expediente ──────────────────────────────────────────────

class ExpedienteBase(BaseModel):
    nombre_completo: str = Field(..., example="José Miguel Moosquera")
    cedula_id: str = Field(..., example="1100433455")
    organizacion: Optional[str] = Field(None, example="Asociación APECAEL")
    celular: Optional[str] = None
    genero: Optional[GeneroEnum] = None
    edad: Optional[int] = None

    nombre_finca: str = Field(..., example="El Ahuacate")
    provincia: Optional[str] = Field(None, example="Loja")
    canton: Optional[str] = Field(None, example="Loja")
    parroquia: Optional[str] = None
    barrio_sector: Optional[str] = None
    area_total_ha: Optional[float] = Field(None, example=3.0)
    area_cultivada_ha: Optional[float] = None
    tenencia: Optional[TenenciaEnum] = None

    latitud: Optional[float] = Field(None, example=-4.2625)
    longitud: Optional[float] = Field(None, example=-79.2231)
    organizacion_inquilino: Optional[str] = None

class ExpedienteCreate(ExpedienteBase):
    datos_agroambientales: Optional[DatoAgroambientalCreate] = None

class ExpedienteUpdate(BaseModel):
    estado: Optional[EstadoEnum] = None
    nombre_finca: Optional[str] = None
    area_total_ha: Optional[float] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None

class ExpedienteOut(ExpedienteBase):
    id: UUID
    eudr_id: str
    estado: EstadoEnum
    creado_en: datetime
    actualizado_en: datetime
    datos_agroambientales: List[DatoAgroambientalOut] = []
    historial: List[HistorialOut] = []

    class Config:
        from_attributes = True

# ─── Rol ─────────────────────────────────────────────────────

class RolCreate(BaseModel):
    nombre: RolNombreEnum
    descripcion: Optional[str] = None

class RolOut(BaseModel):
    id: UUID
    nombre: RolNombreEnum
    descripcion: Optional[str] = None

    class Config:
        from_attributes = True

# ─── Usuario ─────────────────────────────────────────────────

class UsuarioCreate(BaseModel):
    nombre: str
    email: str
    password: str
    rol_id: Optional[UUID] = None

class UsuarioOut(BaseModel):
    id: UUID
    nombre: str
    email: str
    rol_id: Optional[UUID] = None
    activo: bool
    creado_en: datetime

    class Config:
        from_attributes = True

class UsuarioUpdate(BaseModel):
    activo: Optional[bool] = None
    rol_id: Optional[UUID] = None

# ─── Finca ───────────────────────────────────────────────────

class FincaCreate(BaseModel):
    nombre: str
    eudr_id: Optional[str] = None
    provincia: Optional[str] = None
    canton: Optional[str] = None
    parroquia: Optional[str] = None
    area_total_ha: Optional[float] = None
    area_cultivada_ha: Optional[float] = None
    tenencia: Optional[TenenciaEnum] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    productor_id: Optional[UUID] = None

class FincaOut(FincaCreate):
    id: UUID
    creado_en: datetime

    class Config:
        from_attributes = True

class FincaUpdate(BaseModel):
    nombre: Optional[str] = None
    provincia: Optional[str] = None
    canton: Optional[str] = None
    parroquia: Optional[str] = None
    area_total_ha: Optional[float] = None
    area_cultivada_ha: Optional[float] = None
    tenencia: Optional[TenenciaEnum] = None
    latitud: Optional[float] = None
    longitud: Optional[float] = None

# ─── AuditoriaGEE ────────────────────────────────────────────

class AuditoriaCreate(BaseModel):
    expediente_id: UUID
    resultado: ResultadoAuditoriaEnum
    deforestacion_detectada: bool = False
    fecha_corte: Optional[datetime] = None
    fuente: Optional[str] = "Google Earth Engine"
    observaciones: Optional[str] = None
    ejecutado_por: Optional[str] = None

class AuditoriaOut(BaseModel):
    id: UUID
    expediente_id: UUID
    fecha_auditoria: datetime
    resultado: ResultadoAuditoriaEnum
    deforestacion_detectada: bool
    fecha_corte: Optional[datetime] = None
    fuente: Optional[str] = None
    observaciones: Optional[str] = None
    ejecutado_por: Optional[str] = None

    class Config:
        from_attributes = True

# ─── CertificadoDDS ──────────────────────────────────────────

class CertificadoCreate(BaseModel):
    expediente_id: UUID
    fecha_vencimiento: Optional[datetime] = None
    generado_por: Optional[str] = None
    url_documento: Optional[str] = None

class CertificadoOut(BaseModel):
    id: UUID
    expediente_id: UUID
    codigo_certificado: str
    fecha_emision: datetime
    fecha_vencimiento: Optional[datetime] = None
    estado: EstadoCertificadoEnum
    generado_por: Optional[str] = None
    url_documento: Optional[str] = None

    class Config:
        from_attributes = True
