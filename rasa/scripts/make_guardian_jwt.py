# scripts/make_guardian_jwt.py
import os, jwt, datetime

JWT_SECRET   = os.getenv("JWT_SECRET", "change-me-in-prod")
JWT_ALG      = os.getenv("JWT_ALG", "HS256")
JWT_ISSUER   = os.getenv("JWT_ISSUER", "guardian-api")
JWT_AUDIENCE = os.getenv("JWT_AUDIENCE", "zajuna-client")

def make_token(user_id: str) -> str:
    now = datetime.datetime.utcnow()
    payload = {
        "sub": user_id,
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE,
        "iat": now,
        "exp": now + datetime.timedelta(hours=12),
        "scope": "autosave:rw",
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)

if __name__ == "__main__":
    print(make_token("demo-user-123"))
