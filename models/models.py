# Modelos de SQLModel
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import date

# ENTIDADES BASE

class Rol(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(index=True, unique=True)
    
    # Relaciones
    usuarios: List["Usuario"] = Relationship(back_populates="rol")


class Usuario(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    email: str = Field(unique=True, index=True)
    hashed_password: str
    is_active: bool = Field(default=True) # Soft Delete
    
    rol_id: int = Field(default=None, foreign_key="rol.id")
    
    # Relaciones
    rol: Optional[Rol] = Relationship(back_populates="usuarios")
    prestamos: List["Prestamo"] = Relationship(back_populates="usuario")


class Categoria(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(unique=True, index=True)
    descripcion: Optional[str] = Field(default=None)
    
    libros: List["Libro"] = Relationship(back_populates="categoria")


class Autor(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str = Field(index=True)
    nacionalidad: Optional[str] = Field(default=None)
    fecha_nacimiento: Optional[date] = Field(default=None)
    biografia: Optional[str] = Field(default=None)
    
    libros: List["Libro"] = Relationship(back_populates="autor")


class Libro(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    titulo: str = Field(index=True)
    isbn: str = Field(unique=True, index=True)
    disponible: bool = Field(default=True) # Regla de negocio: estado actual
    is_active: bool = Field(default=True)  # Soft Delete
    
    autor_id: int = Field(foreign_key="autor.id")
    categoria_id: int = Field(foreign_key="categoria.id")
    
    # Relaciones
    autor: Optional[Autor] = Relationship(back_populates="libros")
    categoria: Optional[Categoria] = Relationship(back_populates="libros")
    prestamos: List["Prestamo"] = Relationship(back_populates="libro")


class Prestamo(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    fecha_prestamo: date = Field(default_factory=date.today)
    fecha_devolucion_esperada: date # Se calcula automáticamente
    fecha_devolucion_real: Optional[date] = Field(default=None)
    estado: str = Field(default="ACTIVO") # ACTIVO, DEVUELTO, VENCIDO
    
    usuario_id: int = Field(foreign_key="usuario.id")
    libro_id: int = Field(foreign_key="libro.id")
    
    # Relaciones
    usuario: Optional[Usuario] = Relationship(back_populates="prestamos")
    libro: Optional[Libro] = Relationship(back_populates="prestamos")
