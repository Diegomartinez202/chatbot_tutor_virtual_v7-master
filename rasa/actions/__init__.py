# rasa/actions/__init__.py

# ======= General =======
from .acciones_general import (
    ActionEnviarCorreo,
    ActionConectarHumano,
    ActionHealthCheck,
    ActionOfrecerContinuarTema,
)

# ======= Soporte =======
from .acciones_soporte import (
    ValidateSoporteForm,
    ActionEnviarSoporte,
    ActionSoporteSubmit,
    ActionSubmitSoporte,
    ActionDerivarYRegistrarHumano,
)

# ======= Autenticación =======
from .acciones_autenticacion import (
    ValidateRecoveryForm,
    ActionCheckAuth,
    ActionCheckAuthEstado,
    ActionSyncAuthFromMetadata,
    ActionSetAuthenticatedTrue,
    ActionMarkAuthenticated,
    ActionNecesitaAuth,
    ActionSubmitRecovery,
)

# ======= Académico =======
from .acciones_academico import (
    ActionEstadoEstudiante,
    ActionVerCertificados,
    ActionListarCertificados,
    ActionTutorAsignado,
    ActionIngresoZajuna,
    ActionRecuperarContrasena,
    ZajunaGetCertificados,
    ZajunaGetEstadoEstudiante,
)

# ======= Encuesta =======
from .acciones_encuesta import (
    ActionRegistrarEncuesta,
    ActionPreguntarResolucion,
    ActionSetEncuestaTipo,
)

# Alias de compatibilidad por typo en nombre de archivo
from .accines_encuesta import (  # noqa: F401
    ActionRegistrarEncuesta as _AliasActionRegistrarEncuesta,
    ActionPreguntarResolucion as _AliasActionPreguntarResolucion,
)

# ======= Menú / Acciones de acceso rápido =======
from .acciones_menu import (
    ActionSetMenuPrincipal,
    ActionVerEstadoEstudiante,
    ActionConsultarCertificados,
)

# ======= Cierre conversación (versión estándar) =======
from .acciones_terminar_conversacion import (
    ActionConfirmarCierre as ActionConfirmarCierreStd,
    ActionFinalizarConversacion,
    ActionCancelarCierre as ActionCancelarCierreStd,
)

# ======= Cierre segura (otra variante) =======
from .acciones_terminar_conversacion_segura import (
    ActionVerificarProcesoActivo,
    ActionConfirmarCierre as ActionConfirmarCierreSegura,
    ActionCancelarCierre as ActionCancelarCierreSegura,
)

# ======= Cierre segura + autosave =======
from .acciones_terminar_conversacion_segura_autosave import (
    ActionVerificarProcesoActivoAutosave,
    ActionGuardarEncuestaIncompleta,
    ActionConfirmarCierreAutosave,
    ActionCancelarCierre as ActionCancelarCierreAutosave,
)

# ======= Conversación segura (guardian/autosave) =======
from .acciones_conversacion_segura import (
    ActionVerificarEstadoConversacion,
    ActionGuardarProgresoConversacion,
    ActionTerminarConversacionSegura,
    ActionReanudarConversacionSegura,
)

from .acciones_conversacion_segura import (
    ActionConfirmarCierreSeguro,
    ActionAutoSaveEncuesta,
    ActionGuardarAutoSaveMongo,
    ActionCargarAutoSaveMongo,
    ActionAutoResumeConversacion,
    ActionResetConversacionSegura,
)

# ======= Sesión segura (eventos) =======
from .acciones_sesion_segura import (
    ActionNotificarDesconexion,
    ActionNotificarInactividad,
    ActionNotificarReconexion,
    ActionGuardarEstadoSeguridad,
    ActionRecuperarEstadoSeguridad,
)

# ======= Guardian (Mongo autosave) =======
from .acciones_seguridad_guardian import (
    ActionGuardianGuardarProgreso,
    ActionGuardianCargarProgreso,
    ActionGuardianPausar,
    ActionGuardianReanudar,
    ActionGuardianReset,
    ActionRegistrarEncuesta as ActionRegistrarEncuestaGuardian,  # no pisa el otro
)

# ======= Conversación persistente =======
from .acciones_conversacion_persistente import (
    ActionAutoResume,
    ActionReanudarAuto,
)
from .acciones_handoff_fallback import (
    ActionRegistrarIntentoForm,
    ActionVerificarMaxIntentosForm,
)
from .acciones_cierre_conversacion import (
    ActionConfirmarCierre,
    ActionFinalizarConversacion,
    ActionCancelarCierre,
)

from .acciones_handoff import (
    ActionRegistrarIntentoForm,
    ActionVerificarMaxIntentosForm,
    ActionOfrecerHumano,
    ActionDerivarYRegistrarHumano as ActionDerivarYRegistrarHumano_HandoffAlias,
    ActionHandoffCancelar,
    ActionDerivarHumanoConfirmada,
    ActionCancelarDerivacion,
)
from .acciones_certificados import (
    ActionConsultarCertificados,  # ← NUEVA
)
__all__ = [
    # Validators
    "ValidateSoporteForm",
    "ValidateRecoveryForm",

    # Core utility / email / health / humano
    "ActionEnviarCorreo",
    "ActionConectarHumano",
    "ActionHealthCheck",
    "ActionOfrecerContinuarTema",

    # Soporte
    "ActionEnviarSoporte",
    "ActionSoporteSubmit",
    "ActionSubmitSoporte",
    "ActionDerivarYRegistrarHumano",

    # Auth / gates y sync
    "ActionCheckAuth",
    "ActionCheckAuthEstado",
    "ActionSyncAuthFromMetadata",
    "ActionSetAuthenticatedTrue",
    "ActionMarkAuthenticated",
    "ActionNecesitaAuth",
    "ActionSubmitRecovery",

    # Flujos académicos
    "ActionEstadoEstudiante",
    "ActionVerCertificados",
    "ActionListarCertificados",
    "ActionTutorAsignado",
    "ActionIngresoZajuna",
    "ActionRecuperarContrasena",

    # Encuesta / resolución (ambas referencias válidas)
    "ActionRegistrarEncuesta",
    "ActionPreguntarResolucion",
    "ActionSetEncuestaTipo",

    # Menú / accesos
    "ActionSetMenuPrincipal",
    "ActionVerEstadoEstudiante",
    "ActionConsultarCertificados",

    # Cierre conversación (usa explícitamente la estándar por defecto)
    "ActionConfirmarCierreStd",
    "ActionFinalizarConversacion",
    "ActionCancelarCierreStd",

    # Cierre conversación segura
    "ActionVerificarProcesoActivo",
    "ActionConfirmarCierreSegura",
    "ActionCancelarCierreSegura",

    # Cierre segura + autosave
    "ActionVerificarProcesoActivoAutosave",
    "ActionGuardarEncuestaIncompleta",
    "ActionConfirmarCierreAutosave",
    "ActionCancelarCierreAutosave",

    # Conversación segura (guardian/autosave)
    "ActionVerificarEstadoConversacion",
    "ActionGuardarProgresoConversacion",
    "ActionTerminarConversacionSegura",
    "ActionReanudarConversacionSegura",

    "ActionConfirmarCierreSeguro",
    "ActionAutoSaveEncuesta",
    "ActionGuardarAutoSaveMongo",
    "ActionCargarAutoSaveMongo",
    "ActionAutoResumeConversacion",
    "ActionResetConversacionSegura",

    # Sesión segura
    "ActionNotificarDesconexion",
    "ActionNotificarInactividad",
    "ActionNotificarReconexion",
    "ActionGuardarEstadoSeguridad",
    "ActionRecuperarEstadoSeguridad",

    # Guardian
    "ActionGuardianGuardarProgreso",
    "ActionGuardianCargarProgreso",
    "ActionGuardianPausar",
    "ActionGuardianReanudar",
    "ActionGuardianReset",
    "ActionRegistrarEncuestaGuardian",

    # Conversación persistente
    "ActionAutoResume",
    "ActionReanudarAuto",

    "ActionRegistrarIntentoForm",
    "ActionVerificarMaxIntentosForm",

    "ActionOfrecerHumano",
    "ActionHandoffCancelar",

    "ActionConfirmarCierre",
    "ActionFinalizarConversacion",
    "ActionCancelarCierre",
    
 
    "ActionDerivarHumanoConfirmada",
    "ActionCancelarDerivacion",
    "ActionConsultarCertificados",   
    "ZajunaGetCertificados",
    "ZajunaGetEstadoEstudiante",
]
