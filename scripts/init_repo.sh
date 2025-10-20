#!/bin/bash
echo "ðŸš€ Inicializando repositorio Git..."

# Inicializar Git si no existe
if [ ! -d .git ]; then
  git init
  echo "âœ… Repositorio Git inicializado"
else
  echo "â„¹ï¸ Git ya estÃ¡ inicializado"
fi

# Crear README si no existe
if [ ! -f README.md ]; then
  echo "# Chatbot Tutor Virtual" > README.md
  echo "ðŸ“ README.md creado"
fi

# Crear LICENSE si no existe
if [ ! -f LICENSE ]; then
  curl -s https://raw.githubusercontent.com/github/choosealicense.com/gh-pages/_licenses/mit.txt > LICENSE
  sed -i "s/[year]/2025/g; s/[fullname]/Daniel MartÃ­nez/g" LICENSE
  echo "ðŸ“œ LICENSE MIT creada"
fi

# Hacer primer commit
git add .
git commit -m "ðŸŽ‰ Proyecto inicial con README y LICENSE"

# Crear repo en GitHub (manual si no tienes GitHub CLI)
echo "ðŸ“Œ Recuerda crear el repositorio en GitHub manualmente y luego ejecutar:"
echo "git remote add origin https://github.com/TU_USUARIO/TU_REPO.git"
echo "git push -u origin main"
