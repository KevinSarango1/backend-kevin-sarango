from app.database import engine, Base
from app.models.models import (  # noqa: F401 - importar todos los modelos para registrarlos
    Expediente,
    DatoAgroambiental,
    HistorialTrazabilidad,
    Rol,
    Usuario,
    Finca,
    AuditoriaGEE,
    CertificadoDDS,
)

def init_db():
    Base.metadata.create_all(bind=engine)
    print("Tablas creadas correctamente en la base de datos.")

if __name__ == "__main__":
    init_db()
