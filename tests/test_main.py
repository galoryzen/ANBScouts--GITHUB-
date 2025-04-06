import unittest
from src.app import app


class TestClass(unittest.TestCase):
    def setUp(self):
        self.url = "/"
        self.client = app.test_client()

    def test_hello_world(self):
        response = self.client.get(self.url)

        assert response.status_code == 200
        assert response.json == {"message": "Hello, World!"}
