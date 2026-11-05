# Endpoints CRUD de Usuarios y Roles
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List, Optional
from core.database import get_session
from core.security import get_password_hash
from core.dependencias import get_current_user, require_roles
from models.models import Usuario, Rol, Prestamo
from schemas.schemas import UsuarioCreate, UsuarioUpdate, UsuarioRead, RolRead

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])

@router.get("/roles", response_model=List[RolRead])
def listar_roles(
    session: Session = Depends(get_session),
    current_user: Usuario = Depends(require_roles(["Administrador", "Bibliotecario"]))
):
    """Lista todos los roles disponibles en el sistema."""
    return session.exec(select(Rol)).all()

@router.post("/registro", response_model=UsuarioRead, status_code=status.HTTP_201_CREATED)
def autoregistro_usuario(
    usuario_in: UsuarioCreate,
    session: Session = Depends(get_session)
):
    """Permite el autoregistro de un nuevo usuario con rol predeterminado 'Usuario'."""
    # Validar que el email no esté registrado
    existente = session.exec(select(Usuario).where(Usuario.email == usuario_in.email)).first()
    if existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo electrónico ya se encuentra registrado"
        )
    
    # Asignar rol 'Usuario'
    rol_usuario = session.exec(select(Rol).where(Rol.nombre == "Usuario")).first()
    if not rol_usuario:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="El rol predeterminado de Usuario no está configurado"
        )
        
    nuevo_usuario = Usuario(
        nombre=usuario_in.nombre,
        email=usuario_in.email,
        hashed_password=get_password_hash(usuario_in.password),
        rol_id=rol_usuario.id,
        is_active=True
    )
    session.add(nuevo_usuario)
    session.commit()
    session.refresh(nuevo_usuario)
    return nuevo_usuario

@router.post("/", response_model=UsuarioRead, status_code=status.HTTP_201_CREATED)
def crear_usuario_admin(
    usuario_in: UsuarioCreate,
    session: Session = Depends(get_session),
    current_user: Usuario = Depends(require_roles(["Administrador"]))
):
    """Crea un nuevo usuario con rol explícito (Solo Administradores)."""
    existente = session.exec(select(Usuario).where(Usuario.email == usuario_in.email)).first()
    if existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo electrónico ya se encuentra registrado"
        )
        
    rol_id = usuario_in.rol_id
    if not rol_id:
        rol_usuario = session.exec(select(Rol).where(Rol.nombre == "Usuario")).first()
        rol_id = rol_usuario.id if rol_usuario else None
    else:
        rol = session.get(Rol, rol_id)
        if not rol:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="El id de rol especificado no existe"
            )

    nuevo_usuario = Usuario(
        nombre=usuario_in.nombre,
        email=usuario_in.email,
        hashed_password=get_password_hash(usuario_in.password),
        rol_id=rol_id,
        is_active=True
    )
    session.add(nuevo_usuario)
    session.commit()
    session.refresh(nuevo_usuario)
    return nuevo_usuario

@router.get("/me", response_model=UsuarioRead)
def obtener_perfil(current_user: Usuario = Depends(get_current_user)):
    """Retorna los datos del usuario autenticado."""
    return current_user

@router.get("/", response_model=List[UsuarioRead])
def listar_usuarios(
    session: Session = Depends(get_session),
    current_user: Usuario = Depends(require_roles(["Administrador", "Bibliotecario"]))
):
    """Lista todos los usuarios registrados (Solo Administradores y Bibliotecarios)."""
    statement = select(Usuario).where(Usuario.is_active == True)
    return session.exec(statement).all()

@router.get("/{usuario_id}", response_model=UsuarioRead)
def obtener_usuario_por_id(
    usuario_id: int,
    session: Session = Depends(get_session),
    current_user: Usuario = Depends(require_roles(["Administrador", "Bibliotecario"]))
):
    """Consulta los datos de un usuario por su ID (Solo Administradores y Bibliotecarios)."""
    usuario = session.get(Usuario, usuario_id)
    if not usuario or not usuario.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    return usuario

@router.put("/{usuario_id}", response_model=UsuarioRead)
def actualizar_usuario(
    usuario_id: int,
    usuario_in: UsuarioUpdate,
    session: Session = Depends(get_session),
    current_user: Usuario = Depends(require_roles(["Administrador"]))
):
    """Actualiza datos de un usuario (Solo Administradores)."""
    usuario = session.get(Usuario, usuario_id)
    if not usuario or not usuario.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )

    if usuario_in.email and usuario_in.email != usuario.email:
        existente = session.exec(select(Usuario).where(Usuario.email == usuario_in.email)).first()
        if existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El correo electrónico ya está en uso por otro usuario"
            )
        usuario.email = usuario_in.email

    if usuario_in.nombre is not None:
        usuario.nombre = usuario_in.nombre
    if usuario_in.password:
        usuario.hashed_password = get_password_hash(usuario_in.password)
    if usuario_in.rol_id is not None:
        rol = session.get(Rol, usuario_in.rol_id)
        if not rol:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="El id de rol especificado no existe"
            )
        usuario.rol_id = usuario_in.rol_id
    if usuario_in.is_active is not None:
        usuario.is_active = usuario_in.is_active

    session.add(usuario)
    session.commit()
    session.refresh(usuario)
    return usuario

@router.delete("/{usuario_id}", status_code=status.HTTP_200_OK)
def desactivar_usuario(
    usuario_id: int,
    session: Session = Depends(get_session),
    current_user: Usuario = Depends(require_roles(["Administrador"]))
):
    """
    Desactiva a un usuario (Soft Delete).
    Regla 7: Se verifica integridad referencial impidiendo la eliminación si tiene préstamos activos.
    """
    usuario = session.get(Usuario, usuario_id)
    if not usuario or not usuario.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )

    if usuario.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes desactivar tu propia cuenta administradora"
        )

    # Verificar si tiene préstamos activos
    prestamos_activos = session.exec(
        select(Prestamo).where(Prestamo.usuario_id == usuario_id, Prestamo.estado == "ACTIVO")
    ).first()
    
    if prestamos_activos:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede eliminar el usuario porque tiene préstamos activos pendientes de devolución"
        )

    usuario.is_active = False
    session.add(usuario)
    session.commit()
    return {"mensaje": f"Usuario {usuario.email} desactivado correctamente"}
