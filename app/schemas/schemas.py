from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ─── Enums (valores alineados con Prisma) ────────────────────

class TenenciaEnum(str, Enum):
    PROPIA = "PROPIA"
    POSESION = "POSESION"
    ARRENDAMIENTO = "ARRENDAMIENTO"


class GeneroEnum(str, Enum):
    MASCULINO = "MASCULINO"
    FEMENINO = "FEMENINO"


class EstadoEnum(str, Enum):
    PENDIENTE = "PENDIENTE"
    EN_PROCESO = "EN_PROCESO"
    APROBADO = "APROBADO"
    RECHAZADO = "RECHAZADO"


class RolNombreEnum(str, Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    TENANT_ADMIN = "TENANT_ADMIN"
    CLIENTE = "CLIENTE"
    TECNICO_CAMPO = "TECNICO_CAMPO"
    AUDITOR_INTERNO = "AUDITOR_INTERNO"
    AUDITOR_EXTERNO = "AUDITOR_EXTERNO"


class ResultadoAuditoriaEnum(str, Enum):
    APROBADO = "APROBADO"
    RECHAZADO = "RECHAZADO"


class EstadoCertificadoEnum(str, Enum):
    VIGENTE = "VIGENTE"
    VENCIDO = "VENCIDO"
    REVOCADO = "REVOCADO"


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
    id: str
    expediente_id: str
    creado_en: datetime

    class Config:
        from_attributes = True


# ─── Historial / Trazabilidad ────────────────────────────────

class HistorialCreate(BaseModel):
    accion: str
    descripcion: Optional[str] = None
    usuario: Optional[str] = None


class HistorialOut(HistorialCreate):
    id: str
    expediente_id: str
    fecha: datetime

    class Config:
        from_attributes = True


# ─── Expediente ──────────────────────────────────────────────

class ExpedienteBase(BaseModel):
    nombre_completo: str = Field(..., example="José Miguel Mosquera")
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
    id: str
    eudr_id: Optional[str] = None
    estado: str
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
    id: str
    nombre: str
    descripcion: Optional[str] = None

    class Config:
        from_attributes = True


# ─── Usuario ─────────────────────────────────────────────────

class UsuarioCreate(BaseModel):
    nombre: str
    email: str
    password: str
    rol_id: Optional[str] = None


class UsuarioOut(BaseModel):
    id: str
    nombre: str
    email: str
    rol_id: Optional[str] = None
    activo: bool
    creado_en: datetime

    class Config:
        from_attributes = True


class UsuarioUpdate(BaseModel):
    activo: Optional[bool] = None
    rol_id: Optional[str] = None


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
    productor_id: Optional[str] = None


class FincaOut(FincaCreate):
    id: str
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
    expediente_id: str
    resultado: ResultadoAuditoriaEnum
    deforestacion_detectada: bool = False
    fecha_corte: Optional[datetime] = None
    fuente: Optional[str] = "Google Earth Engine"
    observaciones: Optional[str] = None
    ejecutado_por: Optional[str] = None


class AuditoriaOut(BaseModel):
    id: str
    expediente_id: str
    fecha_auditoria: datetime
    resultado: str
    deforestacion_detectada: bool
    fecha_corte: Optional[datetime] = None
    fuente: Optional[str] = None
    observaciones: Optional[str] = None
    ejecutado_por: Optional[str] = None

    class Config:
        from_attributes = True


# ─── CertificadoDDS ──────────────────────────────────────────

class CertificadoCreate(BaseModel):
    expediente_id: str
    fecha_vencimiento: Optional[datetime] = None
    generado_por: Optional[str] = None
    url_documento: Optional[str] = None


class CertificadoOut(BaseModel):
    id: str
    expediente_id: str
    codigo_certificado: str
    fecha_emision: datetime
    fecha_vencimiento: Optional[datetime] = None
    estado: str
    generado_por: Optional[str] = None
    url_documento: Optional[str] = None

    class Config:
        from_attributes = True
