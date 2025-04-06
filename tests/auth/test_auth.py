import unittest
from flask import json
from flask_jwt_extended import create_access_token
from src.models.main import User
from src.app import app, db
from werkzeug.security import generate_password_hash

class TestAuth(unittest.TestCase):
    def setUp(self):
        """Configurar el entorno de prueba"""
        self.client = app.test_client()
        self.signup_url = "auth/signup"
        self.login_url = "auth/login"

        # Crear la base de datos en memoria
        with app.app_context():
            db.create_all()

    def tearDown(self):
        """Limpiar la base de datos después de cada prueba"""
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_signup_success(self):
        """Prueba de registro exitoso"""
        response = self.client.post(self.signup_url, json={
            "username": "crios",
            "password1": "Easy789",
            "password2": "Easy789",
            "role": "player",
            "name": "Carlos",
            "last_name": "Rios",
            "email": "carlos.rios@uniandes.com",
            "city": "Zipaquira",
            "country": "Colombia"
        })
        self.assertEqual(response.status_code, 201)
        self.assertIn("Usuario creado exitosamente", response.get_json()["message"])

    def test_signup_password_mismatch(self):
        """Prueba de error cuando las contraseñas no coinciden"""
        response = self.client.post(self.signup_url, json={
            "username": "crios",
            "password1": "Easy789",
            "password2": "Easy123",
            "role": "player",
            "name": "Carlos",
            "last_name": "Rios",
            "email": "carlos.rios@uniandes.com",
            "city": "Zipaquira",
            "country": "Colombia"
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn("Las contraseñas no coinciden", response.get_json()["error"])

    def test_signup_email_already_registered(self):
        """Prueba de error cuando el email ya está registrado"""
        # Crear un usuario en la base de datos
        with app.app_context():
            user = User(
                username="crios",
                password=generate_password_hash("Easy789"),
                role="player",
                name="Carlos",
                last_name="Rios",
                email="carlos.rios@uniandes.com",
                city="Zipaquira",
                country="Colombia"
            )
            db.session.add(user)
            db.session.commit()

        # Intentar registrar un usuario con el mismo email
        response = self.client.post(self.signup_url, json={
            "username": "carprios",
            "password1": "Sal456",
            "password2": "Sal456",
            "role": "player",
            "name": "Carlos",
            "last_name": "Rios",
            "email": "carlos.rios@uniandes.com",
            "city": "Chia",
            "country": "Colombia"
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn("El email ya está registrado", response.get_json()["error"])

    def test_login_success(self):
        """Prueba de inicio de sesión exitoso"""
        # Crear un usuario en la base de datos
        with app.app_context():
            user = User(
                username="crios",
                password=generate_password_hash("Easy789"),
                role="player",
                name="Carlos",
                last_name="Rios",
                email="carlos.rios@uniandes.com",
                city="Zipaquira",
                country="Colombia"
            )
            db.session.add(user)
            db.session.commit()

        # Intentar iniciar sesión
        response = self.client.post(self.login_url, json={
            "username": "crios",
            "password": "Easy789"
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("access_token", response.get_json())

    def test_login_invalid_credentials(self):
        """Prueba de error con credenciales inválidas"""
        response = self.client.post(self.login_url, json={
            "username": "crios",
            "password": "Wrong789"
        })
        self.assertEqual(response.status_code, 401)
        self.assertIn("Credenciales inválidas", response.get_json()["error"])