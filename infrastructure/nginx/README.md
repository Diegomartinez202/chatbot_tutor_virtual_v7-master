# Nginx para Frontend + Proxy API

## Build & Push (Docker Hub)
```bash
# en la raíz del repo
docker build -t TUUSER/nginx-chatbot:latest -f infrastructure/nginx/Dockerfile .
docker push TUUSER/nginx-chatbot:latest
Railway (dos servicios)
•	Service A: backend (FastAPI en puerto 8000)
•	Service B: nginx (esta imagen) en puerto 80
Variables/Networking
•	En Railway, crea un Private Networking o usa nombres de servicio:
o	En nginx.conf, proxy_pass http://backend:8000/; donde backend es el nombre DNS del servicio FastAPI.
•	Asegúrate de tener client_max_body_size 20m; en nginx.conf (ya incluido).
Frontend estático
•	Si compilas el frontend en CI, copia /dist dentro de la imagen Nginx (añade un stage builder o usa artefactos del pipeline).
•	Alternativamente, sirve el frontend desde un CDN y usa Nginx sólo como reverse proxy.
TLS
•	Para TLS gestiona con Railway Add-ons, Cloudflare, o un Nginx con certbot (no incluido aquí).
