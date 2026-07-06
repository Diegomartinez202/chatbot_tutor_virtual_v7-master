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
     ActionConsultarCertificados,
)

from .acciones_encuesta import (
    ActionRegistrarEncuesta,
    ActionGuardarFeedback,
    ActionPreguntarResolucion,
    ActionSetEncuestaTipo,
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
    ActionCancelarCierre,
    ActionTerminarConversacionSegura,
    ActionDecidirCierre,
    ActionCierreLimpio,
    ActionFinalizarCierre,

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

from .acciones_guardian import (
    ActionAutosaveSnapshot,
    ActionGuardianGuardarProgreso,
    ActionGuardianCargarProgreso,
    ActionGuardianPausar,
    ActionGuardianReanudar,
    ActionGuardianReset,
    ActionRegistrarEncuestaGuardian,
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
    "ActionFinalizarCierre",

    "ActionIrMenuPrincipal",
    "ActionIrMenuSoporte",
    "ActionIrMenuAdministrativo",
    "ActionIrMenuAcademico",

    
    "ActionConfirmarCierre",
    "ActionCancelarCierre",
    "ActionTerminarConversacionSegura",
     
    "ActionDecidirCierre",
    "ActionCierreLimpio",
   
    
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

    "ActionConsultarCertificados",
   

    "ActionGuardianGuardarProgreso",
    "ActionGuardianCargarProgreso",
    "ActionGuardianPausar",
    "ActionGuardianReanudar",
    "ActionGuardianReset",
    "ActionRegistrarEncuestaGuardian",
    "ActionGuardarAutosave",


    "ActionReiniciarConversacion",
    "ActionPingServidor",
    "ActionSetDefaultTipoUsuario",
    "ActionMostrarToken",
    "ActionResetTurnosConversacion",

    "ActionIncrementarTurnosConversacion",

    "ActionSessionStart",

]
