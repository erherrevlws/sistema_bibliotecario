# Schemas Pydantic para validación de entrada y serialización de salida
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import date

# ----------------- AUTENTICACIÓN -----------------
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    email: Optional[str] = None
    rol: Optional[str] = None

# ----------------- ROLES -----------------
class RolRead(BaseModel):
    id: int
    nombre: str

    class Config:
        from_attributes = True

# ----------------- USUARIOS -----------------
class UsuarioCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)
    rol_id: Optional[int] = None  # Si no se envía, se asigna el rol Usuario por defecto

class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=6)
    rol_id: Optional[int] = None
    is_active: Optional[bool] = None

class UsuarioRead(BaseModel):
    id: int
    nombre: str
    email: EmailStr
    is_active: bool
    rol_id: int
    rol: Optional[RolRead] = None

    class Config:
        from_attributes = True

# ----------------- AUTORES -----------------
class AutorCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    nacionalidad: Optional[str] = Field(None, max_length=100)
    fecha_nacimiento: Optional[date] = None
    biografia: Optional[str] = None

class AutorUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    nacionalidad: Optional[str] = None
    fecha_nacimiento: Optional[date] = None
    biografia: Optional[str] = None

class AutorRead(BaseModel):
    id: int
    nombre: str
    nacionalidad: Optional[str] = None
    fecha_nacimiento: Optional[date] = None
    biografia: Optional[str] = None

    class Config:
        from_attributes = True

# ----------------- CATEGORÍAS -----------------
class CategoriaCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    descripcion: Optional[str] = None

class CategoriaUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    descripcion: Optional[str] = None

class CategoriaRead(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str] = None

    class Config:
        from_attributes = True

# ----------------- LIBROS -----------------
class LibroCreate(BaseModel):
    titulo: str = Field(..., min_length=1, max_length=200)
    isbn: str = Field(..., min_length=5, max_length=30)
    autor_id: int
    categoria_id: int

class LibroUpdate(BaseModel):
    titulo: Optional[str] = Field(None, min_length=1, max_length=200)
    isbn: Optional[str] = Field(None, min_length=5, max_length=30)
    autor_id: Optional[int] = None
    categoria_id: Optional[int] = None
    disponible: Optional[bool] = None

class LibroRead(BaseModel):
    id: int
    titulo: str
    isbn: str
    disponible: bool
    is_active: bool
    autor_id: int
    categoria_id: int
    autor: Optional[AutorRead] = None
    categoria: Optional[CategoriaRead] = None

    class Config:
        from_attributes = True

# ----------------- PRÉSTAMOS -----------------
class PrestamoCreate(BaseModel):
    libro_id: int
    usuario_id: Optional[int] = None  # Si lo crea el bibliotecario/admin puede especificarlo; si es usuario regular, toma el suyo
    dias_prestamo: Optional[int] = Field(default=14, ge=1, le=60)

class PrestamoRead(BaseModel):
    id: int
    fecha_prestamo: date
    fecha_devolucion_esperada: date
    fecha_devolucion_real: Optional[date] = None
    estado: str
    usuario_id: int
    libro_id: int
    libro: Optional[LibroRead] = None
    usuario: Optional[UsuarioRead] = None

    class Config:
        from_attributes = True

class DevolucionResponse(BaseModel):
    mensaje: str
    prestamo: PrestamoRead
