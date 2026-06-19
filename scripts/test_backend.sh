#!/bin/bash

echo "ðŸš€ Ejecutando pruebas del backend..."

# Ir a raÃ­z del proyecto (desde la ubicaciÃ³n del script)
cd "$(dirname "$0")/.."

# Ejecutar pruebas del backend
cd backend
pytest test/

# Regresar a la raÃ­z si se desea continuar con otras tareas
cd ..
