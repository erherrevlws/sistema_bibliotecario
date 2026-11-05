from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlmodel import Session, select
from core.config import SECRET_KEY, ALGORITHM
from core.database import get_session
from models.models import Usuario, Rol
from schemas.schemas import TokenData

# Define el endpoint desde el cual Swagger UI capturará el token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session)
) -> Usuario:
    """Extrae y valida el usuario actual desde el Token JWT."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales o el token ha expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = TokenData(email=email)
    except JWTError:
        raise credentials_exception

    statement = select(Usuario).where(Usuario.email == token_data.email, Usuario.is_active == True)
    usuario = session.exec(statement).first()
    if usuario is None:
        raise credentials_exception
    return usuario

def require_roles(roles_permitidos: list[str]):
    """Verifica si el usuario autenticado posee uno de los roles autorizados (RBAC)."""
    def role_checker(
        usuario_actual: Usuario = Depends(get_current_user),
        session: Session = Depends(get_session)
    ) -> Usuario:
        rol = session.get(Rol, usuario_actual.rol_id) if usuario_actual.rol_id else None
        if not rol or rol.nombre not in roles_permitidos:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No posees los privilegios requeridos para ejecutar esta operación"
            )
        return usuario_actual
    return role_checker
