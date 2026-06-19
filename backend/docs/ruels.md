version: "3.1"

rules:

  - rule: Ir siempre al menú principal
    steps:
      - intent: ir_menu_principal
      - action: utter_menu_principal
  
  - rule: Limpiar sesión (alias de reinicio)
    steps:
      - intent: limpiar_sesion
      - action: action_reiniciar_conversacion

  - rule: Ping servidor admin
    steps:
      - intent: ping_servidor
      - action: action_ping_servidor

  - rule: Submit auth_login_form OK
    condition:
      - active_loop: auth_login_form
    steps:
      - action: auth_login_form
      - active_loop: null
      - action: action_ingreso_zajuna
      - action: action_set_authenticated_true
      - action: utter_auth_ok

  - rule: Submit auth_login_form FAIL (manual)
    condition:
      - active_loop: auth_login_form
    steps:
      - intent: deny
      - action: action_deactivate_loop
      - active_loop: null
      - action: utter_auth_fail
  
  - rule: Confirmar autenticación directa 
    steps:
      - intent: confirmar_autenticacion
      - action: action_set_authenticated_true
      - action: utter_auth_ok
      - action: utter_confirmacion_consulta

  - rule: Iniciar recuperación por intent
    steps:
      - intent: recuperar_contrasena
      - action: utter_recuperar_acceso_cta
      - action: password_recovery_form
      - active_loop: password_recovery_form

  - rule: Submit password_recovery_form
    condition:
      - active_loop: password_recovery_form
    steps:
      - action: password_recovery_form
      - active_loop: null
      - action: action_recuperar_contrasena
      - action: action_enviar_correo_recuperacion
      - action: utter_recuperacion_enviada
  
  - rule: Iniciar flujo de login pidiendo email
    steps:
      - intent: auth_login_cmd
      - action: utter_ask_email
      - action: auth_login_form
      - active_loop: auth_login_form
  
  - rule: Iniciar login por enviar_credenciales
    steps:
      - intent: enviar_credenciales
      - action: auth_login_form
      - active_loop: auth_login_form
  
  - rule: Limpiar autosave
    steps:
      - intent: limpiar_autosave
      - action: action_reset_conversacion_segura
      - action: utter_limpiar_autosave
  
  - rule: Cambiar idioma a español
    steps:
      - intent: cambiar_idioma_espanol
      - action: utter_cambiar_idioma_espanol

  - rule: Cambiar idioma a inglés
    steps:
      - intent: cambiar_idioma_ingles
      - action: utter_cambiar_idioma_ingles

  - rule: Mostrar catálogo
    steps:
      - intent: explorar_temas
      - action: utter_catalogo_cursos
  
  - rule: Guardar snapshot manual (Guardian)
    steps:
      - intent: guardar_snapshot
      - action: action_autosave_snapshot
      - action: utter_guardian_snapshot_ok
  
  - rule: Ayuda sobre Guardian
    steps:
      - intent: ayuda_guardian
      - action: utter_guardian_help
  
  - rule: Guardar progreso explícito
    steps:
      - intent: guardian_guardar_progreso
      - action: action_guardian_guardar_progreso

  - rule: Pausar conversación segura
    steps:
      - intent: guardian_pausar_conversacion
      - action: action_guardian_pausar

  - rule: Guardar estado en desconexión
    steps:
      - intent: notificar_desconexion
      - action: action_notificar_desconexion
      - action: action_guardar_estado_seguridad
      - action: utter_notificar_desconexion

  - rule: Reanudar conversación automática
    steps:
      - intent: reanudar_conversacion
      - action: action_cargar_autosave_mongo
      - action: action_autoresume_conversacion

  - rule: Restaurar estado en reconexión
    steps:
      - intent: notificar_reconexion
      - action: action_recuperar_estado_seguridad
      - action: action_notificar_reconexion
  
  - rule: Guardar estado bajo demanda
    steps:
      - intent: guardar_estado
      - action: action_guardar_estado_seguridad
      - action: utter_guardando_progreso

  - rule: Recuperar estado bajo demanda
    steps:
      - intent: recuperar_estado_seguridad
      - action: action_recuperar_estado_seguridad

  - rule: Enviar correo a tutor
    steps:
      - intent: enviar_correo_tutor
      - action: utter_contactar_tutor_confirmacion
      - action: action_enviar_correo_tutor
      - action: utter_correo_enviado
      - action: utter_ofrecer_continuar

  - rule: Cancelar cierre seguro con autosave (alineada con stories)
    steps:
      - intent: cancelar_cierre_autosave
      - action: action_cancelar_cierre_autosave
      - action: utter_cierre_cancelado_seguro
      - action: action_ir_menu_principal
  
  - rule: Terminar conversación segura con autosave dentro de soporte_form
    condition:
      - active_loop: soporte_form
    steps:
      - intent: terminar_conversacion_segura_autosave
      - action: action_deactivate_loop
      - active_loop: null
      - action: action_verificar_proceso_activo_autosave
 
  - rule: Enviar correo genérico
    steps:
      - intent: enviar_correo
      - action: action_enviar_correo

  - rule: Detectar que necesita autenticación
    steps:
      - intent: necesita_auth
      - action: utter_necesita_autenticacion  
  
  - rule: Usuario cancela la acción actual
    steps:
      - intent: cancelar
      - action: utter_cancelar_accion
 
  - rule: Usuario confirma derivación a humano
    steps:
      - intent: confirmar_derivacion
      - action: utter_confirmar_derivacion

  - rule: Usuario dice 'continue'
    steps:
      - intent: continue
      - action: utter_continuar_tema_menu

  - rule: Usuario inicia feedback directo
    steps:
      - intent: dar_retroalimentacion
      - action: utter_iniciar_retroalimentacion
      - action: feedback_form
      - active_loop: feedback_form
  
  - rule: Usuario reporta error en actividad
    steps:
      - intent: error_actividad
      - action: utter_error_actividad_ayuda
  
  - rule: Usuario pide horarios o calendario
    steps:
      - intent: horarios_calendario
      - action: utter_horarios_calendario_info
  
  - rule: Usuario usa intent iniciar_sesion
    steps:
      - intent: iniciar_sesion
      - action: utter_redirigir_login
 
  - rule: Usuario niega autenticación
    steps:
      - intent: negar_autenticacion
      - action: utter_negar_autenticacion
  
  - rule: Usuario reporta pantalla blanca
    steps:
      - intent: pantalla_blanca
      - action: utter_pantalla_blanca_ayuda
  
  - rule: Usuario tiene problema para ingresar
    steps:
      - intent: problema_no_ingreso
      - action: utter_problema_no_ingreso
  
  - rule: Usuario pide ver proceso académico
    steps:
      - intent: proceso_academico
      - action: utter_menu_academico
  
  - rule: Usuario abre submenú académico
    steps:
      - intent: proceso_academico_secundario
      - action: utter_menu_academico
  
  - rule: Usuario envía correo fuera de formularios
    condition:
      - active_loop: null
    steps:
      - intent: provide_email
      - action: utter_confirmar_email
  
  - rule: Usuario pide soporte técnico
    steps:
      - intent: soporte_tecnico
      - action: utter_menu_soporte
  
  - rule: Usuario quiere ver link de soporte
    steps:
      - intent: ver_link_soporte
      - action: utter_ver_link_soporte
  
  - rule: Usuario quiere ver información del soporte creado
    steps:
      - intent: ver_soporte_creado_info
      - action: utter_ver_soporte_creado_info

  - rule: Mostrar menú principal rápido
    steps:
      - intent: menu_rapido
      - action: action_ir_menu_principal

  - rule: Pedir nombre fuera de formulario
    steps:
      - intent: pedir_nombre      
      - action: utter_ask_nombre

  - rule: Reinicio confirmado
    steps:
      - intent: reiniciar_conversacion
      - action: action_reiniciar_conversacion
      - action: utter_reinicio_confirmado
  
  - rule: Capturar URL de soporte
    steps:
      - intent: enviar_url
      - action: utter_gracias_url
  
  - rule: Usuario decide no continuar con el tema actual
    steps:
      - intent: continuar_tema_no
      - action: utter_no_continuar_tema
      - action: utter_menu_principal

  - rule: Pedir usuario en feedback_form
    condition:
      - active_loop: feedback_form
    steps:
      - action: utter_ask_usuario

  - rule: Pedir texto de feedback en feedback_form
    condition:
      - active_loop: feedback_form
    steps:
      - action: utter_ask_feedback_texto

  - rule: Cancelar cierre seguro
    steps:
      - intent: cancelar_cierre_segura
      - action: action_cancelar_cierre_segura
      - action: utter_cierre_cancelado_seguro
      - action: action_ir_menu_principal
  
  - rule: Terminar conversación
    steps:
      - intent: terminar_conversacion
      - action: action_verificar_proceso_activo_autosave
      - action: action_resumen_sesion_llm
      - action: utter_despedida_profesional
  
  - rule: Usuario cancela cierre
    steps:
      - intent: cancelar_cierre
      - action: action_cancelar_cierre
      - action: utter_cierre_cancelado
      - action: utter_volver_menu_principal
  
  - rule: Asignar usuario si no se especifica
    steps:
      - intent: mostrar_token
      - action: action_set_default_tipo_usuario
      - action: action_mostrar_token

  - rule: Usuario niega cierre
    steps:
      - intent: negar_cierre
      - action: action_ir_menu_principal  
  
  - rule: Usuario quiere cerrar solo el chat
    steps:
      - intent: cerrar_chat
      - action: utter_cerrar_chat_confirmacion

  - rule: Usuario quiere ver info del estado estudiante
    steps:
      - intent: ver_estado_estudiante_info
      - action: utter_ver_estado_estudiante_info

  - rule: Usuario pide ayuda con certificados
    steps:
      - intent: ayuda_certificados
      - action: utter_ayuda_certificados

  - rule: Usuario elige consultar certificados por identificación
    steps:
      - intent: consulta_por_identificacion
      - action: utter_consulta_por_identificacion_info

  - rule: Usuario elige consultar certificados por solicitud
    steps:
      - intent: consulta_por_solicitud
      - action: utter_consulta_por_solicitud_info

  - rule: Usuario elige consultar certificados por tipo
    steps:
      - intent: consulta_por_tipo
      - action: utter_consulta_por_tipo_info

  - rule: Usuario quiere listar tipos de certificados (solo info)
    steps:
      - intent: listar_certificados
      - action: utter_listar_certificados

  - rule: Usuario quiere ver info general de certificados
    steps:
      - intent: ver_certificados_info
      - action: utter_ver_certificados_info

  - rule: Usuario elige certificado de estudio
    steps:
      - intent: certificado_estudio
      - action: utter_certificado_estudio_info

  - rule: Usuario elige certificado de notas
    steps:
      - intent: certificado_notas
      - action: utter_certificado_notas_info

  - rule: Usuario elige certificado laboral
    steps:
      - intent: certificado_laboral
      - action: utter_certificado_laboral_info

  - rule: Usuario elige otro tipo de certificado
    steps:
      - intent: certificado_otro
      - action: utter_certificado_otro_info

  - rule: Usuario quiere descargar certificado
    steps:
      - intent: descargar_certificado
      - action: utter_descargar_certificado

  - rule: Mostrar guía de login (deep-links)
    steps:
      - intent: ver_login_hint
      - action: utter_login_hint

  - rule: Usuario quiere iniciar sesión en Zajuna
    steps:
      - intent: ingreso_zajuna
      - action: action_ingreso_zajuna

  - rule: Consultar certificados (flujo unificado)
    steps:
      - intent: consultar_certificados
      - action: action_consultar_certificados
      - action: action_incrementar_turnos_conversacion

  - rule: Ver estado estudiante (flujo unificado)
    steps:
      - intent: ver_estado_estudiante
      - action: action_ver_estado_estudiante
      - action: action_incrementar_turnos_conversacion 
  
  - rule: Sugerir contacto con tutor
    steps:
      - intent: sugerir_tutor
      - action: utter_ofrecer_contacto_tutor

  - rule: Abrir menú académico
    steps:
      - intent: menu_academico
      - action: utter_menu_academico
  
  - rule: Soporte - problemas de acceso
    steps:
      - intent: soporte_acceso
      - action: utter_soporte_acceso

  - rule: Soporte - errores en la plataforma
    steps:
      - intent: soporte_error_plataforma
      - action: utter_soporte_error_plataforma 

  - rule: Ver estado del estudiante
    steps:
      - intent: estado_estudiante
      - action: utter_estado_estudiante_resumen

  - rule: Ver contenido del curso
    steps:
      - intent: consultar_contenido_curso
      - action: utter_contenido_curso_resumen
  
  - rule: Abrir menú administrativo
    steps:
      - intent: menu_administrativo
      - action: utter_menu_administrativo

  - rule: Abrir menú soporte
    steps:
      - intent: menu_soporte
      - action: utter_menu_soporte

  - rule: Ver tutor asignado (flujo unificado)
    steps:
      - intent: ver_tutor_asignado
      - action: action_tutor_asignado

  - rule: Guardar estado por inactividad
    steps:
      - intent: notificar_inactividad
      - action: action_guardar_estado_seguridad

  - rule: manejar solicitud de certificado
    steps:
      - intent: solicitar_certificado
      - action: utter_info_certificado

  - rule: manejar intent sugerido por LLM para certificado
    condition:
      - slot_was_set:
          - llm_suggested_intent: "solicitar_certificado"
    steps:
      - action: utter_info_certificado

  - rule: Ir a menú académico desde consultar_academico
    steps:
      - intent: consultar_academico
      - action: utter_menu_academico
      - action: utter_pedir_tema
      - action: action_incrementar_turnos_conversacion

  - rule: Despedida del usuario (unificada v3.1)
    steps:
      - intent: despedida
      - action: action_resumen_sesion_llm
      - action: utter_despedida_final
      - action: action_finalizar_conversacion
 
  - rule: Manejar emoción detectada (unificada v3.1)
    steps:
      - intent: detectar_emocion
      - action: action_analizar_estado_usuario
  
  - rule: Ayuda detalle certificados (unificada v3.1)
    steps:
      - intent: ayuda_certificados_detalle
      - action: action_mostrar_certificados_carousel
      - action: utter_ayuda_certificados_detalle

  - rule: Iniciar soporte desde intent principal
    steps:
      - intent: solicitar_soporte
      - action: utter_preguntar_tipo_soporte
      - action: action_incrementar_turnos_conversacion
  
  - rule: Soporte como PQRS formal (unificada v3.1)
    steps:
      - intent: soporte_pqrs
      - action: utter_iniciar_soporte_desde_pedir_mensaje
      - action: utter_ask_email_contacto
      - action: soporte_form
      - active_loop: soporte_form

  - rule: Responder negación genérica
    steps:
      - intent: deny
      - action: utter_deny

  - rule: Historial académico → registrar y responder con LLM
    condition:
      - active_loop: null
    steps:
      - intent: informar_historial_academico
      - action: action_historial_academico
      - action: action_incrementar_turnos_conversacion
  
  - rule: Consultar horarios de clases (flujo unificado)
    condition:
      - active_loop: null
    steps:
      - intent: consultar_horarios_clases
      - action: action_consultar_horarios_clases
      - action: action_incrementar_turnos_conversacion

  - rule: Consultar progreso de curso (flujo unificado)
    condition:
      - active_loop: null
    steps:
      - intent: consultar_progreso_curso
      - action: action_consultar_progreso_curso
      - action: action_incrementar_turnos_conversacion
  
  - rule: Saludo inicial muestra menú principal
    steps:
      - intent: saludo
      - action: utter_menu_principal
      - action: action_incrementar_turnos_conversacion
  
  - rule: Usuario quiere continuar con otro tema
    steps:
      - intent: continuar_consulta
      - action: utter_continuar_tema_menu
 

  - rule: Usuario acepta derivación a humano
    steps:
      - intent: confirmacion_escalar_humano
      - action: action_derivar_y_registrar_humano
      - action: utter_handoff_iniciado
      - action: utter_derivando_humano

  - rule: Usuario rechaza derivación a humano
    steps:
      - intent: negar_escalar
      - action: action_handoff_cancelar
      - action: utter_derivacion_cancelada
  
  - rule: Derivar a humano directo 
    steps:
      - intent: pedir_humano_directo
      - action: action_derivar_y_registrar_humano
      - action: utter_handoff_iniciado
      - action: utter_derivando_humano
      - action: utter_ofrecer_continuar
  
  - rule: Usuario pide hablar con humano
    steps:
      - intent: pedir_humano
      - action: action_marcar_escalar_humano
      - action: utter_derivar_a_humano_opciones

  - rule: Usuario sigue con el bot en vez de humano
    steps:
      - intent: negar_handoff
      - action: utter_derivacion_cancelada

  - rule: Manejar error en flujo de soporte (unificada v3.1)
    steps:
      - intent: soporte_error
      - action: utter_soporte_error
      - action: action_handle_with_llm

  - rule: Fallback general → LLM con memoria
    condition:
      - active_loop: null
    steps:
      - intent: llm_fallback
      - action: action_memory_wrapper
      - action: action_handle_with_llm
      - action: action_incrementar_turnos_conversacion

  - rule: Manejar out_of_scope con LLM y mensaje estándar (unificada v3.1)
    steps:
      - intent: out_of_scope
      - action: utter_out_of_scope
      - action: action_handle_with_llm

  - rule: Fallback explícito del usuario (unificada v3.1)
    steps:
      - intent: fallback
      - action: utter_fallback
      - action: action_handle_with_llm

  - rule: Resumir clase con LLM
    steps:
      - intent: resumir_clase
      - action: utter_resumir_clase
      - action: action_memory_wrapper
      - action: action_handle_with_llm

  - rule: Usuario reporta otro problema técnico (mensaje + LLM v3.1)
    steps:
      - intent: otro_problema_tecnico
      - action: utter_otro_problema_tecnico
      - action: action_handle_with_llm

  - rule: Problema no resuelto -> LLM + ofrecer escalamiento
    steps:
      - intent: problema_no_resuelto
      - action: action_handle_with_llm
      - action: utter_problema_resuelto_no
      - action: utter_ofrecer_humano
  
  - rule: Explicar un tema académico con LLM
    steps:
      - intent: explicar_tema
      - action: action_explicar_tema_llm
      - action: utter_preguntar_explicacion_tema
      - action: action_incrementar_turnos_conversacion

  - rule: Continuar explicación del tema (affirm)
    condition:
      - slot_was_set:
          - from_llm: true
      - slot_was_set:
          - tema_actual: true
    steps:
      - intent: affirm
      - action: action_explicar_tema_llm

  - rule: Continuar explicación temática (continuar_tema_si)
    steps:
      - intent: continuar_tema_si
      - action: action_explicar_tema_llm

  - rule: Usuario cancela creación de soporte (deny)
    steps:
      - action: utter_pedir_confirmacion_soporte
      - intent: deny
      - action: utter_cancelar_soporte

  - rule: Atajo rápido → Enviar soporte
    steps:
      - intent: enviar_soporte
      - action: action_enviar_soporte
      - action: utter_soporte_creado
      - action: action_incrementar_turnos_conversacion

  - rule: Enviar soporte directo
    steps:
      - intent: enviar_soporte_directo
      - action: action_enviar_soporte_directo
      - action: action_incrementar_turnos_conversacion

  - rule: Submit soporte_form
    condition:
      - active_loop: soporte_form
    steps:
      - action: soporte_form
      - active_loop: null
      - action: action_soporte_submit

  - rule: Terminar conversación durante soporte_form
    condition:
      - active_loop: soporte_form
    steps:
      - intent: terminar_conversacion
      - action: action_deactivate_loop
      - active_loop: null
      - action: utter_cancelar_soporte

  - rule: Fallback dentro de soporte_form (solo mensaje libre)
    condition:
      - active_loop: soporte_form
    steps:
      - intent: llm_fallback
      - slot_was_set:
          - requested_slot: soporte_mensaje
      - action: action_registrar_intento_form
      - action: action_verificar_max_intentos_form
      - action: soporte_form
      - active_loop: soporte_form

  - rule: Fallback genérico durante soporte_form (cuando NO es soporte_mensaje)
    condition:
      - active_loop: soporte_form
    steps:
      - intent: llm_fallback
      - slot_was_set:
          - requested_slot: null
      - action: soporte_form
      - active_loop: soporte_form

  - rule: Soporte como mensaje interno (unificada v3.1)
    steps:
      - intent: soporte_interno
      - action: utter_iniciar_soporte_desde_pedir_mensaje

  - rule: Derivar a humano (desde oferta)
    steps:
      - action: utter_ofrecer_humano
      - intent: affirm
      - action: action_derivar_y_registrar_humano
      - action: utter_handoff_iniciado
      - action: utter_derivando_humano

  - rule: Problema resuelto (disparar encuesta rápida)
    steps:
      - intent: problema_resuelto_si
      - action: utter_agradecimiento_satisfaccion
      - action: utter_preguntar_satisfaccion

  - rule: Usuario satisfecho (encuesta general)
    steps:
      - intent: respuesta_satisfecho
      - action: action_set_encuesta_tipo
      - slot_was_set:
          - encuesta_tipo: "positiva"
      - action: utter_agradecimiento_satisfaccion
      - action: utter_resumen_sesion
      - action: utter_opciones_finales_aprendizaje

  - rule: Usuario insatisfecho (encuesta rápida/global)
    steps:
      - intent: respuesta_insatisfecho
      - action: action_set_encuesta_tipo
      - slot_was_set:
          - encuesta_tipo: "negativa"
      - action: utter_encuesta_insatisfaccion
      - action: utter_ofrecer_contacto_tutor

  - rule: Mini encuesta - explicación satisfactoria
    steps:
      - intent: encuesta_explicacion_si
      - action: utter_explicacion_ok
      - action: utter_opciones_finales_aprendizaje
  
  - rule: Mini encuesta - explicación no clara
    steps:
      - intent: encuesta_explicacion_no
      - action: utter_reconocer_dudas_tema
      - action: action_explicar_tema_llm
      - action: utter_preguntar_tutor_academico

  - rule: Ayuda con tema académico → pedir tema
    condition:
      - active_loop: null
    steps:
      - intent: solicitar_ayuda_tema
      - action: utter_confirmar_tema_academico

  - rule: Iniciar encuesta de satisfacción completa
    steps:
      - intent: iniciar_encuesta
      - action: utter_encuesta_satisfaccion
      - action: action_preguntar_resolucion
      - action: encuesta_satisfaccion_form
      - active_loop: encuesta_satisfaccion_form

  - rule: Preguntar nivel de satisfacción (form)
    condition:
      - active_loop: encuesta_satisfaccion_form
    steps:
      - action: utter_ask_nivel_satisfaccion

  - rule: Finalizar encuesta de satisfacción completa
    condition:
      - active_loop: null
    steps:
      - action: action_registrar_encuesta
      - action: utter_agradecimiento_satisfaccion
      - action: action_resumen_sesion_llm
      - action: utter_despedida_final
      - action: action_finalizar_conversacion

  - rule: Sugerencia tutor tras encuesta negativa
    condition:
      - slot_was_set:
          - encuesta_satisfaccion: "negativa"
    steps:
      - action: utter_ofrecer_contacto_tutor

  - rule: Reanudar encuesta si hay pendiente
    condition:
      - slot_was_set:
          - reanudar_pendiente: true
    steps:
      - intent: reanudar_auto_si
      - action: action_reanudar_auto
      - action: utter_reanudar_confirmado

  - rule: No reanudar encuesta
    steps:
      - intent: reanudar_auto_no
      - action: utter_reanudar_cancelado

  - rule: Confirmar cierre con autosave cuando hay encuesta incompleta
    condition:
      - active_loop: null
      - slot_was_set:
          - encuesta_incompleta: true
    steps:
      - intent: terminar_conversacion_segura_autosave
      - action: utter_confirmar_cierre_con_autosave

  - rule: Confirmar cierre seguro con autosave (unificada v3.1)
    steps:
      - intent: confirmar_cierre_autosave
      - action: action_guardar_encuesta_incompleta
      - action: action_confirmar_cierre_autosave
      - action: action_resumen_sesion_llm

  - rule: Flujo base - cierre seguro (unificada v3.1)
    steps:
      - intent: terminar_conversacion_segura
      - action: action_verificar_estado_encuesta

  - rule: Confirmar cierre seguro
    steps:
      - intent: confirmar_cierre_segura
      - action: action_guardar_progreso_encuesta
      - action: action_resumen_sesion_llm
      - action: action_confirmar_cierre_seguro
      - action: utter_cierre_confirmado_seguro
  
  - rule: Usuario no quiere responder encuesta general
    steps:
      - intent: no_encuesta_general
      - action: utter_despedida_final
      - action: action_finalizar_conversacion
  
  - rule: Cerrar encuesta general con agradecimiento
    steps:
      - intent: encuesta_nivel_general
      - action: utter_agradecimiento_encuesta_general
      - action: utter_despedida_profesional