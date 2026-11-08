from contextlib import asynccontextmanager
from fastapi import FastAPI
from sqlmodel import Session, select
from core.database import create_db_and_tables, engine
from core.security import get_password_hash
from models.models import Rol, Usuario, Autor, Categoria, Libro, Prestamo
from routers import auth, usuarios, autores, categorias, libros, prestamos
from datetime import date

def seed_initial_data():
    """Siembra de roles predeterminados, usuarios de prueba y catálogo inicial."""
    with Session(engine) as session:
        # 1. Crear Roles si no existen
        roles_nombres = ["Administrador", "Bibliotecario", "Usuario"]
        roles_map = {}
        for r_nombre in roles_nombres:
            r = session.exec(select(Rol).where(Rol.nombre == r_nombre)).first()
            if not r:
                r = Rol(nombre=r_nombre)
                session.add(r)
                session.commit()
                session.refresh(r)
            roles_map[r_nombre] = r

        # 2. Crear usuarios de demostración para cada rol
        usuarios_seed = [
            ("Administrador General", "admin@biblioteca.com", "admin123", roles_map["Administrador"].id),
            ("Bibliotecario Principal", "bibliotecario@biblioteca.com", "biblio123", roles_map["Bibliotecario"].id),
            ("Usuario Lector", "lector@biblioteca.com", "lector123", roles_map["Usuario"].id),
        ]

        for nombre, email, pwd, rol_id in usuarios_seed:
            user = session.exec(select(Usuario).where(Usuario.email == email)).first()
            if not user:
                session.add(Usuario(
                    nombre=nombre,
                    email=email,
                    hashed_password=get_password_hash(pwd),
                    rol_id=rol_id,
                    is_active=True
                ))
        session.commit()

        # Categorías iniciales
        categorias_seed = [
            ("Tecnología e Informática", "Libros técnicos de desarrollo y software"),
            ("Literatura Latinoamericana", "Obras destacadas de narrativa iberoamericana")
        ]
        cat_map = {}
        for cat_nombre, cat_desc in categorias_seed:
            cat = session.exec(select(Categoria).where(Categoria.nombre == cat_nombre)).first()
            if not cat:
                cat = Categoria(nombre=cat_nombre, descripcion=cat_desc)
                session.add(cat)
                session.commit()
                session.refresh(cat)
            cat_map[cat_nombre] = cat

        #  Autores iniciales
        autores_seed = [
            ("Gabriel García Márquez", "Colombiana", date(1927, 3, 6), "Premio Nobel de Literatura 1982"),
            ("Robert C. Martin", "Estadounidense", date(1952, 12, 5), "Conocido como Uncle Bob, referente en Clean Code")
        ]
        autor_map = {}
        for aut_nom, aut_nac, aut_fec, aut_bio in autores_seed:
            autor = session.exec(select(Autor).where(Autor.nombre == aut_nom)).first()
            if not autor:
                autor = Autor(nombre=aut_nom, nacionalidad=aut_nac, fecha_nacimiento=aut_fec, biografia=aut_bio)
                session.add(autor)
                session.commit()
                session.refresh(autor)
            autor_map[aut_nom] = autor

        #  Libros iniciales
        libros_seed = [
            ("Cien Años de Soledad", "978-0307474728", autor_map["Gabriel García Márquez"].id, cat_map["Literatura Latinoamericana"].id),
            ("Clean Code: A Handbook of Agile Software Craftsmanship", "978-0132350884", autor_map["Robert C. Martin"].id, cat_map["Tecnología e Informática"].id)
        ]
        for lib_titulo, lib_isbn, lib_aut_id, lib_cat_id in libros_seed:
            libro = session.exec(select(Libro).where(Libro.isbn == lib_isbn)).first()
            if not libro:
                session.add(Libro(
                    titulo=lib_titulo,
                    isbn=lib_isbn,
                    autor_id=lib_aut_id,
                    categoria_id=lib_cat_id,
                    disponible=True,
                    is_active=True
                ))
        session.commit()

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    seed_initial_data()
    yield

app = FastAPI(
    title="API Sistema Bibliotecario",
    description=(
        "API REST modular para la gestión de catálogo bibliográfico, ejemplares, préstamos, "
        "devoluciones y usuarios con autenticación JWT y control de acceso basado en roles (RBAC)."
    ),
    version="1.0.0",
    lifespan=lifespan
)

# Inclusión de routers
app.include_router(auth.router)
app.include_router(usuarios.router)
app.include_router(autores.router)
app.include_router(categorias.router)
app.include_router(libros.router)
app.include_router(prestamos.router)

@app.get("/", tags=["General"])
def root():
    return {
        "sistema": "API REST Sistema Bibliotecario",
        "estado": "En línea",
        
    }
