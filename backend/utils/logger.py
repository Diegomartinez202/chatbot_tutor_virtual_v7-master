# backend/logger.py
"""
Compatibilidad: Este módulo permite que el código existente que importe `logger`
desde `backend/logger.py` siga funcionando, pero internamente se apoya
en el sistema unificado de logging definido en `backend/utils/logging.py`.
"""

from backend.utils.logging import get_logger

# Logger principal para compatibilidad
logger = get_logger("chatbot")