# GeoGuard EUDR — Backend Kevin Sarango

Backend FastAPI para el módulo de **Gestión de Expedientes, Trazabilidad e Información Agroambiental** del sistema GeoGuard EUDR.

## Módulos cubiertos

| Módulo | Tarea |
|--------|-------|
| Gestión | Gestión de expedientes y trazabilidad |
| Cliente | Información agroambiental |

## Endpoints principales

### Expedientes (`/api/v1/expedientes`)
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/` | Listar expedientes (filtros: estado, organización) |
| POST | `/` | Crear nuevo expediente |
| GET | `/{id}` | Obtener expediente por ID |
| GET | `/eudr/{eudr_id}` | Buscar por EUDR ID |
| PATCH | `/{id}` | Actualizar expediente |
| DELETE | `/{id}` | Eliminar expediente |
| GET | `/{id}/historial` | Ver historial de trazabilidad |
| POST | `/{id}/historial` | Agregar evento al historial |

### Agroambiental (`/api/v1/agroambiental`)
| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/{expediente_id}` | Obtener datos agroambientales |
| POST | `/{expediente_id}` | Registrar datos agroambientales |
| PUT | `/{expediente_id}/{dato_id}` | Actualizar datos agroambientales |
| GET | `/resumen/carbono` | Resumen de stock de carbono por finca |

## Instalación local

```bash
# 1. Clonar el repo
git clone https://github.com/TU_USUARIO/backend-kevin-sarango.git
cd backend-kevin-sarango

# 2. Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales de Supabase

# 5. Levantar el servidor
uvicorn app.main:app --reload
```

La API estará disponible en: http://localhost:8000

Documentación automática: http://localhost:8000/docs

## Base de Datos

- **Supabase** (PostgreSQL)
- Las tablas se crean automáticamente al iniciar la app

## Stack

- Python 3.11+
- FastAPI
- SQLAlchemy
- PostgreSQL / Supabase
- Pydantic v2
