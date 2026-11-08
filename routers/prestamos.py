# Endpoints de Negocio - Préstamos y Devoluciones
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List, Optional
from datetime import date, timedelta
from core.database import get_session
from core.dependencias import get_current_user, require_roles
from models.models import Prestamo, Libro, Usuario, Rol
from schemas.schemas import PrestamoCreate, PrestamoRead, DevolucionResponse

router = APIRouter(prefix="/prestamos", tags=["Préstamos y Devoluciones"])

@router.post("/", response_model=PrestamoRead, status_code=status.HTTP_201_CREATED)
def crear_prestamo(
    prestamo_in: PrestamoCreate,
    session: Session = Depends(get_session),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Registra un préstamo bibliotecario aplicando las reglas de negocio.
    """
    #  Determinar el usuario del préstamo
    rol_actual = session.get(Rol, current_user.rol_id)
    rol_nombre = rol_actual.nombre if rol_actual else "Usuario"

    if rol_nombre in ["Administrador", "Bibliotecario"] and prestamo_in.usuario_id is not None:
        target_usuario_id = prestamo_in.usuario_id
    else:
        target_usuario_id = current_user.id

    # Validar que el usuario exista y esté activo
    usuario_prestamo = session.get(Usuario, target_usuario_id)
    if not usuario_prestamo or not usuario_prestamo.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El usuario destinatario del préstamo no existe o se encuentra inactivo"
        )

    #  Validar existencia del libro
    libro = session.get(Libro, prestamo_in.libro_id)
    if not libro or not libro.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El libro solicitado no existe en el catálogo activo"
        )

    #  Validar disponibilidad
    if not libro.disponible:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El libro solicitado no se encuentra disponible para préstamo"
        )

    #  Calcular fechas
    dias = prestamo_in.dias_prestamo if prestamo_in.dias_prestamo else 14
    hoy = date.today()
    fecha_esperada = hoy + timedelta(days=dias)

    #  Crear el registro de préstamo y actualizar disponibilidad del libro
    nuevo_prestamo = Prestamo(
        usuario_id=target_usuario_id,
        libro_id=libro.id,
        fecha_prestamo=hoy,
        fecha_devolucion_esperada=fecha_esperada,
        estado="ACTIVO"
    )
    libro.disponible = False

    session.add(nuevo_prestamo)
    session.add(libro)
    session.commit()
    session.refresh(nuevo_prestamo)
    return nuevo_prestamo

@router.get("/", response_model=List[PrestamoRead])
def listar_prestamos(
    estado: Optional[str] = None,
    usuario_id: Optional[int] = None,
    session: Session = Depends(get_session),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Consulta préstamos con filtros opcionales.
    - Usuarios regulares solo ven sus propios préstamos.
    - Administradores y Bibliotecarios pueden consultar todos o filtrar por usuario.
    """
    rol = session.get(Rol, current_user.rol_id)
    rol_nombre = rol.nombre if rol else "Usuario"

    statement = select(Prestamo)

    if rol_nombre not in ["Administrador", "Bibliotecario"]:
        statement = statement.where(Prestamo.usuario_id == current_user.id)
    elif usuario_id is not None:
        statement = statement.where(Prestamo.usuario_id == usuario_id)

    if estado:
        statement = statement.where(Prestamo.estado == estado.upper())

    return session.exec(statement).all()

@router.get("/activos", response_model=List[PrestamoRead])
def listar_prestamos_activos(
    session: Session = Depends(get_session),
    current_user: Usuario = Depends(get_current_user)
):
    """Lista todos los préstamos que continúan en estado ACTIVO."""
    rol = session.get(Rol, current_user.rol_id)
    rol_nombre = rol.nombre if rol else "Usuario"

    statement = select(Prestamo).where(Prestamo.estado == "ACTIVO")
    if rol_nombre not in ["Administrador", "Bibliotecario"]:
        statement = statement.where(Prestamo.usuario_id == current_user.id)

    return session.exec(statement).all()

@router.get("/{prestamo_id}", response_model=PrestamoRead)
def obtener_prestamo(
    prestamo_id: int,
    session: Session = Depends(get_session),
    current_user: Usuario = Depends(get_current_user)
):
    """Consulta el detalle de un préstamo específico."""
    prestamo = session.get(Prestamo, prestamo_id)
    if not prestamo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Préstamo no encontrado"
        )

    rol = session.get(Rol, current_user.rol_id)
    rol_nombre = rol.nombre if rol else "Usuario"

    if rol_nombre not in ["Administrador", "Bibliotecario"] and prestamo.usuario_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permiso para consultar este préstamo"
        )

    return prestamo

@router.post("/{prestamo_id}/devolver", response_model=DevolucionResponse)
def registrar_devolucion(
    prestamo_id: int,
    session: Session = Depends(get_session),
    current_user: Usuario = Depends(require_roles(["Administrador", "Bibliotecario"]))
):
    """
    Registra la devolución de un libro prestado.
    - El libro vuelve a estar disponible .
    - El préstamo pasa a estado 'DEVUELTO' con su fecha real de entrega.
    """
    prestamo = session.get(Prestamo, prestamo_id)
    if not prestamo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Préstamo no encontrado"
        )

    if prestamo.estado == "DEVUELTO":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El libro de este préstamo ya fue devuelto previamente"
        )

    libro = session.get(Libro, prestamo.libro_id)
    if not libro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El libro asociado a este préstamo no existe"
        )

    # Actualizar estado del préstamo
    prestamo.estado = "DEVUELTO"
    prestamo.fecha_devolucion_real = date.today()

    # El libro vuelve a estar disponible
    libro.disponible = True

    session.add(prestamo)
    session.add(libro)
    session.commit()
    session.refresh(prestamo)

    return DevolucionResponse(
        mensaje=f"Devolución registrada exitosamente. El libro '{libro.titulo}' vuelve a estar disponible.",
        prestamo=prestamo
    )
