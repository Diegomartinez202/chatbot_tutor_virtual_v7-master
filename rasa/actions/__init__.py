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
    ActionEnviarCorreoTutor,
    ActionDerivarYRegistrarHumano,
    ActionProcesarSoporte,
    ActionMarcarEscalarHumano,
)

from .acciones_autenticacion import (
    ValidatePasswordRecoveryForm,
    ActionCheckAuth,
    ActionIngresoZajuna,
    ActionRecuperarContrasena,
    ActionEnviarCorreoRecuperacion,
    ActionSetAuthenticatedTrue,
)

from .acciones_academico import (
    ActionTutorAsignado,
    ActionListarCertificados,
    ZajunaGetCertificados,
    ZajunaGetEstadoEstudiante,
    ActionVerEstadoEstudiante,

)

from .acciones_encuesta import (
    ActionRegistrarEncuesta,
    ActionPreguntarResolucion,
    ActionVerificarEstadoEncuesta,
    ValidateEncuestaSatisfaccionForm,
    ActionGuardarFeedback,
    ActionSetEncuestaTipo,
)

from .acciones_menu import (
    ActionSetMenuPrincipal,
)

from .acciones_terminar_conversacion import (
    ActionConfirmarCierre as ActionConfirmarCierreStd,
    ActionFinalizarConversacion,
    ActionCancelarCierre as ActionCancelarCierreStd,
)

from .acciones_terminar_conversacion_segura import (
    ActionVerificarProcesoActivo,
    ActionConfirmarCierreSeguroFinal,
    ActionCancelarCierreSeguro,
)

from .acciones_terminar_conversacion_segura_autosave import (
    ActionVerificarProcesoActivoAutosave,
    ActionGuardarEncuestaIncompleta,
    ActionConfirmarCierreAutosave,
    ActionCancelarCierreAutosave,
)

from .acciones_conversacion_segura import (
    ActionConfirmarCierreSeguro,
    ActionAutosaveEncuesta,
    ActionCargarAutosaveMongo,
    ActionAutosaveEncuesta,
    ActionAutoresumeConversacion,
    ActionResetConversacionSegura,
)

from .acciones_seguridad import (
    ActionVerificarEstadoEncuestaSegura,
    ActionGuardarProgresoEncuesta,
    ActionTerminarConversacionSegura,
    ActionIrMenuPrincipal,
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
    ActionRegistrarEncuestaGuardian, 
    ActionGuardarAutosave,
)

from .acciones_conversacion_persistente import (
    ActionAutoResume,
    ActionReanudarAuto,
)

from .acciones_cierre_conversacion import (
    ActionAnalizarEstadoUsuario,
)

from .acciones_handoff import (
    ActionRegistrarIntentoForm,
    ActionVerificarMaxIntentosForm,
    ActionOfrecerHumano,
    ActionDerivarYRegistrarHumano,
    ActionHandoffCancelar,
    ActionDerivarHumanoConfirmada,
    ActionCancelarDerivacion,
    ActionHandoffEnCola,
)
from .acciones_certificados import (
    ActionRenderCertificados,
    ActionMostrarCertificadosCarousel,

)

from .acciones_guardian import (
    ActionAutosaveSnapshot,
)
from .acciones_enviar_soporte import (
    ActionEnviarSoporteDirecto,
)
from .acciones_menu_estado_certificados import (
    ActionConsultarCertificados,
)
from .acciones_admin import (
    ActionReiniciarConversacion,
    ActionPingServidor,
    ActionSetDefaultTipoUsuario,
    ActionMostrarToken,
    ActionResetTurnosConversacion,
)
from .acciones_llm import (
    ActionHandleWithOllama,
    ActionRouteLLMIntent,
    ActionMemoryWrapper,
)
from .acciones_tracking import (
    ActionIncrementarTurnosConversacion,

)
__all__ = [
  
    "ValidateSoporteForm",
    "ValidateRecoveryForm",
    "ActionSetDefaultTipoUsuario",
    
    "ActionEnviarCorreo",
    "ActionConectarHumano",
    "ActionHealthCheck",
    "ActionOfrecerContinuarTema",

    "ActionEnviarSoporte",
    "ActionSoporteSubmit",
    "ActionDerivarYRegistrarHumano",

    "ActionCheckAuth",
    "ActionCheckAuthEstado",
    "ActionSyncAuthFromMetadata",
    "ActionSetAuthenticatedTrue",
    "ActionMarkAuthenticated",
    "ActionNecesitaAuth",
    "ActionSubmitRecovery",

    "ActionEstadoEstudiante",
    "ActionVerCertificados",
    "ActionListarCertificados",
    "ActionTutorAsignado",
    "ActionIngresoZajuna",
    "ActionRecuperarContrasena",

    "ActionRegistrarEncuesta",
    "ActionPreguntarResolucion",
    
    "ActionSetMenuPrincipal",
    "ActionVerEstadoEstudiante",
    "ActionConsultarCertificados",

    "ActionConfirmarCierreStd",
    "ActionFinalizarConversacion",
    "ActionCancelarCierreStd",

    "ActionVerificarProcesoActivo",
    "ActionConfirmarCierreSegura",
    "ActionCancelarCierreSegura",

    "ActionVerificarProcesoActivoAutosave",
    "ActionGuardarEncuestaIncompleta",
    "ActionConfirmarCierreAutosave",
    "ActionCancelarCierreAutosave",

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

    "ActionNotificarDesconexion",
    "ActionNotificarInactividad",
    "ActionNotificarReconexion",
    "ActionGuardarEstadoSeguridad",
    "ActionRecuperarEstadoSeguridad",

    "ActionGuardianGuardarProgreso",
    "ActionGuardianCargarProgreso",
    "ActionGuardianPausar",
    "ActionGuardianReanudar",
    "ActionGuardianReset",
    "ActionRegistrarEncuestaGuardian",

    "ActionAutoResume",
    "ActionReanudarAuto",

    "ActionRegistrarIntentoForm",
    "ActionVerificarMaxIntentosForm",

    "ActionOfrecerHumano",
    "ActionHandoffCancelar",

    "ActionConfirmarCierre",
    "ActionCancelarCierre",
 
    "ActionDerivarHumanoConfirmada",
    "ActionCancelarDerivacion",
    "ZajunaGetCertificados",
    "ZajunaGetEstadoEstudiante",
    "ActionHandoffEnCola",
    "ActionAutosaveSnapshot",
        
    "ValidatePasswordRecoveryForm",
    "ActionEnviarCorreoRecuperacion",
    "ActionReiniciarConversacion",
    "ActionMostrarToken",
    "ActionPingServidor",

    "ActionVerificarEstadoEncuesta",
    "ValidateEncuestaSatisfaccionForm",
    "ActionGuardarFeedback",

    "ActionAnalizarEstadoUsuario",

    "ActionHandleWithOllama",
    "ActionRouteLLMIntent",
    "ActionMemoryWrapper",
    "ActionEnviarCorreoTutor",
    "ActionProcesarSoporte",
    "ActionMarcarEscalarHumano",

    "ActionSetEncuestaTipo",
    "ActionVerificarProcesoActivo",

    "ActionConfirmarCierreSeguroFinal",
    "ActionCancelarCierreSeguro",

   "ActionRenderCertificados",
   "ActionResetTurnosConversacion",

   "ActionMostrarCertificadosCarousel",

   "ActionIncrementarTurnosConversacion",
]
