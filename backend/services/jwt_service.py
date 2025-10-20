from typing import Optional, Tuple, Dict, Any 
import jwt 
from jwt import InvalidTokenError, PyJWKClient 
from backend.config.settings import settings 
def decode_token(auth_header: Optional[str]) -> Tuple[bool, Dict[str, Any]]: 
""" 
Devuelve (is_valid, claims). Soporta HS* con SECRET_KEY y RS* con JWT_PUBLIC_KEY. 
""" 
if not auth_header or not auth_header.lower().startswith("bearer "): 
return False, {} 
token = auth_header.split(" ", 1)[1].strip() 
alg = settings.jwt_algorithm.upper() 
try: 
if alg.startswith("HS"): 
if not settings.secret_key: 
return False, {} 
claims = jwt.decode(token, settings.secret_key, algorithms=[alg]) 
return True, claims 
if alg.startswith("RS"): 
if not settings.jwt_public_key: 
return False, {} 
claims = jwt.decode(token, settings.jwt_public_key, algorithms=[alg]) 
return True, claims 
# Algoritmo no soportado 
return False, {} 
except InvalidTokenError: 
return False, {}

