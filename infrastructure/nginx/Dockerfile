FROM nginx:1.27-alpine

# Copia el build del frontend (ajusta el origen si tu pipeline lo genera a otro path)
# Si vas a servir sólo el frontend aquí:
# COPY --from=builder /app/dist/ /usr/share/nginx/html/

# Conf Nginx
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
