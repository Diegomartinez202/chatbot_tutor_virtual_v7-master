version: "3.1"

stories:

- story: Soporte general con aclaración LLM
  steps:
    - intent: solicitar_soporte
    - action: utter_preguntar_tipo_soporte
    - action: action_incrementar_turnos_conversacion
    - intent: soporte_interno
    - action: utter_iniciar_soporte_desde_pedir_mensaje
    - intent: otro_problema_tecnico
    - action: utter_otro_problema_tecnico
    - action: action_handle_with_llm
    - intent: pedir_mensaje
    - action: utter_iniciar_soporte_desde_pedir_mensaje
    - action: soporte_form
    - active_loop: soporte_form

- story: Soporte pantalla en blanco → ticket
  steps:
    - intent: pantalla_blanca
    - action: utter_pantalla_blanca_ayuda
    - intent: pedir_mensaje
    - action: utter_iniciar_soporte_desde_pedir_mensaje
    - action: soporte_form
    - active_loop: soporte_form

- story: Aprender tema desde menú académico con seguimiento
  steps:
    - intent: menu_academico
    - action: utter_menu_academico
    - intent: aprender_tema
    - action: action_memory_wrapper
    - action: action_handle_with_llm
    - action: action_incrementar_turnos_conversacion
    - intent: continue
    - action: utter_continuar_tema_menu
    - intent: continuar_consulta
    - action: utter_continuar_tema_menu

- story: Aprender tema directo con cierre elegante
  steps:
    - intent: aprender_tema
    - action: action_memory_wrapper
    - action: action_handle_with_llm
    - action: action_incrementar_turnos_conversacion
    - intent: continuar_tema_no
    - action: utter_no_continuar_tema
    - action: utter_menu_principal

- story: Ver contenido de curso y profundizar
  steps:
    - intent: consultar_contenido_curso
    - action: utter_contenido_curso_resumen
    - intent: aprender_tema
    - action: action_memory_wrapper
    - action: action_handle_with_llm
    - action: action_incrementar_turnos_conversacion

- story: Emoción negativa → apoyo académico y contacto por correo
  steps:
    - intent: detectar_emocion
    - action: action_analizar_estado_usuario
    - intent: sugerir_tutor
    - action: utter_ofrecer_contacto_tutor
    - intent: contactar_tutor
    - action: utter_contactar_tutor_opciones

- story: Feedback directo con registro
  steps:
    - intent: dar_retroalimentacion
    - action: utter_iniciar_retroalimentacion
    - action: feedback_form
    - active_loop: feedback_form
    - action: feedback_form
    - active_loop: null
    - action: action_guardar_feedback
    - action: utter_gracias_retroalimentacion

- story: Fallback en tutor académico
  steps:
    - intent: aprender_tema
    - action: action_memory_wrapper
    - action: action_handle_with_llm
    - action: action_incrementar_turnos_conversacion
    - intent: nlu_fallback
    - action: action_handle_with_llm
    - intent: menu_academico
    - action: utter_menu_academico

- story: Usuario pausa y luego reanuda con Guardian
  steps:
    - intent: guardian_guardar_progreso
    - action: action_guardian_guardar_progreso
    - intent: guardian_pausar_conversacion
    - action: action_guardian_pausar
    - intent: guardian_reanudar_conversacion
    - action: action_guardian_reanudar
