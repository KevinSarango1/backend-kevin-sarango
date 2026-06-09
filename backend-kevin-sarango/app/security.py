from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from dotenv import load_dotenv
import os

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "")
ALGORITHM = "HS256"

_bearer = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> dict:
    """
    Valida el JWT localmente con la SECRET_KEY compartida.
    Retorna el payload completo: {"sub", "role", "session_token", "exp"}.
    Lanza HTTP 401 si el token es inválido, mal formado o expirado.
    """
    try:
        payload = jwt.decode(
            credentials.credentials,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_roles(*allowed: str):
    """
    Dependency factory para RBAC.
    Uso: current_user: dict = Depends(require_roles("ADMIN", "AUDITOR"))
    Lanza HTTP 403 si el rol del token no está en la lista permitida.
    """
    def _guard(current_user: dict = Depends(get_current_user)) -> dict:
        if current_user.get("role") not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Rol '{current_user.get('role')}' no tiene permisos para esta acción",
            )
        return current_user
    return _guard
