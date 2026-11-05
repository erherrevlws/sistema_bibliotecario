# API REST para el Manejo de un Sistema Bibliotecario

**Módulo / Asignatura:** Utilización de Frameworks para el Desarrollo de Software  
**Docente:** Oscar Alfredo Cruz Rovira  
**Ciclo:** Ciclo II 2026 — Entrega: Semana 16  
**Framework Principal:** FastAPI (Python 3.10+) + SQLModel  

---

## 1. Descripción del Proyecto

Esta solución es una **API REST robusta, modular y segura** para la administración integral de las operaciones de una biblioteca. Permite gestionar:
* **Usuarios y Roles (RBAC):** Administrador, Bibliotecario y Usuario lector.
* **Autenticación y Seguridad:** Tokens Bearer JWT con tiempo de expiración y contraseñas hasheadas con algoritmo *bcrypt*.
* **Catálogo Bibliográfico:** CRUD completo de libros, autores y categorías, con validación de datos e integridad referencial.
* **Reglas de Negocio de Préstamos y Devoluciones:** Validación en tiempo real de disponibilidad de ejemplares, control de fechas e historial.

---

## 2. Arquitectura del Proyecto

El proyecto sigue una arquitectura en capas limpia y desacoplada:

```text
frameworks_proyecto_biblioteca/
├── core/
│   ├── config.py           # Carga de variables de entorno (.env)
│   ├── database.py         # Configuración del motor de BD (SQLite / MySQL) y sesiones
│   ├── dependencias.py     # Inyección de dependencias de seguridad y roles (RBAC)
│   └── security.py         # Criptografía bcrypt y generación/validación de JWT
├── models/
│   └── models.py           # Modelos de entidades de base de datos con SQLModel
├── schemas/
│   └── schemas.py          # Modelos Pydantic para validación y serialización HTTP
├── routers/
│   ├── auth.py             # Login y emisión de token OAuth2 Bearer
│   ├── usuarios.py         # CRUD de usuarios, roles y autorregistro
│   ├── autores.py          # CRUD de autores
│   ├── categorias.py       # CRUD de categorías bibliográficas
│   ├── libros.py           # CRUD de catálogo de libros con control de disponibilidad
│   └── prestamos.py        # Flujos de negocio: prestar, devolver e historial
├── tests/
│   └── test_api.py         # Suite de pruebas automatizadas (10 Casos del PDF)
├── .env                    # Configuración del entorno
├── .gitignore              # Archivos y carpetas excluidas de Git
├── main.py                 # Punto de entrada de la aplicación FastAPI y seeding inicial
├── requirements.txt        # Dependencias del proyecto
└── README.md               # Documentación técnica completa
```

---

## 3. Instalación y Puesta en Marcha

### Prerrequisitos
* Python 3.10, 3.11, 3.12, 3.13 o 3.14 instalado.
* Git.

### Paso 1: Clonar el repositorio y acceder a la carpeta
```bash
git clone <url-del-repositorio>
cd frameworks_proyecto_biblioteca
```

### Paso 2: Crear y activar el entorno virtual
En Windows (PowerShell / CMD):
```powershell
python -m venv .venv
.venv\Scripts\activate
```

En Linux / macOS:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Paso 3: Instalar dependencias
```bash
pip install -r requirements.txt
```

### Paso 4: Configurar variables de entorno (`.env`)
El proyecto incluye un archivo `.env` configurado por defecto para funcionar inmediatamente con **SQLite** (reproducibilidad garantizada sin requerir bases de datos externas):

```env
DATABASE_URL=sqlite:///./biblioteca.db
# Para alternar a MySQL, descomenta la siguiente línea y asegúrate de crear la BD 'biblioteca_db':
# DATABASE_URL=mysql+pymysql://root:@localhost:3306/biblioteca_db
SECRET_KEY=super_secreto_para_el_proyecto_biblioteca_cambiar_luego
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

### Paso 5: Iniciar el servidor de desarrollo
```bash
uvicorn main:app --reload
```
La API quedará accesible en:
* **API Base:** `http://127.0.0.1:8000/`
* **Documentación Interactiva (Swagger UI):** `http://127.0.0.1:8000/docs`
* **Documentación Alternativa (Redoc):** `http://127.0.0.1:8000/redoc`

---

## 4. Credenciales de Prueba Iniciales (Siembra Automática)

Al iniciar la aplicación por primera vez, el sistema ejecuta automáticamente la siembra de datos iniciales (*seeding*):

| Rol | Correo Electrónico | Contraseña | Alcance de Permisos |
| :--- | :--- | :--- | :--- |
| **Administrador** | `admin@biblioteca.com` | `admin123` | Control total del sistema, gestión de usuarios, roles, catálogo y préstamos. |
| **Bibliotecario** | `bibliotecario@biblioteca.com` | `biblio123` | Gestión de catálogo (libros, autores, categorías), registro de préstamos y devoluciones. |
| **Usuario** | `lector@biblioteca.com` | `lector123` | Consulta del catálogo, solicitud de préstamos propios y visualización de su historial. |

---

## 5. Módulos y Endpoints de la API REST

### A. Autenticación (`/auth`)
* `POST /auth/login`: Autenticación con credenciales OAuth2. Retorna `access_token` JWT y `token_type: "bearer"`.

### B. Usuarios y Roles (`/usuarios`)
* `POST /usuarios/registro`: Autoregistro público para nuevos lectores (Rol `Usuario`).
* `POST /usuarios/`: Creación administrativa de usuarios con rol explícito (`[Administrador]`).
* `GET /usuarios/me`: Datos del perfil del usuario autenticado actual.
* `GET /usuarios/`: Listado de usuarios activos (`[Administrador, Bibliotecario]`).
* `GET /usuarios/{id}`: Detalle de usuario por ID (`[Administrador, Bibliotecario]`).
* `PUT /usuarios/{id}`: Actualización de datos y roles (`[Administrador]`).
* `DELETE /usuarios/{id}`: Soft delete de usuario validando que no tenga préstamos activos (`[Administrador]`).
* `GET /usuarios/roles`: Listado de roles disponibles (`[Administrador, Bibliotecario]`).

### C. Catálogo de Libros (`/libros`)
* `POST /libros/`: Registrar nuevo libro validando unicidad de ISBN y existencia de autor/categoría (`[Administrador, Bibliotecario]`).
* `GET /libros/`: Listado de libros con filtros opcionales (`titulo`, `autor_id`, `categoria_id`, `disponible`).
* `GET /libros/{id}`: Consulta detallada de un libro.
* `PUT /libros/{id}`: Actualización de información del libro (`[Administrador, Bibliotecario]`).
* `DELETE /libros/{id}`: Desactivación / eliminación lógica impidiendo la acción si el libro está prestado (`[Administrador, Bibliotecario]`).

### D. Autores y Categorías (`/autores`, `/categorias`)
* `POST /autores/` y `POST /categorias/`: Registro de nuevos autores y categorías.
* `GET /autores/` y `GET /categorias/`: Consulta con filtros por nombre.
* `PUT` y `DELETE`: Actualización y eliminación con validación de integridad referencial.

### E. Préstamos y Devoluciones (`/prestamos`)
* `POST /prestamos/`: Registrar nuevo préstamo. Valida que `disponible == True` y actualiza automáticamente el libro a `disponible = False`.
* `GET /prestamos/`: Historial de préstamos (filtrado por usuario si es lector, o general si es bibliotecario/admin).
* `GET /prestamos/activos`: Lista únicamente préstamos activos pendientes de devolución.
* `GET /prestamos/{id}`: Detalle de un préstamo.
* `POST /prestamos/{id}/devolver`: Registra devolución, calcula fecha real, cambia estado a `DEVUELTO` y restaura el libro a `disponible = True` (`[Administrador, Bibliotecario]`).

---

## 6. Reglas de Negocio Implementadas

1. **Disponibilidad de Ejemplares (Reglas 1 y 3):** No es posible prestar un libro que ya se encuentre prestado (`disponible = False`). Al efectuar la devolución, el ejemplar vuelve a estar disponible automáticamente.
2. **Identificación Obligatoria (Regla 2):** Todo préstamo registra usuario, libro, fecha de salida, fecha esperada de entrega y estado.
3. **Control de Acceso RBAC (Regla 4):** Las rutas administrativas devuelven `403 Forbidden` ante intentos de acceso por parte de usuarios sin los privilegios requeridos.
4. **Seguridad en Fallo de Autenticación (Regla 5):** Las credenciales incorrectas retornan `401 Unauthorized` con el mensaje genérico `"Credenciales incorrectas"`, sin revelar si el correo existe o no en la base de datos.
5. **Validación de Datos (Regla 6):** Validación estricta con Pydantic (longitudes mínimas, formato de correos, números positivos, ISBN válido).
6. **Integridad Referencial Justificada (Regla 7):** Se impide eliminar usuarios o libros con préstamos activos pendientes. Se implementa *Soft Delete* (`is_active = False`) para mantener la trazabilidad histórica de los registros.

---

## 7. Casos de Prueba Obligatorios y Evidencias

El proyecto incluye una suite de pruebas automatizadas que cubre al 100% los **10 Casos de Prueba Obligatorios** descritos en la página 4 de la guía de evaluación:

| # | Caso de Prueba | Endpoint Evaluado | Resultado / Evidencia |
| :-: | :--- | :--- | :--- |
| **1** | **Login válido** | `POST /auth/login` | Retorna `200 OK`, `access_token` JWT válido y `token_type: bearer`. |
| **2** | **Login inválido** | `POST /auth/login` | Retorna `401 Unauthorized` genérico sin revelar datos sensibles. |
| **3** | **Ruta protegida sin token** | `GET /usuarios/me` | Retorna `401 Unauthorized` con mensaje de autenticación requerida. |
| **4** | **Token inválido o expirado** | `GET /usuarios/me` | Retorna `401 Unauthorized` ante token manipulado o vencido. |
| **5** | **Acción sin permiso** | `POST /usuarios/` (como Lector) | Retorna `403 Forbidden` ("No posees los privilegios requeridos"). |
| **6** | **CRUD de libro** | `/libros/` (POST, GET, PUT, DELETE) | Creación, consulta, edición y borrado seguro gestionando restricciones. |
| **7** | **Préstamo válido** | `POST /prestamos/` | Retorna `201 Created` y el libro pasa a `disponible: false`. |
| **8** | **Préstamo inválido** | `POST /prestamos/` (mismo libro) | Retorna `400 Bad Request` impidiendo prestar libro no disponible. |
| **9** | **Devolución** | `POST /prestamos/{id}/devolver` | Retorna `200 OK`, estado `DEVUELTO` y el libro pasa a `disponible: true`. |
| **10**| **Datos inválidos** | `POST /libros/` (datos incompletos) | Retorna `422 Unprocessable Entity` rechazando entradas inválidas. |

### Ejecutar las pruebas automatizadas:
```bash
python tests/test_api.py
```
*Salida esperada:*
```text
..........
----------------------------------------------------------------------
Ran 10 tests in 2.5s

OK
```

---

## 8. Guía para la Demostración en Vivo ante el Docente

Para realizar la defensa técnica siguiendo los criterios del numeral 9 del documento:

1. **Abrir Swagger UI:** Navegar a `http://127.0.0.1:8000/docs`.
2. **Autenticación (Flujo 1):**
   * Presionar el botón verde **Authorize** arriba a la derecha.
   * Introducir `admin@biblioteca.com` y `admin123`.
3. **Consumo de ruta protegida (Flujo 2):**
   * Ejecutar `GET /usuarios/me` y verificar que devuelve el perfil y rol del administrador.
4. **Operación rechazada por permisos (Flujo 3):**
   * Iniciar sesión con `lector@biblioteca.com` / `lector123`.
   * Intentar ejecutar `POST /usuarios/` o `POST /libros/` y demostrar la respuesta `403 Forbidden`.
5. **Registro y consulta de libros (Flujo 4):**
   * Con token de Bibliotecario o Admin, registrar un nuevo libro en `POST /libros/`.
   * Consultarlo mediante `GET /libros/`.
6. **Préstamo de ejemplar disponible (Flujo 5):**
   * Ejecutar `POST /prestamos/` con el ID del libro creado.
   * Verificar que la respuesta es `201 Created` y que al consultar `GET /libros/{id}`, `disponible` es ahora `false`.
7. **Intento de préstamo de ejemplar no disponible (Flujo 6):**
   * Intentar ejecutar nuevamente `POST /prestamos/` con el mismo ID de libro.
   * Demostrar que el sistema responde con `400 Bad Request` indicando que el libro ya está prestado.
8. **Devolución y actualización de disponibilidad (Flujo 7):**
   * Ejecutar `POST /prestamos/{id}/devolver`.
   * Verificar respuesta exitosa y consultar nuevamente `GET /libros/{id}` para evidenciar que `disponible` volvió a ser `true`.
