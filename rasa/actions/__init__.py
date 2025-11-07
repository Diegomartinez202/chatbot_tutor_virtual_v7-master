# rasa/actions/__init__.py
from .acciones_general import (
    ActionEnviarCorreo,
    ActionConectarHumano,
    ActionHealthCheck,
    ActionOfrecerContinuarTema,
)

from .acciones_soporte import (
    ValidateSoporteForm,
    ActionEnviarSoporte,
    ActionSoporteSubmit,
    ActionSubmitSoporte,
    ActionDerivarYRegistrarHumano,
)

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

from .acciones_academico import (
    ActionEstadoEstudiante,
    ActionVerCertificados,
    ActionListarCertificados,
    ActionTutorAsignado,
    ActionIngresoZajuna,
    ActionRecuperarContrasena,
)

from .acciones_encuesta import (
    ActionRegistrarEncuesta,
    ActionPreguntarResolucion,
    ActionSetEncuestaTipo,
)

# Alias por compatibilidad con nombre con typo
from .accines_encuesta import (
    ActionRegistrarEncuesta as _AliasActionRegistrarEncuesta,
    ActionPreguntarResolucion as _AliasActionPreguntarResolucion,
)
from .actions_menu import (
    ActionSetMenuPrincipal,
    ActionVerEstadoEstudiante,
    ActionConsultarCertificados,
)
from .actions_terminar_conversacion import (
    ActionConfirmarCierre,
    ActionFinalizarConversacion,
    ActionCancelarCierre,
)
from .actions_terminar_conversacion_segura import (
    ActionVerificarProcesoActivo,
    ActionConfirmarCierre,
    ActionCancelarCierre,
)
from .actions_terminar_conversacion_segura_autosave import (
    ActionVerificarProcesoActivoAutosave,
    ActionGuardarEncuestaIncompleta,
    ActionConfirmarCierreAutosave,
    ActionCancelarCierre,
)
from .acciones_conversacion_segura import (
    ActionVerificarEstadoConversacion,
    ActionGuardarProgresoConversacion,
    ActionTerminarConversacionSegura,
    ActionReanudarConversacionSegura,
)
from .conversacion_segura import (
    ActionConfirmarCierreSeguro,
    ActionAutoSaveEncuesta,
    ActionGuardarAutoSaveMongo,
    ActionCargarAutoSaveMongo,
    ActionAutoResumeConversacion,
    ActionResetConversacionSegura,
)

from .acciones_sesion_segura import (
    ActionNotificarDesconexion,
    ActionNotificarInactividad,
    ActionNotificarReconexion,
    ActionGuardarEstadoSeguridad,
    ActionRecuperarEstadoSeguridad,
)
from .acciones_seguridad_guardian import (
    ActionGuardianGuardarProgreso,
    ActionGuardianCargarProgreso,
    ActionGuardianPausar,
    ActionGuardianReanudar,
    ActionGuardianReset,
    ActionRegistrarEncuesta,
)
from .acciones_conversacion_persistente import (
    ActionAutoResume,
    ActionReanudarAuto,
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

    # Encuesta / resolución
    "ActionRegistrarEncuesta",
    "ActionPreguntarResolucion",
    "ActionSetEncuestaTipo",
    "ActionSetMenuPrincipal",
    "ActionVerEstadoEstudiante",
    "ActionConsultarCertificados",

    "ActionConfirmarCierre",
    "ActionFinalizarConversacion",
    "ActionCancelarCierre",
    "ActionVerificarProcesoActivo",
    "ActionConfirmarCierre",
   
    "ActionVerificarProcesoActivoAutosave",
    "ActionGuardarEncuestaIncompleta",
    "ActionConfirmarCierreAutosave",

     "ActionVerificarEstadoConversacion",
    "ActionGuardarProgresoConversacion",
    "ActionTerminarConversacionSegura",
    "ActionReanudarConversacionSegura",
    "ActionAutoResume",
    "ActionReanudarAuto"

   
    "ActionOfrecerContinuarTema",
    "ActionConfirmarCierreSeguro",
    "ActionAutoSaveEncuesta",
    "ActionGuardarAutoSaveMongo",
    "ActionCargarAutoSaveMongo",
    "ActionAutoResumeConversacion",
    "ActionResetConversacionSegura",

   "ActionNotificarDesconexion",
   "ActionNotificarInactividad",
   "ActionNotificarReconexion",
   "ActionGuardarEstadoSeguridad",
   "ActionRecuperarEstadoSeguridad",

   "ActionGuardianGuardarProgreso",
   "ActionGuardianCargarProgreso",
   "ActionGuardianPausar",
   "ActionGuardianReanudar",
   "ActionGuardianReset"

   "ActionGuardianGuardarProgreso",
   "ActionGuardianCargarProgreso",
   "ActionGuardianPausar",
   "ActionGuardianReanudar",
   "ActionGuardianReset",
   "ActionRegistrarEncuesta",
]
    


