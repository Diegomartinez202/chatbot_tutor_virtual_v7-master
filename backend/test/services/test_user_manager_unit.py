import pytest

from backend.services import user_manager


@pytest.fixture(autouse=True)
def clean_users_collection(mongo_test_db):
    """
    Ejemplo: limpiar colección users antes de cada test.
    Ajusta según cómo obtengas la DB de test.
    """
    mongo_test_db["users"].delete_many({})
    yield
    mongo_test_db["users"].delete_many({})


def test_crear_y_validar_usuario_unit():
    email = "prueba@example.com"
    password = "claveSegura123"
    rol = "admin"

    user = user_manager.crear_usuario(email=email, password=password, rol=rol)
    assert user["email"] == email
    assert user["rol"] == rol

    encontrado = user_manager.buscar_usuario_por_email(email)
    assert encontrado is not None
    assert encontrado["email"] == email

    assert user_manager.validar_credenciales(email, password) is not None
    assert user_manager.validar_credenciales(email, "mala") is None

    assert user_manager.eliminar_usuario(email) is True
    assert user_manager.buscar_usuario_por_email(email) is None
