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
    ActionEnviarCorreoTutor,
    ActionDerivarYRegistrarHumano,
    ActionProcesarSoporte,
    ActionMarcarEscalarHumano,
)

# ======= Autenticación =======
from .acciones_autenticacion import (
    ValidatePasswordRecoveryForm,
    ActionCheckAuth,
    ActionIngresoZajuna,
    ActionRecuperarContrasena,
    ActionEnviarCorreoRecuperacion,
    ActionSetAuthenticatedTrue,
)

# ======= Académico =======
from .acciones_academico import (
    ActionEstadoEstudiante,
    ActionTutorAsignado,
    ActionListarCertificados,
    ActionVerCertificados,
    ActionIngresoZajuna,
    ActionRecuperarContrasena,
    ZajunaGetCertificados,
    ZajunaGetEstadoEstudiante,
    ActionVerEstadoEstudiante,

)
# ======= Encuesta =======
from .acciones_encuesta import (
    ActionRegistrarEncuesta,
    ActionPreguntarResolucion,
    ActionVerificarEstadoEncuesta,
    ValidateEncuestaSatisfaccionForm,
    ActionGuardarFeedback,
    ActionSetEncuestaTipo,
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
    ActionConfirmarCierreSeguroFinal,
    ActionCancelarCierreSeguro
)

# ======= Cierre segura + autosave =======
from .acciones_terminar_conversacion_segura_autosave import (
    ActionVerificarProcesoActivoAutosave,
    ActionGuardarEncuestaIncompleta,
    ActionConfirmarCierreAutosave,
    ActionCancelarCierreAutosave,
)

# ======= Conversación segura (guardian/autosave) =======
from .acciones_conversacion_segura import (
    ActionConfirmarCierreSeguro,
    ActionAutosaveEncuesta,
    ActionCargarAutosaveMongo,
    ActionAutosaveEncuesta,
    ActionAutoresumeConversacion,
    ActionResetConversacionSegura,
)

from .acciones_seguridad import (
    ActionVerificarEstadoEncuesta,
    ActionGuardarProgresoEncuesta,
    ActionTerminarConversacionSegura,
    ActionIrMenuPrincipal,
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
    ActionRegistrarEncuesta, 
    ActionGuardarAutosave,
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
    ActionConsultarCertificados,  
)

from .acciones_guardian import (
    ActionAutosaveSnapshot,
)
from .acciones_enviar_soporte import (
    ActionEnviarSoporte,
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
)
from .acciones_llm import (
    ActionHandleWithOllama,
    ActionRouteLLMIntent,
    ActionMemoryWrapper,
)

__all__ = [
    # Validators
    "ValidateSoporteForm",
    "ValidateRecoveryForm",
    "ActionSetDefaultTipoUsuario",
    # Core utility / email / health / humano
    "ActionEnviarCorreo",
    "ActionConectarHumano",
    "ActionHealthCheck",
    "ActionOfrecerContinuarTema",

    # Soporte
    "ActionEnviarSoporte",
    "ActionSoporteSubmit",
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
    "ActionCancelarCierre",
 
    "ActionDerivarHumanoConfirmada",
    "ActionCancelarDerivacion",
    "ZajunaGetCertificados",
    "ZajunaGetEstadoEstudiante",
    "ActionHandoffEnCola",
    "ActionAutosaveSnapshot",
        
    "ValidatePasswordRecoveryForm",
    "ActionEnviarCorreoRecuperacion",
    "ActionPreguntarResolucion",

    "ActionReiniciarConversacion",
    "ActionMostrarToken",
    "ActionPingServidor",

    "ActionRegistrarEncuesta",
    "ActionPreguntarResolucion",
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
]
