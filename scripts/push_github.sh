#!/bin/bash

echo "ðŸ“¦ Iniciando push a GitHub..."

# Verificar si estamos en un repositorio Git
if [ ! -d ".git" ]; then
  echo "âŒ Este directorio no es un repositorio Git. Ejecuta 'git init' primero."
  exit 1
fi

# Mostrar cambios pendientes
git status

# Agregar todos los cambios
git add .

# Confirmar con mensaje estÃ¡ndar
echo "ðŸ“ Ingresando commit..."
git commit -m "ðŸš€ Primer push del proyecto Chatbot Tutor Virtual v2"

# Confirmar si el repositorio remoto estÃ¡ configurado
REMOTE=$(git remote get-url origin 2>/dev/null)

if [ -z "$REMOTE" ]; then
  echo "âŒ No se ha configurado el repositorio remoto."
  echo "âž¡ï¸ Usa este comando (reemplaza tu URL):"
  echo "   git remote add origin https://github.com/tu_usuario/tu_repositorio.git"
  exit 1
fi

# Hacer push a la rama principal
echo "ðŸš€ Enviando cÃ³digo a GitHub..."
git push -u origin main

echo "âœ… Push completado exitosamente."
