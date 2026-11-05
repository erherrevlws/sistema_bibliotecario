# Endpoints para Autores
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List, Optional
from core.database import get_session
from core.dependencias import get_current_user, require_roles
from models.models import Autor, Libro, Usuario
from schemas.schemas import AutorCreate, AutorUpdate, AutorRead

router = APIRouter(prefix="/autores", tags=["Autores"])

@router.post("/", response_model=AutorRead, status_code=status.HTTP_201_CREATED)
def crear_autor(
    autor_in: AutorCreate,
    session: Session = Depends(get_session),
    current_user: Usuario = Depends(require_roles(["Administrador", "Bibliotecario"]))
):
    """Crea un nuevo autor (Solo Administrador y Bibliotecario)."""
    autor = Autor.from_orm(autor_in)
    session.add(autor)
    session.commit()
    session.refresh(autor)
    return autor

@router.get("/", response_model=List[AutorRead])
def listar_autores(
    nombre: Optional[str] = None,
    session: Session = Depends(get_session),
    current_user: Usuario = Depends(get_current_user)
):
    """Lista todos los autores registrados con filtro opcional por nombre."""
    statement = select(Autor)
    if nombre:
        statement = statement.where(Autor.nombre.contains(nombre))
    return session.exec(statement).all()

@router.get("/{autor_id}", response_model=AutorRead)
def obtener_autor(
    autor_id: int,
    session: Session = Depends(get_session),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtiene el detalle de un autor."""
    autor = session.get(Autor, autor_id)
    if not autor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Autor no encontrado"
        )
    return autor

@router.put("/{autor_id}", response_model=AutorRead)
def actualizar_autor(
    autor_id: int,
    autor_in: AutorUpdate,
    session: Session = Depends(get_session),
    current_user: Usuario = Depends(require_roles(["Administrador", "Bibliotecario"]))
):
    """Actualiza datos de un autor."""
    autor = session.get(Autor, autor_id)
    if not autor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Autor no encontrado"
        )
        
    if autor_in.nombre is not None:
        autor.nombre = autor_in.nombre
    if autor_in.nacionalidad is not None:
        autor.nacionalidad = autor_in.nacionalidad
    if autor_in.fecha_nacimiento is not None:
        autor.fecha_nacimiento = autor_in.fecha_nacimiento
    if autor_in.biografia is not None:
        autor.biografia = autor_in.biografia

    session.add(autor)
    session.commit()
    session.refresh(autor)
    return autor

@router.delete("/{autor_id}", status_code=status.HTTP_200_OK)
def eliminar_autor(
    autor_id: int,
    session: Session = Depends(get_session),
    current_user: Usuario = Depends(require_roles(["Administrador"]))
):
    """
    Elimina un autor verificando integridad referencial (no tener libros activos asociados).
    """
    autor = session.get(Autor, autor_id)
    if not autor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Autor no encontrado"
        )
        
    libros_asociados = session.exec(
        select(Libro).where(Libro.autor_id == autor_id, Libro.is_active == True)
    ).first()
    if libros_asociados:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede eliminar el autor porque tiene libros activos asociados en el catálogo"
        )
        
    session.delete(autor)
    session.commit()
    return {"mensaje": f"Autor '{autor.nombre}' eliminado correctamente"}
