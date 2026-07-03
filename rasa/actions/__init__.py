try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

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
    ActionMarcarEscalarHumano,
    ActionRegistrarIntentoForm,
    ActionVerificarMaxIntentosForm,
    ActionPQRSLLM,
    ActionPreguntasFrecuentesLLM,
    ActionSoporteTecnicoLLM,

)

from .acciones_autenticacion import (
    ActionCheckAuth,
    ActionIngresoZajuna,
    ActionSetAuthenticatedTrue,
    ActionEnviarCorreoRecuperacion,
    
)

from .acciones_academico import (
     ActionVerEstadoEstudiante,
     ActionTutorAsignado,
     ActionHistorialAcademico,
     ActionConsultarHorariosClases,
     ActionConsultarProgresoCurso,
)

from .acciones_encuesta import (
    ActionRegistrarEncuesta,
    ActionGuardarFeedback,
    ActionPreguntarResolucion,
    ActionSetEncuestaTipo,
    ActionFinalizarConversacion,
    ValidateEncuestaSatisfaccionForm,
    ActionLanzarEncuestaGeneral,
    ActionProcesarRespuestaResolucion,
)

from .acciones_llm import (
     ActionHandleWithLLM,
     ActionMemoryWrapper,
)
from .forms.feedback_form import (
     ValidateFeedbackForm,
)

from .acciones_menu import (
    ActionIrMenuPrincipal,
    ActionIrMenuAcademico,
    ActionIrMenuSoporte,
    ActionIrMenuAdministrativo,
)

from .acciones_terminar_conversacion import (
    ActionConfirmarCierre,
    ActionFinalizarConversacion,
    ActionCancelarCierre,
    ActionTerminarConversacionSegura,
)

from .acciones_seguridad import (
    ActionGuardarProgresoEncuesta,
  
)

from .acciones_sesion_segura import (
    ActionNotificarDesconexion,
    ActionNotificarInactividad,
    ActionNotificarReconexion,
    ActionGuardarEstadoSeguridad,
    ActionRecuperarEstadoSeguridad,
    ActionCargarAutosaveMongo,
    ActionAutoresumeConversacion,
)

from .acciones_handoff import (
    ActionOfrecerHumano,
    ActionHandoffCancelar,
    ActionDerivarHumanoConfirmada,
    ActionCancelarDerivacion,
    ActionDerivarYRegistrarHumano,
    ActionHandoffEnCola,
)
from .runtime.actions_support import (
    ActionSoporteLLM,
)

from .runtime.actions_core import (
    ActionExplicarTemaLLM,
)


from .acciones_certificados import (
    ActionRenderCertificados,

)

from .acciones_guardian import (
    ActionAutosaveSnapshot,
    ActionGuardianGuardarProgreso,
    ActionGuardianCargarProgreso,
    ActionGuardianPausar,
    ActionGuardianReanudar,
    ActionGuardianReset,
    ActionRegistrarEncuestaGuardian,
    ActionGuardarAutosave,
    ActionGuardarEncuestaIncompleta,
)


from .acciones_admin import (
    ActionReiniciarConversacion,
    ActionPingServidor,
    ActionSetDefaultTipoUsuario,
    ActionMostrarToken,
    ActionResetTurnosConversacion,
)

from .acciones_tracking import (
    ActionIncrementarTurnosConversacion,


)
from .acciones_session_start import (
    ActionSessionStart,
)

__all__ = [
  
    
    "ActionEnviarCorreo",
    "ActionConectarHumano",
    "ActionHealthCheck",
    "ActionOfrecerContinuarTema",

    "ValidateSoporteForm",
    "ActionEnviarSoporte",
    "ActionSoporteSubmit",
    "ActionEnviarCorreoTutor",
    "ActionProcesarSoporte",
    "ActionMarcarEscalarHumano",
    "ActionRegistrarIntentoForm",
    "ActionVerificarMaxIntentosForm",
    "ActionPQRSLLM",
    "ActionPreguntasFrecuentesLLM",
    "ActionSoporteTecnicoLLM",
    
 
    "ActionCheckAuth",
    "ActionIngresoZajuna",
    "ActionSetAuthenticatedTrue",
    "ActionEnviarCorreoRecuperacion",


    
    "ActionVerEstadoEstudiante",
    "ActionTutorAsignado",
    "ActionZajunaGetEstadoEstudiante",
    "ActionHistorialAcademico",
    "ActionConsultarHorariosClases",
    "ActionConsultarProgresoCurso",

    "ActionRegistrarEncuesta",
    "ActionGuardarFeedback",
    "ActionPreguntarResolucion",
    "ActionSetEncuestaTipo",
    "ValidateEncuestaSatisfaccionForm",
    "ActionLanzarEncuestaGeneral",
    "ActionProcesarRespuestaResolucion",
    "ActionFinalizarConversacion",

    "ActionIrMenuPrincipal",
    "ActionIrMenuSoporte",
    "ActionIrMenuAdministrativo",
    "ActionIrMenuAcademico",

    
    "ActionConfirmarCierre",
    "ActionFinalizarConversacion",
    "ActionCancelarCierre",
    "ActionTerminarConversacionSegura",
    
    
    "ValidateFeedbackForm",

    "ValidateEncuestaSatisfaccionForm",

    "ActionCargarAutosaveMongo",
    "ActionAutoresumeConversacion",
    "ActionResetConversacionSegura",

    "ActionVerificarEstadoEncuestaSegura",
    "ActionGuardarProgresoEncuesta",
    "ActionTerminarConversacionSegura",

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
    "ActionGuardarAutosave",

    "ActionAnalizarEstadoUsuario",


    "ActionRegistrarIntentoForm",
    "ActionVerificarMaxIntentosForm",  
    "ActionOfrecerHumano",
    "ActionHandoffCancelar",
    "ActionDerivarHumanoConfirmada",
    "ActionCancelarDerivacion",
    "ActionDerivarYRegistrarHumano",
    "ActionHandoffEnCola",

    "ActionExplicarErrorActividadLLM",
    "ActionSoporteLLM",
    "ActionHandleWithOllama",
    "ActionRouteLLMIntent",
    "ActionMemoryWrapper",
    "ActionResumenSesionLLM",
    "ActionExplicarTemaLLM",

    "ActionRenderCertificados",
    "ActionMostrarCertificadosCarousel",

    "ActionGuardianGuardarProgreso",
    "ActionGuardianCargarProgreso",
    "ActionGuardianPausar",
    "ActionGuardianReanudar",
    "ActionGuardianReset",
    "ActionRegistrarEncuestaGuardian",
    "ActionGuardarAutosave",
    "ActionGuardarEncuestaIncompleta",


    "ActionReiniciarConversacion",
    "ActionPingServidor",
    "ActionSetDefaultTipoUsuario",
    "ActionMostrarToken",
    "ActionResetTurnosConversacion",

    "ActionIncrementarTurnosConversacion",

    "ActionSessionStart",

]
