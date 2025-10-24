# tests/test_user_manager.py

from backend.services.user_manager import (
    crear_usuario,
    buscar_usuario_por_email,
    validar_credenciales,
    eliminar_usuario
)

def test_crear_y_validar_usuario():
    email = "prueba@example.com"
    password = "claveSegura123"
    rol = "admin"

    # Crear usuario
    user = crear_usuario(email, password, rol)
    assert user["email"] == email
    assert user["rol"] == rol

    # Buscar usuario
    user_db = buscar_usuario_por_email(email)
    assert user_db is not None
    assert user_db["email"] == email

    # Validar credenciales correctas
    assert validar_credenciales(email, password) is not None

    # Validar credenciales incorrectas
    assert validar_credenciales(email, "malaClave") is None

    # Eliminar usuario
    assert eliminar_usuario(email) is True

    # Confirmar eliminación
    assert buscar_usuario_por_email(email) is None
