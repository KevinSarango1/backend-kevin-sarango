# GeoGuard EUDR — Documentación Técnica del Backend

**Módulo:** Backend de Gestión de Expedientes EUDR  
**Autor:** Kevin Sarango  
**Versión:** 2.0.0  
**Stack:** FastAPI · Prisma (SQLite) · JWT HS256 · bcrypt  

---

## Tabla de Contenidos

1. [Descripción General](#1-descripción-general)
2. [Arquitectura](#2-arquitectura)
3. [Estructura del Proyecto](#3-estructura-del-proyecto)
4. [Modelos de Datos](#4-modelos-de-datos)
5. [Autenticación y Autorización](#5-autenticación-y-autorización)
6. [Endpoints de la API](#6-endpoints-de-la-api)
   - [Expedientes](#61-expedientes)
   - [Datos Agroambientales](#62-datos-agroambientales)
   - [Usuarios](#63-usuarios)
   - [Roles](#64-roles)
   - [Fincas](#65-fincas)
   - [Auditoría GEE](#66-auditoría-gee)
   - [Certificados DDS](#67-certificados-dds)
7. [Enums y Valores Permitidos](#7-enums-y-valores-permitidos)
8. [Lógica de Negocio](#8-lógica-de-negocio)
9. [Configuración del Entorno](#9-configuración-del-entorno)
10. [Instalación y Puesta en Marcha](#10-instalación-y-puesta-en-marcha)
11. [Dependencias](#11-dependencias)

---

## 1. Descripción General

GeoGuard EUDR es un sistema de trazabilidad agroambiental que permite gestionar expedientes de productores agrícolas para el cumplimiento del Reglamento Europeo de Deforestación (EUDR). El backend expone una API REST que cubre el ciclo de vida completo de un expediente:

```
Registro del productor → Datos agroambientales → Auditoría GEE → Certificado DDS
```

El sistema se integra con un módulo externo de autenticación (`auth-service`) mediante tokens JWT. La validación del token es **local** (sin llamadas HTTP por petición), usando una clave secreta compartida (HS256).

---

## 2. Arquitectura

```
┌─────────────────────────────────────────────────────────┐
│                    Cliente (Frontend)                   │
└───────────────────────┬─────────────────────────────────┘
                        │ HTTP + Bearer JWT
┌───────────────────────▼─────────────────────────────────┐
│              FastAPI — GeoGuard EUDR API                │
│                                                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌───────────┐  │
│  │Expedientes│ │Auditoria │ │Certific. │ │Usuarios   │  │
│  └──────────┘ └──────────┘ └──────────┘ └───────────┘  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐                 │
│  │Agroamb.  │ │ Fincas   │ │  Roles   │                 │
│  └──────────┘ └──────────┘ └──────────┘                 │
│                                                         │
│  ┌─────────────────────────────────────────────────┐    │
│  │  security.py — JWT local (HS256) + RBAC         │    │
│  └─────────────────────────────────────────────────┘    │
│                                                         │
│  ┌─────────────────────────────────────────────────┐    │
│  │  Prisma ORM (sync) — SQLite (geoguard.db)       │    │
│  └─────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  auth-service (externo) — emite tokens JWT HS256        │
│  https://auth-service-w3lo.onrender.com                 │
└─────────────────────────────────────────────────────────┘
```

**Decisiones de diseño clave:**
- ORM: **Prisma** (sync interface) en lugar de SQLAlchemy — genera el cliente Python desde `schema.prisma`.
- BD: **SQLite** en desarrollo (`file:./geoguard.db`). SQLite no soporta enums nativos en Prisma, por lo que todos los campos de tipo enum se almacenan como `String`; la validación la realiza Pydantic.
- Auth: validación **local** del JWT — la aplicación no llama al `auth-service` en cada petición, solo verifica la firma con la `SECRET_KEY` compartida.

---

## 3. Estructura del Proyecto

```
backend-kevin-sarango/
│
├── app/
│   ├── __init__.py
│   ├── main.py              # Punto de entrada, registro de routers, CORS, lifespan
│   ├── database.py          # Instancia global de Prisma
│   ├── security.py          # Validación JWT y factory RBAC require_roles()
│   │
│   ├── models/
│   │   └── models.py        # Enums de Python (sin SQLAlchemy)
│   │
│   ├── schemas/
│   │   └── schemas.py       # Modelos Pydantic (request/response)
│   │
│   └── routers/
│       ├── expedientes.py   # CRUD expedientes + historial trazabilidad
│       ├── agroambiental.py # CRUD datos agroambientales + resumen carbono
│       ├── usuarios.py      # CRUD usuarios (solo ADMIN)
│       ├── roles.py         # CRUD roles
│       ├── fincas.py        # CRUD fincas
│       ├── auditoria.py     # Registro auditorías GEE
│       └── certificados.py  # Emisión y revocación certificados DDS
│
├── schema.prisma            # Definición de modelos de base de datos
├── init_db.py               # Script para generar cliente Prisma y aplicar schema
├── requirements.txt         # Dependencias Python
├── test_api.py              # Suite de validaciones automatizadas (42 tests)
├── .env                     # Variables de entorno (NO subir a git)
└── .env.example             # Plantilla de variables de entorno
```

---

## 4. Modelos de Datos

El schema completo está definido en `schema.prisma`. A continuación se describe cada tabla:

### Expediente → tabla `expedientes`
Registro principal del productor y su finca.

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | String (UUID) | Clave primaria |
| `eudr_id` | String (único) | Código EUDR generado automáticamente (`uuidv4-XXXXXXXX-XXXXX`) |
| `nombre_completo` | String | Nombre del productor |
| `cedula_id` | String | Número de cédula/ID |
| `organizacion` | String? | Organización a la que pertenece |
| `celular` | String? | Teléfono de contacto |
| `genero` | String? | `MASCULINO` / `FEMENINO` |
| `edad` | Int? | Edad del productor |
| `nombre_finca` | String | Nombre de la finca |
| `provincia` | String? | Provincia |
| `canton` | String? | Cantón |
| `parroquia` | String? | Parroquia |
| `barrio_sector` | String? | Barrio o sector |
| `area_total_ha` | Float? | Área total en hectáreas |
| `area_cultivada_ha` | Float? | Área cultivada en hectáreas |
| `tenencia` | String? | `PROPIA` / `POSESION` / `ARRENDAMIENTO` |
| `latitud` | Float? | Coordenada geográfica |
| `longitud` | Float? | Coordenada geográfica |
| `estado` | String | `PENDIENTE` / `EN_PROCESO` / `APROBADO` / `RECHAZADO` |
| `organizacion_inquilino` | String? | Organización del inquilino (multi-tenant) |
| `creado_en` | DateTime | Fecha de creación (automático) |
| `actualizado_en` | DateTime | Fecha de última actualización (automático) |

**Relaciones:** tiene muchos `Dato`, `Historial`, `Auditoria`, `Certificado` (todos con `onDelete: Cascade`).

---

### Dato → tabla `datos_agroambientales`
Indicadores de biodiversidad y carbono asociados a un expediente.

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | String (UUID) | Clave primaria |
| `expediente_id` | String | FK a `expedientes` |
| `indice_shannon` | Float? | Índice de diversidad Shannon |
| `indice_simpson` | Float? | Índice de diversidad Simpson |
| `uso_suelo` | String? | Descripción del uso del suelo |
| `cobertura_forestal` | String? | Tipo de cobertura forestal |
| `sistema_produccion` | String? | Sistema de producción agrícola |
| `biomasa_arboles` | Float? | Biomasa de árboles (tC/ha) |
| `biomasa_cafe` | Float? | Biomasa de café (tC/ha) |
| `hojarasca_mantillo` | Float? | Hojarasca y mantillo (tC/ha) |
| `carbono_organico_suelo` | Float? | Carbono orgánico del suelo (tC/ha) |
| `total_stock_carbono` | Float? | Stock total de carbono (tC/ha) |
| `creado_en` | DateTime | Fecha de creación (automático) |

---

### Historial → tabla `historial_trazabilidad`
Registro automático de todos los eventos del expediente.

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | String (UUID) | Clave primaria |
| `expediente_id` | String | FK a `expedientes` |
| `accion` | String | Descripción corta del evento |
| `descripcion` | String? | Detalle del evento |
| `usuario` | String? | `sub` del token JWT que realizó la acción |
| `fecha` | DateTime | Fecha del evento (automático) |

---

### Rol → tabla `roles`
Roles del sistema para RBAC.

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | String (UUID) | Clave primaria |
| `nombre` | String (único) | `ADMIN` / `AUDITOR` / `CLIENTE` |
| `descripcion` | String? | Descripción del rol |

---

### Usuario → tabla `usuarios`
Usuarios del sistema gestionados por el ADMIN.

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | String (UUID) | Clave primaria |
| `nombre` | String | Nombre completo |
| `email` | String (único) | Correo electrónico |
| `password_hash` | String | Contraseña hasheada con bcrypt |
| `rol_id` | String? | FK a `roles` |
| `activo` | Boolean | `true` por defecto; `false` = desactivado (soft delete) |
| `creado_en` | DateTime | Fecha de creación (automático) |

---

### Finca → tabla `fincas`
Información geoespacial de fincas, opcionalmente vinculadas a un productor.

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | String (UUID) | Clave primaria |
| `nombre` | String | Nombre de la finca |
| `eudr_id` | String? (único) | Código EUDR |
| `provincia` | String? | Provincia |
| `canton` | String? | Cantón |
| `parroquia` | String? | Parroquia |
| `area_total_ha` | Float? | Área total |
| `area_cultivada_ha` | Float? | Área cultivada |
| `tenencia` | String? | `PROPIA` / `POSESION` / `ARRENDAMIENTO` |
| `latitud` | Float? | Latitud |
| `longitud` | Float? | Longitud |
| `productor_id` | String? | FK a `usuarios` |
| `creado_en` | DateTime | Fecha de creación |

---

### Auditoria → tabla `auditorias_gee`
Resultados de auditorías satelitales de deforestación (Google Earth Engine).

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | String (UUID) | Clave primaria |
| `expediente_id` | String | FK a `expedientes` |
| `fecha_auditoria` | DateTime | Fecha de la auditoría (automático) |
| `resultado` | String | `APROBADO` / `RECHAZADO` |
| `deforestacion_detectada` | Boolean | Si se detectó deforestación |
| `fecha_corte` | DateTime? | Fecha de corte del análisis |
| `fuente` | String? | Fuente del análisis (default: `Google Earth Engine`) |
| `observaciones` | String? | Observaciones adicionales |
| `ejecutado_por` | String? | `sub` del token JWT del auditor |

**Efecto secundario:** al crear una auditoría, el estado del expediente se actualiza automáticamente a `APROBADO` o `RECHAZADO`.

---

### Certificado → tabla `certificados_dds`
Certificados de Due Diligence Statement (DDS) para exportación.

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | String (UUID) | Clave primaria |
| `expediente_id` | String | FK a `expedientes` |
| `codigo_certificado` | String (único) | Código generado: `DDS-{año}-{8 chars hex}` |
| `fecha_emision` | DateTime | Fecha de emisión (automático) |
| `fecha_vencimiento` | DateTime? | Fecha de vencimiento |
| `estado` | String | `VIGENTE` / `VENCIDO` / `REVOCADO` |
| `generado_por` | String? | `sub` del token JWT del generador |
| `url_documento` | String? | URL del documento PDF |

**Requisito previo:** el expediente debe tener al menos una auditoría GEE con `resultado = APROBADO`.

---

## 5. Autenticación y Autorización

### Flujo de autenticación

```
1. El usuario se autentica en auth-service (externo)
2. auth-service emite un JWT firmado con SECRET_KEY compartida (HS256)
3. El cliente envía el JWT en el header: Authorization: Bearer <token>
4. Este backend valida la firma localmente (sin llamadas HTTP)
5. Se extrae el payload: { sub, role, exp }
```

### Estructura del JWT

```json
{
  "sub": "usuario@ejemplo.com",
  "role": "ADMIN",
  "exp": 1700000000
}
```

| Campo | Descripción |
|---|---|
| `sub` | Identificador del usuario (email) |
| `role` | Rol del usuario: `ADMIN`, `AUDITOR` o `CLIENTE` |
| `exp` | Timestamp de expiración |

### Implementación (`app/security.py`)

**`get_current_user`** — verifica el token y retorna el payload:
```python
def get_current_user(credentials = Depends(HTTPBearer())) -> dict:
    # Lanza HTTP 401 si el token es inválido o expirado
```

**`require_roles(*roles)`** — factory de dependencias para RBAC:
```python
def require_roles(*allowed: str):
    # Lanza HTTP 403 si el rol del token no está en la lista
```

### Tabla de permisos por endpoint

| Recurso | GET (listar/leer) | POST (crear) | PATCH/PUT | DELETE |
|---|---|---|---|---|
| Expedientes | Cualquier token | ADMIN, AUDITOR | ADMIN, AUDITOR | ADMIN |
| Agroambiental | Cualquier token | ADMIN, AUDITOR | ADMIN, AUDITOR | — |
| Usuarios | ADMIN | ADMIN | ADMIN | ADMIN |
| Roles | Cualquier token | ADMIN | — | ADMIN |
| Fincas | Cualquier token | Cualquier token | ADMIN, AUDITOR | ADMIN |
| Auditoría GEE | ADMIN, AUDITOR* | ADMIN, AUDITOR | — | — |
| Certificados DDS | ADMIN, AUDITOR* | ADMIN, AUDITOR | — | — |

> *El GET por ID o por expediente está abierto a cualquier token autenticado.  
> *Revocar certificado: solo ADMIN.

---

## 6. Endpoints de la API

**Base URL:** `http://localhost:8000/api/v1`  
**Documentación interactiva:** `http://localhost:8000/docs`

---

### 6.1 Expedientes

**Prefijo:** `/api/v1/expedientes`

#### `GET /`
Lista todos los expedientes. Soporta filtros por query params.

**Auth:** cualquier token  
**Query params opcionales:**
- `estado` — filtra por estado (`PENDIENTE`, `APROBADO`, etc.)
- `organizacion` — filtra por `organizacion_inquilino`

**Respuesta 200:**
```json
[
  {
    "id": "uuid",
    "eudr_id": "uuidv4-2A43E5A5-3EC5C",
    "nombre_completo": "José Mosquera",
    "nombre_finca": "El Ahuacate",
    "estado": "PENDIENTE",
    "historial": [...],
    "datos_agroambientales": [...]
  }
]
```

---

#### `POST /`
Crea un nuevo expediente. Genera `eudr_id` automáticamente y registra el primer evento en el historial.

**Auth:** ADMIN, AUDITOR

**Body:**
```json
{
  "nombre_completo": "José Mosquera",
  "cedula_id": "1100433455",
  "nombre_finca": "El Ahuacate",
  "provincia": "Loja",
  "canton": "Loja",
  "latitud": -4.2625,
  "longitud": -79.2231,
  "genero": "MASCULINO",
  "tenencia": "PROPIA",
  "area_total_ha": 3.0,
  "datos_agroambientales": {
    "indice_shannon": 2.5,
    "total_stock_carbono": 45.3
  }
}
```

**Respuesta 201:** objeto `ExpedienteOut` completo con historial y datos agroambientales.

---

#### `GET /eudr/{eudr_id}`
Busca un expediente por su código EUDR.

**Auth:** cualquier token  
**Respuesta 200:** objeto `ExpedienteOut` | **404** si no existe.

---

#### `GET /{expediente_id}`
Obtiene un expediente por UUID.

**Auth:** cualquier token  
**Respuesta 200:** objeto `ExpedienteOut` | **404** si no existe.

---

#### `PATCH /{expediente_id}`
Actualiza campos del expediente y registra el cambio en el historial.

**Auth:** ADMIN, AUDITOR

**Body (campos opcionales):**
```json
{
  "estado": "EN_PROCESO",
  "nombre_finca": "Nueva Finca",
  "area_total_ha": 5.0,
  "latitud": -4.3,
  "longitud": -79.5
}
```

**Respuesta 200:** objeto `ExpedienteOut` actualizado.

---

#### `DELETE /{expediente_id}`
Elimina un expediente y todos sus registros relacionados (cascade).

**Auth:** ADMIN  
**Respuesta 200:** `{"message": "Expediente eliminado"}`

---

#### `GET /{expediente_id}/historial`
Lista el historial de trazabilidad de un expediente.

**Auth:** cualquier token  
**Respuesta 200:** lista de `HistorialOut`

---

#### `POST /{expediente_id}/historial`
Agrega un evento manual al historial.

**Auth:** ADMIN, AUDITOR

**Body:**
```json
{
  "accion": "Visita de campo",
  "descripcion": "Se verificó la finca in situ"
}
```

---

### 6.2 Datos Agroambientales

**Prefijo:** `/api/v1/agroambiental`

#### `GET /{expediente_id}`
Lista los datos agroambientales de un expediente.

**Auth:** cualquier token  
**Respuesta 200:** lista de `DatoAgroambientalOut`

---

#### `POST /{expediente_id}`
Agrega un nuevo registro de datos agroambientales. Registra automáticamente un evento en el historial.

**Auth:** ADMIN, AUDITOR

**Body:**
```json
{
  "indice_shannon": 2.1,
  "indice_simpson": 0.85,
  "uso_suelo": "Agroforestal",
  "cobertura_forestal": "Bosque nativo",
  "biomasa_arboles": 120.5,
  "biomasa_cafe": 8.3,
  "total_stock_carbono": 38.5
}
```

---

#### `PUT /{expediente_id}/{dato_id}`
Actualiza un registro de datos agroambientales existente.

**Auth:** ADMIN, AUDITOR  
**Body:** mismos campos que POST (todos opcionales).

---

#### `GET /resumen/carbono`
Resumen consolidado del stock de carbono por finca.

**Auth:** ADMIN, AUDITOR

**Respuesta 200:**
```json
[
  {
    "nombre_finca": "El Ahuacate",
    "eudr_id": "uuidv4-2A43E5A5-3EC5C",
    "total_stock_carbono_tC_ha": 45.3
  }
]
```

---

### 6.3 Usuarios

**Prefijo:** `/api/v1/usuarios`  
**Todos los endpoints requieren rol ADMIN.**

#### `GET /`
Lista todos los usuarios del sistema.

**Respuesta 200:** lista de `UsuarioOut` (sin `password_hash`).

---

#### `POST /`
Crea un nuevo usuario. La contraseña se hashea con bcrypt antes de almacenarse.

**Body:**
```json
{
  "nombre": "Ana Auditora",
  "email": "ana@geoguard.ec",
  "password": "MiPassword123!",
  "rol_id": "uuid-del-rol"
}
```

**Respuesta 201:** objeto `UsuarioOut`  
**400** si el email ya está registrado.

---

#### `GET /{usuario_id}`
Obtiene un usuario por ID.

**Respuesta 200:** `UsuarioOut` | **404** si no existe.

---

#### `PATCH /{usuario_id}`
Actualiza el rol o estado activo de un usuario.

**Body:**
```json
{
  "rol_id": "nuevo-uuid-rol",
  "activo": true
}
```

---

#### `DELETE /{usuario_id}`
**Soft delete** — desactiva el usuario (`activo = false`) sin eliminar el registro.

**Respuesta 200:** `{"message": "Usuario desactivado correctamente"}`

---

### 6.4 Roles

**Prefijo:** `/api/v1/roles`

#### `GET /`
Lista todos los roles.

**Auth:** cualquier token  
**Respuesta 200:** lista de `RolOut`

---

#### `GET /{rol_id}`
Obtiene un rol por ID.

**Auth:** cualquier token  
**Respuesta 200:** `RolOut` | **404** si no existe.

---

#### `POST /`
Crea un nuevo rol.

**Auth:** ADMIN

**Body:**
```json
{
  "nombre": "AUDITOR",
  "descripcion": "Auditor GEE del sistema"
}
```

**Respuesta 201:** `RolOut`  
**400** si el nombre ya existe.

---

#### `DELETE /{rol_id}`
Elimina un rol.

**Auth:** ADMIN  
**Respuesta 200:** `{"message": "Rol eliminado correctamente"}`

---

### 6.5 Fincas

**Prefijo:** `/api/v1/fincas`

#### `GET /`
Lista las fincas. Soporta filtros por `provincia` y `canton`.

**Auth:** cualquier token

---

#### `POST /`
Crea una nueva finca.

**Auth:** cualquier token

**Body:**
```json
{
  "nombre": "Finca Verde",
  "provincia": "Loja",
  "canton": "Loja",
  "area_total_ha": 5.5,
  "tenencia": "PROPIA",
  "latitud": -4.0,
  "longitud": -79.2,
  "productor_id": "uuid-del-usuario"
}
```

---

#### `GET /{finca_id}`
Obtiene una finca por ID.

**Auth:** cualquier token  
**Respuesta 200:** `FincaOut` | **404** si no existe.

---

#### `PATCH /{finca_id}`
Actualiza datos de la finca.

**Auth:** ADMIN, AUDITOR

---

#### `DELETE /{finca_id}`
Elimina una finca.

**Auth:** ADMIN  
**Respuesta 200:** `{"message": "Finca eliminada correctamente"}`

---

### 6.6 Auditoría GEE

**Prefijo:** `/api/v1/auditoria`

#### `GET /`
Lista todas las auditorías.

**Auth:** ADMIN, AUDITOR

---

#### `POST /`
Registra el resultado de una auditoría GEE. Al crear una auditoría:
1. Se almacena el resultado (`APROBADO` / `RECHAZADO`).
2. El campo `estado` del expediente se actualiza automáticamente.
3. Se agrega un evento al historial de trazabilidad del expediente.
4. `ejecutado_por` toma el valor del `sub` del token si no se especifica.

**Auth:** ADMIN, AUDITOR

**Body:**
```json
{
  "expediente_id": "uuid-del-expediente",
  "resultado": "APROBADO",
  "deforestacion_detectada": false,
  "fuente": "Google Earth Engine",
  "observaciones": "Sin hallazgos de deforestación en el período analizado",
  "fecha_corte": "2024-12-31T00:00:00Z"
}
```

**Respuesta 201:** objeto `AuditoriaOut`  
**404** si el expediente no existe.

---

#### `GET /expediente/{expediente_id}`
Lista todas las auditorías de un expediente.

**Auth:** cualquier token

---

#### `GET /{auditoria_id}`
Obtiene una auditoría por ID.

**Auth:** cualquier token

---

### 6.7 Certificados DDS

**Prefijo:** `/api/v1/certificados`

#### `GET /`
Lista todos los certificados.

**Auth:** ADMIN, AUDITOR

---

#### `POST /`
Genera un certificado DDS. Reglas de negocio:
1. El expediente debe existir.
2. El expediente debe tener al menos una auditoría GEE con `resultado = APROBADO` (HTTP 400 si no).
3. El código se genera automáticamente: `DDS-{año}-{8 caracteres hex en mayúsculas}`.
4. Se registra un evento en el historial del expediente.

**Auth:** ADMIN, AUDITOR

**Body:**
```json
{
  "expediente_id": "uuid-del-expediente",
  "fecha_vencimiento": "2026-12-31T00:00:00Z",
  "url_documento": "https://storage.ejemplo.com/cert-123.pdf"
}
```

**Respuesta 201:** objeto `CertificadoOut`  
**400** si no existe auditoría APROBADA.  
**404** si el expediente no existe.

---

#### `GET /expediente/{expediente_id}`
Lista los certificados de un expediente.

**Auth:** cualquier token

---

#### `GET /{certificado_id}`
Obtiene un certificado por ID.

**Auth:** cualquier token

---

#### `PATCH /{certificado_id}/revocar`
Revoca un certificado (cambia estado a `REVOCADO`).

**Auth:** ADMIN  
**Respuesta 200:** objeto `CertificadoOut` con `estado = REVOCADO`

---

## 7. Enums y Valores Permitidos

Todos los valores deben enviarse en **MAYÚSCULAS**.

| Enum | Valores válidos |
|---|---|
| `GeneroEnum` | `MASCULINO`, `FEMENINO` |
| `TenenciaEnum` | `PROPIA`, `POSESION`, `ARRENDAMIENTO` |
| `EstadoEnum` (expediente) | `PENDIENTE`, `EN_PROCESO`, `APROBADO`, `RECHAZADO` |
| `RolNombreEnum` | `ADMIN`, `AUDITOR`, `CLIENTE` |
| `ResultadoAuditoriaEnum` | `APROBADO`, `RECHAZADO` |
| `EstadoCertificadoEnum` | `VIGENTE`, `VENCIDO`, `REVOCADO` |

> Los enums son validados por Pydantic. Enviar un valor no listado devuelve **HTTP 422 Unprocessable Entity**.

---

## 8. Lógica de Negocio

### Generación del EUDR ID
Al crear un expediente, se genera automáticamente un identificador único:
```
uuidv4-{8 chars hex}-{5 chars hex}
Ejemplo: uuidv4-2A43E5A5-3EC5C
```

### Trazabilidad automática
El historial se actualiza automáticamente en los siguientes eventos:

| Evento | Acción registrada |
|---|---|
| Creación del expediente | `"Expediente creado"` |
| Actualización del expediente | `"Expediente actualizado"` |
| Registro de auditoría GEE | `"Auditoría GEE ejecutada"` |
| Registro de datos agroambientales | `"Datos agroambientales registrados"` |
| Emisión de certificado DDS | `"Certificado DDS generado"` |

### Ciclo de vida del estado del expediente

```
PENDIENTE ──► EN_PROCESO ──► APROBADO
                         └──► RECHAZADO
```

El estado cambia automáticamente al registrar una auditoría GEE:
- `resultado = APROBADO` → `expediente.estado = APROBADO`
- `resultado = RECHAZADO` → `expediente.estado = RECHAZADO`

### Requisito para emitir certificado DDS

```
expediente.auditorias.find(resultado == "APROBADO") → requerido
     ↓ NO existe
HTTP 400: "El expediente requiere una auditoría GEE con resultado APROBADO"
     ↓ SÍ existe
Certificado generado con código DDS-{año}-{hex}
```

### Hash de contraseñas
Las contraseñas se hashean con `bcrypt` (salt automático):
```python
bcrypt.hashpw(password.encode(), bcrypt.gensalt())
```

### Soft Delete de usuarios
Los usuarios no se eliminan físicamente. El endpoint `DELETE /usuarios/{id}` solo establece `activo = false`.

---

## 9. Configuración del Entorno

Crear un archivo `.env` en la raíz del proyecto con base en `.env.example`:

```env
# Base de datos
DATABASE_URL=file:./geoguard.db

# JWT — clave compartida con auth-service para validación local (HS256)
SECRET_KEY="EUDR-Auth-2026-v1-xK9mPqRz2wL7nBv4Jd8Sf3Gh5Tq1Wx0Zy"

# Comunicación interna entre microservicios (S2S)
INTERNAL_API_KEY="EUDR-Audit-Internal-9f8d7c6b5a4e3w2q1o0pLKmJnHgBfDcSa"
```

> **IMPORTANTE:** el archivo `.env` nunca debe subirse al repositorio. Está en `.gitignore`.

---

## 10. Instalación y Puesta en Marcha

### Requisitos
- Python 3.11+
- Node.js (requerido por Prisma CLI para generar el cliente)

### Pasos

```bash
# 1. Clonar el repositorio
git clone https://github.com/KevinSarango1/backend-kevin-sarango.git
cd backend-kevin-sarango/backend-kevin-sarango

# 2. Crear y activar entorno virtual
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Crear archivo .env
copy .env.example .env
# Editar .env con las claves reales

# 5. Generar cliente Prisma y crear la base de datos
python init_db.py

# 6. Iniciar el servidor
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Acceso a la documentación interactiva
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Ejecutar los tests
```bash
pip install requests
python test_api.py
# Resultado esperado: TOTAL: 42 | PASS: 42 | FAIL: 0
```

---

## 11. Dependencias

| Paquete | Versión | Uso |
|---|---|---|
| `fastapi` | 0.111.0 | Framework web principal |
| `uvicorn[standard]` | 0.29.0 | Servidor ASGI |
| `prisma` | 0.13.1 | ORM — cliente Python generado desde `schema.prisma` |
| `python-dotenv` | 1.0.1 | Carga de variables de entorno desde `.env` |
| `pydantic` | 2.7.1 | Validación de datos y serialización |
| `bcrypt` | 4.1.3 | Hash de contraseñas |
| `python-jose[cryptography]` | 3.3.0 | Validación local de tokens JWT (HS256) |
| `psycopg2-binary` | 2.9.9 | Driver PostgreSQL (para migración futura a producción) |

---

*Documentación generada para GeoGuard EUDR Backend v2.0.0*
