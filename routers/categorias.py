# Endpoints para Categorías
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List, Optional
from core.database import get_session
from core.dependencias import get_current_user, require_roles
from models.models import Categoria, Libro, Usuario
from schemas.schemas import CategoriaCreate, CategoriaUpdate, CategoriaRead

router = APIRouter(prefix="/categorias", tags=["Categorías"])

@router.post("/", response_model=CategoriaRead, status_code=status.HTTP_201_CREATED)
def crear_categoria(
    categoria_in: CategoriaCreate,
    session: Session = Depends(get_session),
    current_user: Usuario = Depends(require_roles(["Administrador", "Bibliotecario"]))
):
    """Crea una nueva categoría."""
    existente = session.exec(select(Categoria).where(Categoria.nombre == categoria_in.nombre)).first()
    if existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe una categoría con ese nombre"
        )
    categoria = Categoria.from_orm(categoria_in)
    session.add(categoria)
    session.commit()
    session.refresh(categoria)
    return categoria

@router.get("/", response_model=List[CategoriaRead])
def listar_categorias(
    nombre: Optional[str] = None,
    session: Session = Depends(get_session),
    current_user: Usuario = Depends(get_current_user)
):
    """Lista las categorías registradas con filtro opcional por nombre."""
    statement = select(Categoria)
    if nombre:
        statement = statement.where(Categoria.nombre.contains(nombre))
    return session.exec(statement).all()

@router.get("/{categoria_id}", response_model=CategoriaRead)
def obtener_categoria(
    categoria_id: int,
    session: Session = Depends(get_session),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtiene el detalle de una categoría."""
    categoria = session.get(Categoria, categoria_id)
    if not categoria:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoría no encontrada"
        )
    return categoria

@router.put("/{categoria_id}", response_model=CategoriaRead)
def actualizar_categoria(
    categoria_id: int,
    categoria_in: CategoriaUpdate,
    session: Session = Depends(get_session),
    current_user: Usuario = Depends(require_roles(["Administrador", "Bibliotecario"]))
):
    """Actualiza una categoría."""
    categoria = session.get(Categoria, categoria_id)
    if not categoria:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoría no encontrada"
        )
        
    if categoria_in.nombre and categoria_in.nombre != categoria.nombre:
        existente = session.exec(select(Categoria).where(Categoria.nombre == categoria_in.nombre)).first()
        if existente:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ya existe una categoría con ese nombre"
            )
        categoria.nombre = categoria_in.nombre
        
    if categoria_in.descripcion is not None:
        categoria.descripcion = categoria_in.descripcion

    session.add(categoria)
    session.commit()
    session.refresh(categoria)
    return categoria

@router.delete("/{categoria_id}", status_code=status.HTTP_200_OK)
def eliminar_categoria(
    categoria_id: int,
    session: Session = Depends(get_session),
    current_user: Usuario = Depends(require_roles(["Administrador"]))
):
    """
    Elimina una categoría verificando integridad referencial (no tener libros activos asociados).
    """
    categoria = session.get(Categoria, categoria_id)
    if not categoria:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Categoría no encontrada"
        )
        
    libros_asociados = session.exec(
        select(Libro).where(Libro.categoria_id == categoria_id, Libro.is_active == True)
    ).first()
    if libros_asociados:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede eliminar la categoría porque tiene libros activos asociados en el catálogo"
        )
        
    session.delete(categoria)
    session.commit()
    return {"mensaje": f"Categoría '{categoria.nombre}' eliminada correctamente"}
