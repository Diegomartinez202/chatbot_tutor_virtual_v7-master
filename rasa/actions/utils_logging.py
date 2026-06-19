# ruta: rasa/actions/utils_logging.py
from __future__ import annotations

import logging
from typing import Optional


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Inicializa o recupera un logger configurado de manera única por módulo.
    Garantiza un formato legible y previene la duplicación de logs en consola.
    """
    # 1. Resolver el nombre del módulo actual de forma segura
    logger_name = name or __name__
    logger = logging.getLogger(logger_name)

    # 2. Configurar el nivel base antes de enlazar los flujos
    logger.setLevel(logging.INFO)

    # 3. CORRECCIÓN: Validar limpiamente la ausencia de manejadores para evitar fugas o silencios
    if not logger.handlers:
        handler = logging.StreamHandler()
        
        # Preserva intacta tu estructura original de traza
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    # 4. MEJORA: Apagar la propagación para evitar duplicidad de líneas en los logs del contenedor Docker
    logger.propagate = False

    return logger