# Suite de pruebas automatizadas para la API de Sistema Bibliotecario
# Cubre exhaustivamente los 10 Casos de Prueba Obligatorios definidos en el PDF

import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlmodel import SQLModel
from fastapi.testclient import TestClient
from main import app, create_db_and_tables, seed_initial_data
from core.database import engine

class TestSistemaBibliotecario(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        SQLModel.metadata.drop_all(engine)
        create_db_and_tables()
        seed_initial_data()
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        cls.client.close()
        # Dejar la base de datos poblada para la demostración manual
        seed_initial_data()

    # ----------------------------------------------------
    # Caso 1: Login válido
    # Evidencia esperada: Se obtiene token y datos mínimos necesarios
    # ----------------------------------------------------
    def test_01_login_valido(self):
        response = self.client.post(
            "/auth/login",
            data={"username": "admin@biblioteca.com", "password": "admin123"}
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access_token", data)
        self.assertEqual(data.get("token_type"), "bearer")
        self.assertTrue(len(data["access_token"]) > 20)

    # ----------------------------------------------------
    # Caso 2: Login inválido
    # Evidencia esperada: Se rechaza el acceso sin exponer credenciales ni existencia de usuario
    # ----------------------------------------------------
    def test_02_login_invalido(self):
        # Caso A: Contraseña incorrecta
        res_pass_err = self.client.post(
            "/auth/login",
            data={"username": "admin@biblioteca.com", "password": "password_incorrecta"}
        )
        self.assertEqual(res_pass_err.status_code, 401)
        self.assertEqual(res_pass_err.json().get("detail"), "Credenciales incorrectas")

        # Caso B: Usuario inexistente (debe devolver exactamente el mismo error genérico)
        res_user_err = self.client.post(
            "/auth/login",
            data={"username": "noexiste@biblioteca.com", "password": "cualquier_pass"}
        )
        self.assertEqual(res_user_err.status_code, 401)
        self.assertEqual(res_user_err.json().get("detail"), "Credenciales incorrectas")

    # ----------------------------------------------------
    # Caso 3: Ruta protegida sin token
    # Evidencia esperada: La API deniega el acceso con respuesta HTTP apropiada (401)
    # ----------------------------------------------------
    def test_03_ruta_protegida_sin_token(self):
        response = self.client.get("/usuarios/me")
        self.assertEqual(response.status_code, 401)
        self.assertIn("detail", response.json())

    # ----------------------------------------------------
    # Caso 4: Token inválido o expirado
    # Evidencia esperada: La API rechaza la solicitud (401)
    # ----------------------------------------------------
    def test_04_token_invalido(self):
        headers = {"Authorization": "Bearer este_es_un_token_totalmente_falso_e_invalido"}
        response = self.client.get("/usuarios/me", headers=headers)
        self.assertEqual(response.status_code, 401)
        self.assertIn("detail", response.json())

    # ----------------------------------------------------
    # Caso 5: Acción sin permiso
    # Evidencia esperada: Usuario autenticado sin privilegios no puede ejecutar la operación (403)
    # ----------------------------------------------------
    def test_05_accion_sin_permiso(self):
        # Login como usuario normal (rol 'Usuario')
        login_res = self.client.post(
            "/auth/login",
            data={"username": "lector@biblioteca.com", "password": "lector123"}
        )
        token_lector = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token_lector}"}

        # Intentar crear un usuario en /usuarios/ (Solo Administrador)
        nuevo_user = {
            "nombre": "Usuario Hack",
            "email": "hack@biblioteca.com",
            "password": "secretpassword",
            "rol_id": 1
        }
        res_crear_user = self.client.post("/usuarios/", json=nuevo_user, headers=headers)
        self.assertEqual(res_crear_user.status_code, 403)
        self.assertIn("privilegios", res_crear_user.json().get("detail", "").lower())

    # ----------------------------------------------------
    # Caso 6: CRUD de libro
    # Evidencia esperada: Crear, consultar, actualizar y eliminar/gestionar restricciones
    # ----------------------------------------------------
    def test_06_crud_de_libro(self):
        # Login como Bibliotecario
        login_res = self.client.post(
            "/auth/login",
            data={"username": "bibliotecario@biblioteca.com", "password": "biblio123"}
        )
        token_biblio = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token_biblio}"}

        # C - Crear libro
        libro_data = {
            "titulo": "Estructuras de Datos y Algoritmos",
            "isbn": "978-0131103627-TEST",
            "autor_id": 1,
            "categoria_id": 1
        }
        res_create = self.client.post("/libros/", json=libro_data, headers=headers)
        self.assertEqual(res_create.status_code, 201)
        libro_creado = res_create.json()
        libro_id = libro_creado["id"]
        self.assertEqual(libro_creado["titulo"], libro_data["titulo"])
        self.assertTrue(libro_creado["disponible"])

        # R - Consultar libro por ID
        res_get = self.client.get(f"/libros/{libro_id}", headers=headers)
        self.assertEqual(res_get.status_code, 200)
        self.assertEqual(res_get.json()["isbn"], libro_data["isbn"])

        # U - Actualizar libro
        update_data = {"titulo": "Estructuras de Datos Avanzadas"}
        res_update = self.client.put(f"/libros/{libro_id}", json=update_data, headers=headers)
        self.assertEqual(res_update.status_code, 200)
        self.assertEqual(res_update.json()["titulo"], "Estructuras de Datos Avanzadas")

        # D - Eliminar libro (Soft Delete y gestión de restricciones)
        res_delete = self.client.delete(f"/libros/{libro_id}", headers=headers)
        self.assertEqual(res_delete.status_code, 200)

        # Verificar que ya no aparece en consulta
        res_verify = self.client.get(f"/libros/{libro_id}", headers=headers)
        self.assertEqual(res_verify.status_code, 404)

    # ----------------------------------------------------
    # Caso 7: Préstamo válido
    # Evidencia esperada: El préstamo se registra y el ejemplar deja de estar disponible
    # ----------------------------------------------------
    def test_07_prestamo_valido(self):
        # Login de admin para crear un libro limpio para prestar
        admin_login = self.client.post(
            "/auth/login",
            data={"username": "admin@biblioteca.com", "password": "admin123"}
        )
        token_admin = admin_login.json()["access_token"]
        headers_admin = {"Authorization": f"Bearer {token_admin}"}

        # Crear libro disponible
        nuevo_libro = self.client.post(
            "/libros/",
            json={"titulo": "Libro de Prueba Préstamo", "isbn": "978-TEST-PRESTAMO-01", "autor_id": 1, "categoria_id": 1},
            headers=headers_admin
        ).json()
        libro_id = nuevo_libro["id"]
        self.assertTrue(nuevo_libro["disponible"])

        # Realizar préstamo con usuario lector
        lector_login = self.client.post(
            "/auth/login",
            data={"username": "lector@biblioteca.com", "password": "lector123"}
        )
        token_lector = lector_login.json()["access_token"]
        headers_lector = {"Authorization": f"Bearer {token_lector}"}

        res_prestamo = self.client.post(
            "/prestamos/",
            json={"libro_id": libro_id, "dias_prestamo": 7},
            headers=headers_lector
        )
        self.assertEqual(res_prestamo.status_code, 201)
        prestamo_creado = res_prestamo.json()
        self.assertEqual(prestamo_creado["estado"], "ACTIVO")

        # Verificar que el ejemplar dejó de estar disponible
        res_libro = self.client.get(f"/libros/{libro_id}", headers=headers_lector)
        self.assertEqual(res_libro.status_code, 200)
        self.assertFalse(res_libro.json()["disponible"])

    # ----------------------------------------------------
    # Caso 8: Préstamo inválido
    # Evidencia esperada: Se impide prestar un ejemplar no disponible
    # ----------------------------------------------------
    def test_08_prestamo_invalido(self):
        admin_login = self.client.post(
            "/auth/login",
            data={"username": "admin@biblioteca.com", "password": "admin123"}
        )
        headers_admin = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

        # Crear libro y prestarlo una primera vez
        libro = self.client.post(
            "/libros/",
            json={"titulo": "Libro Conflicto", "isbn": "978-TEST-CONFLICTO-01", "autor_id": 1, "categoria_id": 1},
            headers=headers_admin
        ).json()
        libro_id = libro["id"]

        # Primer préstamo (válido)
        p1 = self.client.post("/prestamos/", json={"libro_id": libro_id}, headers=headers_admin)
        self.assertEqual(p1.status_code, 201)

        # Segundo préstamo sobre el mismo libro (debe ser rechazado con 400 Bad Request)
        p2 = self.client.post("/prestamos/", json={"libro_id": libro_id}, headers=headers_admin)
        self.assertEqual(p2.status_code, 400)
        self.assertIn("no se encuentra disponible", p2.json().get("detail", "").lower())

    # ----------------------------------------------------
    # Caso 9: Devolución
    # Evidencia esperada: Se registra y el ejemplar vuelve a estar disponible
    # ----------------------------------------------------
    def test_09_devolucion(self):
        admin_login = self.client.post(
            "/auth/login",
            data={"username": "admin@biblioteca.com", "password": "admin123"}
        )
        headers_admin = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

        # Crear libro y prestarlo
        libro = self.client.post(
            "/libros/",
            json={"titulo": "Libro para Devolver", "isbn": "978-TEST-DEVOLVER-01", "autor_id": 1, "categoria_id": 1},
            headers=headers_admin
        ).json()
        libro_id = libro["id"]

        prestamo = self.client.post("/prestamos/", json={"libro_id": libro_id}, headers=headers_admin).json()
        prestamo_id = prestamo["id"]

        # Verificar que inicialmente no está disponible
        libro_check1 = self.client.get(f"/libros/{libro_id}", headers=headers_admin).json()
        self.assertFalse(libro_check1["disponible"])

        # Registrar devolución
        res_dev = self.client.post(f"/prestamos/{prestamo_id}/devolver", headers=headers_admin)
        self.assertEqual(res_dev.status_code, 200)
        dev_data = res_dev.json()
        self.assertEqual(dev_data["prestamo"]["estado"], "DEVUELTO")
        self.assertIsNotNone(dev_data["prestamo"]["fecha_devolucion_real"])

        # Verificar que el libro volvió a estar disponible
        libro_check2 = self.client.get(f"/libros/{libro_id}", headers=headers_admin).json()
        self.assertTrue(libro_check2["disponible"])

    # ----------------------------------------------------
    # Caso 10: Datos inválidos
    # Evidencia esperada: La API rechaza entradas que incumplen las reglas de validación
    # ----------------------------------------------------
    def test_10_datos_invalidos(self):
        admin_login = self.client.post(
            "/auth/login",
            data={"username": "admin@biblioteca.com", "password": "admin123"}
        )
        headers_admin = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

        # Enviar libro con datos inválidos (título vacío, autor_id no numérico o faltante)
        libro_invalido = {
            "titulo": "",
            "isbn": "12",  # Menor a 5 caracteres permitidos
            "autor_id": "no-es-un-id",
            "categoria_id": 1
        }
        response = self.client.post("/libros/", json=libro_invalido, headers=headers_admin)
        # FastAPI/Pydantic devuelve 422 Unprocessable Entity
        self.assertEqual(response.status_code, 422)
        self.assertIn("detail", response.json())

if __name__ == "__main__":
    unittest.main()
