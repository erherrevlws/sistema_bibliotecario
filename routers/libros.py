# Endpoints CRUD de Libros --- Catálogo
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List, Optional
from core.database import get_session
from core.dependencias import get_current_user, require_roles
from models.models import Libro, Autor, Categoria, Prestamo, Usuario
from schemas.schemas import LibroCreate, LibroUpdate, LibroRead

router = APIRouter(prefix="/libros", tags=["Catálogo de Libros"])

@router.post("/", response_model=LibroRead, status_code=status.HTTP_201_CREATED)
def crear_libro(
    libro_in: LibroCreate,
    session: Session = Depends(get_session),
    current_user: Usuario = Depends(require_roles(["Administrador", "Bibliotecario"]))
):
    """
    Crea un nuevo libro en el catálogo.
    Requiere rol de Administrador o Bibliotecario.
    Valida la existencia del Autor y de la Categoría, así como la unicidad del ISBN.
    """
    # Validar autor
    autor = session.get(Autor, libro_in.autor_id)
    if not autor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="El autor especificado no existe"
        )

    # Validar categoría
    categoria = session.get(Categoria, libro_in.categoria_id)
    if not categoria:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="La categoría especificada no existe"
        )

    # Validar unicidad del ISBN
    existente = session.exec(
        select(Libro).where(Libro.isbn == libro_in.isbn)
    ).first()
    if existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El código ISBN ya se encuentra registrado"
        )

    nuevo_libro = Libro(
        titulo=libro_in.titulo,
        isbn=libro_in.isbn,
        disponible=True,
        is_active=True,
        autor_id=libro_in.autor_id,
        categoria_id=libro_in.categoria_id
    )
    session.add(nuevo_libro)
    session.commit()
    session.refresh(nuevo_libro)
    return nuevo_libro

@router.get("/", response_model=List[LibroRead])
def listar_libros(
    titulo: Optional[str] = None,
    autor_id: Optional[int] = None,
    categoria_id: Optional[int] = None,
    disponible: Optional[bool] = None,
    session: Session = Depends(get_session),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Consulta el catálogo de libros activos con filtros opcionales.
    Disponible para cualquier usuario autenticado.
    """
    statement = select(Libro).where(Libro.is_active == True)
    if titulo:
        statement = statement.where(Libro.titulo.contains(titulo))
    if autor_id is not None:
        statement = statement.where(Libro.autor_id == autor_id)
    if categoria_id is not None:
        statement = statement.where(Libro.categoria_id == categoria_id)
    if disponible is not None:
        statement = statement.where(Libro.disponible == disponible)

    return session.exec(statement).all()

@router.get("/{libro_id}", response_model=LibroRead)
def obtener_libro(
    libro_id: int,
    session: Session = Depends(get_session),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtiene el detalle de un libro por su ID."""
    libro = session.get(Libro, libro_id)
    if not libro or not libro.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Libro no encontrado en el catálogo"
        )
    return libro

@router.put("/{libro_id}", response_model=LibroRead)
def actualizar_libro(
    libro_id: int,
    libro_in: LibroUpdate,
    session: Session = Depends(get_session),
    current_user: Usuario = Depends(require_roles(["Administrador", "Bibliotecario"]))
):
    """
    Actualiza la información de un libro existente en el catálogo.
    Requiere rol de Administrador o Bibliotecario.
    """
    libro = session.get(Libro, libro_id)
    if not libro or not libro.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Libro no encontrado en el catálogo"
        )

    if libro_in.isbn and libro_in.isbn != libro.isbn:
        isbn_duplicado = session.exec(
            select(Libro).where(Libro.isbn == libro_in.isbn, Libro.id != libro_id, Libro.is_active == True)
        ).first()
        if isbn_duplicado:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El código ISBN ya está registrado para otro libro"
            )
        libro.isbn = libro_in.isbn

    if libro_in.autor_id is not None:
        autor = session.get(Autor, libro_in.autor_id)
        if not autor:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="El autor especificado no existe")
        libro.autor_id = libro_in.autor_id

    if libro_in.categoria_id is not None:
        categoria = session.get(Categoria, libro_in.categoria_id)
        if not categoria:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="La categoría especificada no existe")
        libro.categoria_id = libro_in.categoria_id

    if libro_in.titulo is not None:
        libro.titulo = libro_in.titulo
    if libro_in.disponible is not None:
        libro.disponible = libro_in.disponible

    session.add(libro)
    session.commit()
    session.refresh(libro)
    return libro

@router.delete("/{libro_id}", status_code=status.HTTP_200_OK)
def eliminar_libro(
    libro_id: int,
    session: Session = Depends(get_session),
    current_user: Usuario = Depends(require_roles(["Administrador", "Bibliotecario"]))
):
    """
    Elimina un libro del catálogo mediante Soft Delete is_active = False.
    Impide la eliminación si el libro tiene un préstamo activo en curso.
    """
    libro = session.get(Libro, libro_id)
    if not libro or not libro.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Libro no encontrado en el catálogo"
        )

    # Verificar si está actualmente prestado
    prestamo_activo = session.exec(
        select(Prestamo).where(Prestamo.libro_id == libro_id, Prestamo.estado == "ACTIVO")
    ).first()
    if prestamo_activo:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede eliminar el libro porque se encuentra actualmente prestado"
        )

    # Aplicar Soft Delete para mantener el historial de préstamos pasados
    libro.is_active = False
    libro.disponible = False
    session.add(libro)
    session.commit()
    return {"mensaje": f"Libro '{libro.titulo}' eliminado del catálogo exitosamente"}
