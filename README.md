# GeoGuard EUDR — Backend Kevin Sarango

Backend **FastAPI** para el módulo de **Gestión de Expedientes, Trazabilidad e Información Agroambiental** del sistema GeoGuard EUDR.

## Módulos cubiertos

| Módulo | Tarea asignada |
|--------|----------------|
| Gestión | Gestión de expedientes y trazabilidad |
| Cliente | Información agroambiental |

---

## Cómo funciona

### Autenticación y autorización

Cada request debe incluir un token JWT en el header:

```
Authorization: Bearer <token>
```

El backend **valida el token localmente** (sin llamar a ningún servicio externo) usando la clave compartida `SECRET_KEY`. Del token extrae el `role` del usuario y decide si puede acceder al endpoint.

### Roles disponibles

| Rol | Descripción |
|-----|-------------|
| `SUPER_ADMIN` | Acceso total al sistema |
| `TENANT_ADMIN` | Administrador de organización |
| `TECNICO_CAMPO` | Crea y edita expedientes y datos |
| `AUDITOR_INTERNO` | Ejecuta auditorías GEE y genera certificados |
| `AUDITOR_EXTERNO` | Solo lectura de auditorías y certificados |
| `CLIENTE` | Solo lectura general |

### Flujo completo de un expediente

```
1. Crear expediente (TECNICO_CAMPO)
        ↓
   Estado: PENDIENTE
   Historial: entrada automática
   Datos agroambientales: registrados

2. Auditoría GEE (AUDITOR_INTERNO)
        ↓
   Estado: APROBADO o RECHAZADO
   Historial: entrada automática

3. Certificado DDS (AUDITOR_INTERNO)
        ↓
   Solo si hay auditoría APROBADA
   Código: DDS-2026-XXXXXXXX
   Historial: entrada automática
```

---

## Endpoints

### Expedientes `/api/v1/expedientes`

| Método | Ruta | Descripción | Roles |
|--------|------|-------------|-------|
| GET | `/` | Listar expedientes | Todos |
| POST | `/` | Crear expediente | SUPER_ADMIN, TENANT_ADMIN, TECNICO_CAMPO |
| GET | `/{id}` | Obtener por ID | Todos |
| GET | `/eudr/{eudr_id}` | Buscar por EUDR ID | Todos |
| PATCH | `/{id}` | Actualizar | SUPER_ADMIN, TENANT_ADMIN, TECNICO_CAMPO |
| DELETE | `/{id}` | Eliminar | SUPER_ADMIN, TENANT_ADMIN |
| GET | `/{id}/historial` | Ver trazabilidad | Todos |
| POST | `/{id}/historial` | Agregar evento | SUPER_ADMIN, TENANT_ADMIN, TECNICO_CAMPO |

### Agroambiental `/api/v1/agroambiental`

| Método | Ruta | Descripción | Roles |
|--------|------|-------------|-------|
| GET | `/{expediente_id}` | Obtener datos | Todos |
| POST | `/{expediente_id}` | Registrar datos | SUPER_ADMIN, TENANT_ADMIN, TECNICO_CAMPO, AUDITOR_INTERNO |
| PUT | `/{expediente_id}/{dato_id}` | Actualizar datos | SUPER_ADMIN, TENANT_ADMIN, TECNICO_CAMPO, AUDITOR_INTERNO |
| GET | `/resumen/carbono` | Resumen de stock de carbono | Todos |

### Fincas `/api/v1/fincas`

| Método | Ruta | Descripción | Roles |
|--------|------|-------------|-------|
| GET | `/` | Listar fincas | Todos |
| POST | `/` | Crear finca | Todos |
| GET | `/{id}` | Obtener por ID | Todos |
| PATCH | `/{id}` | Actualizar | SUPER_ADMIN, TENANT_ADMIN, TECNICO_CAMPO |
| DELETE | `/{id}` | Eliminar | SUPER_ADMIN, TENANT_ADMIN |

### Auditoría GEE `/api/v1/auditoria`

| Método | Ruta | Descripción | Roles |
|--------|------|-------------|-------|
| GET | `/` | Listar auditorías | SUPER_ADMIN, TENANT_ADMIN, AUDITOR_INTERNO |
| POST | `/` | Registrar resultado | SUPER_ADMIN, TENANT_ADMIN, AUDITOR_INTERNO |
| GET | `/expediente/{id}` | Por expediente | Todos |
| GET | `/{id}` | Por ID | Todos |

### Certificados DDS `/api/v1/certificados`

| Método | Ruta | Descripción | Roles |
|--------|------|-------------|-------|
| GET | `/` | Listar certificados | SUPER_ADMIN, TENANT_ADMIN, AUDITOR_INTERNO, AUDITOR_EXTERNO |
| POST | `/` | Generar certificado | SUPER_ADMIN, TENANT_ADMIN, AUDITOR_INTERNO |
| GET | `/expediente/{id}` | Por expediente | Todos |
| GET | `/{id}` | Por ID | Todos |
| PATCH | `/{id}/revocar` | Revocar | SUPER_ADMIN, TENANT_ADMIN |

### Usuarios `/api/v1/usuarios`

| Método | Ruta | Descripción | Roles |
|--------|------|-------------|-------|
| GET | `/` | Listar usuarios | SUPER_ADMIN, TENANT_ADMIN |
| POST | `/` | Crear usuario | SUPER_ADMIN, TENANT_ADMIN |
| PATCH | `/{id}` | Actualizar | SUPER_ADMIN, TENANT_ADMIN |
| DELETE | `/{id}` | Desactivar (soft delete) | SUPER_ADMIN, TENANT_ADMIN |

### Roles `/api/v1/roles`

| Método | Ruta | Descripción | Roles |
|--------|------|-------------|-------|
| GET | `/` | Listar roles | SUPER_ADMIN |
| POST | `/` | Crear rol | SUPER_ADMIN |
| DELETE | `/{id}` | Eliminar rol | SUPER_ADMIN |

---

## Instalación local

```bash
# 1. Clonar el repositorio
git clone https://github.com/KevinSarango1/backend-kevin-sarango.git
cd backend-kevin-sarango

# 2. Crear entorno virtual
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/Mac

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus valores

# 5. Generar cliente Prisma
python -m prisma generate

# 6. Levantar el servidor
uvicorn app.main:app --reload --port 8031
```

- API: `http://localhost:8031`
- Docs (Swagger): `http://localhost:8031/docs`
- Health check: `http://localhost:8031/health`

---

## Stack tecnológico

| Componente | Tecnología |
|------------|------------|
| Framework | FastAPI 0.111 |
| ORM | Prisma Client Python 0.13.1 |
| Base de datos | SQLite (archivo `geoguard.db`) |
| Autenticación | JWT HS256 — `python-jose` |
| Hashing de contraseñas | `bcrypt 4.1.3` |
| Validación | Pydantic v2 |
| Servidor | Uvicorn |
| Python | 3.11+ |

---

## Variables de entorno

Copia `.env.example` a `.env` y completa los valores:

```env
DATABASE_URL=file:./geoguard.db
SECRET_KEY="tu_clave_secreta_jwt"
INTERNAL_API_KEY="tu_clave_interna_s2s"
```

> **Nunca** subas el archivo `.env` al repositorio.
