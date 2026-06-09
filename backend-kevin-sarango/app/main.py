from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import db
from app.routers import expedientes, agroambiental, usuarios, roles, fincas, auditoria, certificados


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.connect()
    yield
    db.disconnect()


app = FastAPI(
    title="GeoGuard EUDR - Backend Kevin Sarango",
    description="API para Gestión de Expedientes, Trazabilidad e Información Agroambiental",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(expedientes.router,  prefix="/api/v1/expedientes",  tags=["Expedientes"])
app.include_router(agroambiental.router, prefix="/api/v1/agroambiental", tags=["Agroambiental"])
app.include_router(usuarios.router,     prefix="/api/v1/usuarios",     tags=["Usuarios"])
app.include_router(roles.router,        prefix="/api/v1/roles",        tags=["Roles"])
app.include_router(fincas.router,       prefix="/api/v1/fincas",       tags=["Fincas"])
app.include_router(auditoria.router,    prefix="/api/v1/auditoria",    tags=["Auditoría GEE"])
app.include_router(certificados.router, prefix="/api/v1/certificados", tags=["Certificados DDS"])


@app.get("/")
def root():
    return {"message": "GeoGuard EUDR API - Kevin Sarango", "version": "2.0.0"}


@app.get("/health")
def health():
    return {"status": "ok"}
