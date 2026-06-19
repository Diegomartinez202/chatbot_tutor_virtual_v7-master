#!/bin/bash
# check_embed.sh â€” Verifica CSP, redirects y health del backend
# Uso: ./check_embed.sh https://tu-backend.com

BACKEND_URL=${1:-"http://localhost:8000"}

echo "ðŸ” Probando /chat-embed.html..."
curl -I "$BACKEND_URL/chat-embed.html" | grep -iE "HTTP|location|content-security-policy"

echo -e "\nðŸ” Probando Content-Security-Policy header..."
curl -s -D- "$BACKEND_URL/chat-embed.html" -o /dev/null | grep -i "^content-security-policy:"

echo -e "\nðŸ” Probando redirect de /widget.html â†’ /chat-embed.html..."
curl -I "$BACKEND_URL/widget.html" | grep -iE "HTTP|location"

echo -e "\nðŸ” Probando redirect de /static/widgets/widget.html â†’ /chat-embed.html..."
curl -I "$BACKEND_URL/static/widgets/widget.html" | grep -iE "HTTP|location"

echo -e "\nðŸ” Probando redirect de /embedded.js â†’ FRONTEND /chat-widget.js..."
curl -I "$BACKEND_URL/embedded.js" | grep -iE "HTTP|location"

echo -e "\nðŸ” Probando API health..."
curl -s "$BACKEND_URL/chat/health" | jq 2>/dev/null || curl -s "$BACKEND_URL/chat/health"

echo -e "\nâœ… VerificaciÃ³n completada."
