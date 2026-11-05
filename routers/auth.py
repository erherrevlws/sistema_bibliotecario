# Endpoints de Autenticación
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from core.database import get_session
from core.security import verify_password, create_access_token
from models.models import Usuario, Rol
from schemas.schemas import Token

router = APIRouter(prefix="/auth", tags=["Autenticación"])

@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales incorrectas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Regla 5: Las credenciales incorrectas no deben revelar si el usuario existe ni exponer información sensible
    statement = select(Usuario).where(Usuario.email == form_data.username, Usuario.is_active == True)
    usuario = session.exec(statement).first()
    
    if not usuario:
        raise credentials_exception
        
    if not verify_password(form_data.password, usuario.hashed_password):
        raise credentials_exception
        
    # Obtener el nombre del rol
    rol = session.get(Rol, usuario.rol_id) if usuario.rol_id else None
    rol_nombre = rol.nombre if rol else "Usuario"

    # Generar el Token JWT con subject y rol
    access_token = create_access_token(
        data={"sub": usuario.email, "rol": rol_nombre}
    )
    
    return {"access_token": access_token, "token_type": "bearer"}
