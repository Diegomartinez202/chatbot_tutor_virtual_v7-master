from pydantic import BaseModel, Field

class LoginRequest(BaseModel):
    """📥 Solicitud de inicio de sesión."""
    email: str = Field(..., example="usuario@correo.com")
    password: str = Field(..., example="123456")

class TokenResponse(BaseModel):
    """🔑 Respuesta con tokens de autenticación."""
    access_token: str = Field(..., description="Token de acceso JWT")
    refresh_token: str = Field(..., description="Token de refresco JWT")
    token_type: str = Field(default="bearer", description="Tipo de token (por defecto: bearer)")
