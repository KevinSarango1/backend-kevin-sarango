# Modelos gestionados por Prisma — ver schema.prisma en la raíz del proyecto.
# Este archivo conserva los enums de Python para importaciones en schemas y routers.

import enum


class TenenciaEnum(str, enum.Enum):
    PROPIA = "PROPIA"
    POSESION = "POSESION"
    ARRENDAMIENTO = "ARRENDAMIENTO"


class GeneroEnum(str, enum.Enum):
    MASCULINO = "MASCULINO"
    FEMENINO = "FEMENINO"


class EstadoExpedienteEnum(str, enum.Enum):
    PENDIENTE = "PENDIENTE"
    EN_PROCESO = "EN_PROCESO"
    APROBADO = "APROBADO"
    RECHAZADO = "RECHAZADO"


class RolNombreEnum(str, enum.Enum):
    ADMIN = "ADMIN"
    AUDITOR = "AUDITOR"
    CLIENTE = "CLIENTE"


class ResultadoAuditoriaEnum(str, enum.Enum):
    APROBADO = "APROBADO"
    RECHAZADO = "RECHAZADO"


class EstadoCertificadoEnum(str, enum.Enum):
    VIGENTE = "VIGENTE"
    VENCIDO = "VENCIDO"
    REVOCADO = "REVOCADO"
