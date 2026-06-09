from sqlalchemy import Column, String, Float, Integer, DateTime, Enum, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base
from datetime import datetime
import uuid
import enum


# ─── Enums existentes ─────────────────────────────────────────

class TenenciaEnum(str, enum.Enum):
    propia = "Propia con escritura"
    posesion = "Posesión de hecho / Sin título"
    arrendamiento = "Arrendamiento legal"

class GeneroEnum(str, enum.Enum):
    masculino = "Masculino"
    femenino = "Femenino"
    otro = "Otro / Prefiero no decir"

class EstadoExpedienteEnum(str, enum.Enum):
    pendiente = "Pendiente"
    en_proceso = "En Proceso"
    aprobado = "Aprobado"
    rechazado = "Rechazado"

# ─── Enums nuevos ─────────────────────────────────────────────

class RolNombreEnum(str, enum.Enum):
    admin = "ADMIN"
    auditor = "AUDITOR"
    cliente = "CLIENTE"

class ResultadoAuditoriaEnum(str, enum.Enum):
    aprobado = "APROBADO"
    rechazado = "RECHAZADO"

class EstadoCertificadoEnum(str, enum.Enum):
    vigente = "VIGENTE"
    vencido = "VENCIDO"
    revocado = "REVOCADO"


# ─── Modelos existentes ───────────────────────────────────────

class Expediente(Base):
    __tablename__ = "expedientes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    eudr_id = Column(String, unique=True, index=True)

    nombre_completo = Column(String, nullable=False)
    cedula_id = Column(String, nullable=False, index=True)
    organizacion = Column(String)
    celular = Column(String)
    genero = Column(Enum(GeneroEnum))
    edad = Column(Integer)

    nombre_finca = Column(String, nullable=False)
    provincia = Column(String)
    canton = Column(String)
    parroquia = Column(String)
    barrio_sector = Column(String)
    area_total_ha = Column(Float)
    area_cultivada_ha = Column(Float)
    tenencia = Column(Enum(TenenciaEnum))

    latitud = Column(Float)
    longitud = Column(Float)

    estado = Column(Enum(EstadoExpedienteEnum), default=EstadoExpedienteEnum.pendiente)
    organizacion_inquilino = Column(String)
    creado_en = Column(DateTime, default=datetime.utcnow)
    actualizado_en = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    datos_agroambientales = relationship("DatoAgroambiental", back_populates="expediente", cascade="all, delete")
    historial = relationship("HistorialTrazabilidad", back_populates="expediente", cascade="all, delete")
    auditorias = relationship("AuditoriaGEE", back_populates="expediente", cascade="all, delete")
    certificados = relationship("CertificadoDDS", back_populates="expediente", cascade="all, delete")


class DatoAgroambiental(Base):
    __tablename__ = "datos_agroambientales"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    expediente_id = Column(UUID(as_uuid=True), ForeignKey("expedientes.id"), nullable=False)

    indice_shannon = Column(Float, comment="Índice de Biodiversidad Shannon-Wiener")
    indice_simpson = Column(Float, comment="Índice de Biodiversidad Simpson")

    uso_suelo = Column(String)
    cobertura_forestal = Column(String)
    sistema_produccion = Column(String)

    biomasa_arboles = Column(Float, comment="Biomasa Aérea de los Árboles (tC/ha)")
    biomasa_cafe = Column(Float, comment="Biomasa Aérea del Café (tC/ha)")
    hojarasca_mantillo = Column(Float, comment="Hojarasca y Mantillo (tC/ha)")
    carbono_organico_suelo = Column(Float, comment="Carbono Orgánico del Suelo COS (tC/ha)")
    total_stock_carbono = Column(Float, comment="Total stock de carbono (tC/ha)")

    creado_en = Column(DateTime, default=datetime.utcnow)

    expediente = relationship("Expediente", back_populates="datos_agroambientales")


class HistorialTrazabilidad(Base):
    __tablename__ = "historial_trazabilidad"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    expediente_id = Column(UUID(as_uuid=True), ForeignKey("expedientes.id"), nullable=False)
    accion = Column(String, nullable=False)
    descripcion = Column(Text)
    usuario = Column(String)
    fecha = Column(DateTime, default=datetime.utcnow)

    expediente = relationship("Expediente", back_populates="historial")


# ─── Modelos nuevos ───────────────────────────────────────────

class Rol(Base):
    __tablename__ = "roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre = Column(Enum(RolNombreEnum), unique=True, nullable=False)
    descripcion = Column(String)

    usuarios = relationship("Usuario", back_populates="rol")


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    rol_id = Column(UUID(as_uuid=True), ForeignKey("roles.id"), nullable=True)
    activo = Column(Boolean, default=True)
    creado_en = Column(DateTime, default=datetime.utcnow)

    rol = relationship("Rol", back_populates="usuarios")
    fincas = relationship("Finca", back_populates="productor")


class Finca(Base):
    __tablename__ = "fincas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre = Column(String, nullable=False)
    eudr_id = Column(String, unique=True, index=True, nullable=True)
    provincia = Column(String)
    canton = Column(String)
    parroquia = Column(String)
    area_total_ha = Column(Float)
    area_cultivada_ha = Column(Float)
    tenencia = Column(Enum(TenenciaEnum))
    latitud = Column(Float)
    longitud = Column(Float)
    productor_id = Column(UUID(as_uuid=True), ForeignKey("usuarios.id"), nullable=True)
    creado_en = Column(DateTime, default=datetime.utcnow)

    productor = relationship("Usuario", back_populates="fincas")


class AuditoriaGEE(Base):
    __tablename__ = "auditorias_gee"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    expediente_id = Column(UUID(as_uuid=True), ForeignKey("expedientes.id"), nullable=False)
    fecha_auditoria = Column(DateTime, default=datetime.utcnow)
    resultado = Column(Enum(ResultadoAuditoriaEnum), nullable=False)
    deforestacion_detectada = Column(Boolean, default=False)
    fecha_corte = Column(DateTime)
    fuente = Column(String, default="Google Earth Engine")
    observaciones = Column(Text)
    ejecutado_por = Column(String)

    expediente = relationship("Expediente", back_populates="auditorias")


class CertificadoDDS(Base):
    __tablename__ = "certificados_dds"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    expediente_id = Column(UUID(as_uuid=True), ForeignKey("expedientes.id"), nullable=False)
    codigo_certificado = Column(String, unique=True, index=True)
    fecha_emision = Column(DateTime, default=datetime.utcnow)
    fecha_vencimiento = Column(DateTime)
    estado = Column(Enum(EstadoCertificadoEnum), default=EstadoCertificadoEnum.vigente)
    generado_por = Column(String)
    url_documento = Column(String)

    expediente = relationship("Expediente", back_populates="certificados")
