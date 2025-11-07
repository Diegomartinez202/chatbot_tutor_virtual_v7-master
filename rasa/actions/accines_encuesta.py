# rasa/actions/accines_encuesta.py
# Alias por compatibilidad: reexporta desde acciones_encuesta
from .acciones_encuesta import ActionRegistrarEncuesta, ActionPreguntarResolucion

__all__ = ["ActionRegistrarEncuesta", "ActionPreguntarResolucion"]
