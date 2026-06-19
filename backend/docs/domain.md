version: '3.1'

session_config:
  session_expiration_time: 60
  carry_over_slots_to_new_session: false

intents:
- consultar_academico
- consultar_certificados
- ver_certificados_info
- ver_estado_estudiante
- ver_estado_estudiante_info
- horarios_calendario
- proceso_academico
- proceso_academico_secundario
- ir_menu_principal
- confirmar_autenticacion
- negar_autenticacion
- auth_login_cmd
- ver_login_hint
- affirm
- deny
- nlu_fallback
- reiniciar_conversacion
- limpiar_sesion
- mostrar_token
- ping_servidor
- solicitar_soporte
- iniciar_encuesta
- enviar_credenciales
- recuperar_contrasena
- provide_email
- fallback
- terminar_conversacion
- cancelar_cierre
- despedida
- confirmacion_escalar_humano
- negar_escalar
- saludo
- reanudar_auto_si
- reanudar_auto_no
- terminar_conversacion_segura
- reanudar_conversacion
- limpiar_autosave
- problema_resuelto_si
- respuesta_satisfecho
- respuesta_insatisfecho
- dar_retroalimentacion
- contactar_tutor
- continuar_tema_si
- continue
- enviar_soporte
- explorar_temas
- cambiar_idioma_espanol
- cambiar_idioma_ingles
- guardar_snapshot
- ayuda_guardian
- confirmar_derivacion
- iniciar_sesion
- cerrar_chat
- terminar_conversacion_segura_autosave
- confirmar_cierre_segura
- guardian_pausar_conversacion
- guardian_reanudar_conversacion
- guardian_guardar_progreso
- notificar_desconexion
- notificar_inactividad
- notificar_reconexion
- recuperar_estado_seguridad
- soporte_tecnico
- problema_no_ingreso
- pantalla_blanca
- error_actividad
- otro_problema_tecnico
- enviar_correo_tutor
- ver_link_soporte
- ver_soporte_creado_info
- cancelar
- negar_cierre
- confirmar_cierre_autosave
- cancelar_cierre_autosave
- certificado_estudio
- certificado_notas
- certificado_laboral
- certificado_otro
- listar_certificados
- descargar_certificado
- ayuda_certificados
- consulta_por_identificacion
- consulta_por_solicitud
- consulta_por_tipo
- pedir_mensaje
- enviar_soporte_directo
- necesita_auth
- continuar_tema_no
- enviar_correo
- enviar_url
- cancelar_cierre_segura
- ingreso_zajuna
- ver_tutor_asignado
- detectar_emocion
- guardar_estado
- pedir_humano
- problema_no_resuelto
- pedir_humano_directo
- menu_rapido
- sugerir_tutor
- menu_soporte
- menu_administrativo
- menu_academico
- estado_estudiante
- soporte_acceso
- soporte_error_plataforma
- consultar_contenido_curso
- soporte_pqrs
- soporte_interno
- aprender_tema
- solicitar_certificado
- ayuda_certificados_detalle
- out_of_scope
- resumir_clase
- informar_historial_academico
- llm_fallback
- explicar_tema
- consultar_progreso_curso
- solicitar_ayuda_tema
- consultar_horarios_clases
- soporte_error
- pedir_nombre
- encuesta_explicacion_si
- encuesta_explicacion_no
- continuar_consulta
- negar_handoff
- no_encuesta_general
- encuesta_nivel_general
- mis_cursos
- encuesta_valor_explicacion_si
- reanudar_mas_tarde
- necesita_humano
- soporte_general
- consultar_calificaciones
- preguntas_frecuentes
- pqrs
- certificados_generales
- encuesta_valor_explicacion_no
- encuesta_rever_tema_si
- encuesta_rever_tema_no
- escalar_humano

entities:
- curso
- certificado
- tutor
- encuesta_tipo
- nombre
- tipo_estado
- email
- password
- prefer_contacto
- motivo_soporte
- phone
- autosave_estado
- satisfaccion
- comentario
- feedback_texto
- nivel_satisfaccion
- usuario
- soporte_mensaje
- token
- menu_seleccion
- nombre_usuario
- mensaje
- problema
- url_problema
- tipo_usuario
- emocion
- tema
- cedula

slots:
  is_authenticated:
    type: bool
    influence_conversation: true
    initial_value: false
    mappings:
    - type: custom
  llm_suggested_intent:
    type: text
    influence_conversation: false
    mappings:
    - type: custom
  from_llm:
    type: bool
    influence_conversation: false
    initial_value: false
    mappings:
    - type: custom
  topic:
    type: text
    influence_conversation: true
    mappings:
    - type: custom
  tema_actual:
    type: text
    influence_conversation: true
    mappings:
    - type: from_entity
      entity: tema
    - type: from_text
      intent: aprender_tema
  memoria_semantica:
    type: text
    influence_conversation: false
    mappings:
    - type: custom
  emocion_detectada:
    type: text
    influence_conversation: true
    mappings:
    - type: from_entity
      entity: emocion
    - type: from_text
      intent: detectar_emocion
  proceso_activo:
    type: bool
    influence_conversation: true
    initial_value: false
    mappings:
    - type: custom
  curso:
    type: text
    influence_conversation: true
    mappings:
    - type: from_entity
      entity: curso
    - type: from_text
  certificado:
    type: text
    influence_conversation: true
    mappings:
    - type: from_entity
      entity: certificado
    - type: from_text
  tutor:
    type: text
    influence_conversation: true
    mappings:
    - type: from_entity
      entity: tutor
    - type: from_text
  user_token:
    type: text
    influence_conversation: false
    mappings:
    - type: custom
  password:
    type: text
    influence_conversation: false
    mappings:
    - type: from_text
      conditions:
      - active_loop: auth_login_form
        requested_slot: password
  motivo_soporte:
    type: categorical
    values:
    - acceso
    - calificaciones
    - certificados
    - tecnico
    - otro
    influence_conversation: true
    mappings:
    - type: from_entity
      entity: motivo_soporte
    - type: from_intent
      intent: solicitar_soporte
      value: otro
    - type: from_text
      conditions:
      - active_loop: soporte_form
        requested_slot: motivo_soporte
  prefer_contacto:
    type: categorical
    values:
    - email
    - whatsapp
    - ninguno
    influence_conversation: false
    mappings:
    - type: from_entity
      entity: prefer_contacto
    - type: from_text
      conditions:
      - active_loop: soporte_form
        requested_slot: prefer_contacto
  tema_academico:
    type: text
    influence_conversation: false
    mappings:
    - type: from_text
      conditions:
      - active_loop: null
  phone:
    type: text
    influence_conversation: false
    mappings:
    - type: from_entity
      entity: phone
    - type: from_text
      conditions:
      - active_loop: soporte_form
        requested_slot: phone
  derivacion_humano:
    type: bool
    influence_conversation: false
    initial_value: false
    mappings:
    - type: custom
  reanudar_pendiente:
    type: bool
    initial_value: false
    influence_conversation: true
    mappings:
    - type: custom
  satisfaccion:
    type: text
    influence_conversation: true
    initial_value: null
    mappings:
    - type: from_entity
      entity: satisfaccion
    - type: from_text
  feedback_texto:
    type: text
    influence_conversation: true
    mappings:
    - type: from_text
      conditions:
      - active_loop: feedback_form
        requested_slot: feedback_texto
  encuesta_tipo:
    type: categorical
    values:
    - positiva
    - negativa
    - neutra
    influence_conversation: true
    mappings:
    - type: from_intent
      intent: respuesta_satisfecho
      value: positiva
    - type: from_intent
      intent: respuesta_insatisfecho
      value: negativa
    - type: from_entity
      entity: encuesta_tipo
    - type: from_text
      conditions:
      - active_loop: encuesta_satisfaccion_form
        requested_slot: encuesta_tipo
  usuario:
    type: text
    influence_conversation: false
    mappings:
    - type: from_entity
      entity: usuario
    - type: from_text
      conditions:
      - active_loop: feedback_form
        requested_slot: usuario
  comentario:
    type: text
    influence_conversation: false
    mappings:
    - type: from_text
      conditions:
      - active_loop: encuesta_satisfaccion_form
        requested_slot: comentario
  soporte_mensaje:
    type: text
    influence_conversation: false
    mappings:
    - type: from_entity
      entity: soporte_mensaje
    - type: from_text
      conditions:
      - active_loop: soporte_form
        requested_slot: soporte_mensaje
  auth_token:
    type: text
    influence_conversation: false
    initial_value: null
    mappings:
    - type: custom
  soporte_intentos:
    type: float
    influence_conversation: false
    initial_value: 0
    mappings:
    - type: custom
  menu_actual:
    type: text
    influence_conversation: true
    initial_value: principal
    mappings:
    - type: custom
  zajuna_base_url:
    type: text
    influence_conversation: false
    initial_value: https://zajuna.edu
    mappings:
    - type: custom
  encuesta_activa:
    type: bool
    influence_conversation: true
    initial_value: false
    mappings:
    - type: custom
  autosave_estado:
    type: text
    influence_conversation: false
    mappings:
    - type: custom
  evento_seguridad:
    type: text
    influence_conversation: true
    mappings:
    - type: custom
  nombre:
    type: text
    influence_conversation: false
    mappings:
    - type: from_entity
      entity: nombre
    - type: from_text
      conditions:
      - active_loop: soporte_form
        requested_slot: nombre
  email:
    type: text
    influence_conversation: false
    mappings:
    - type: from_entity
      entity: email
    - type: from_text
      conditions:
      - active_loop: soporte_form
        requested_slot: email
      - active_loop: auth_login_form
        requested_slot: email
      - active_loop: password_recovery_form
        requested_slot: email
  mensaje:
    type: text
    influence_conversation: false
    mappings:
    - type: from_text
      conditions:
      - active_loop: feedback_form
        requested_slot: mensaje
  session_activa:
    type: bool
    influence_conversation: true
    initial_value: true
    mappings:
    - type: custom
  confirmacion_cierre:
    type: text
    influence_conversation: true
    initial_value: null
    mappings:
    - type: custom
  encuesta_incompleta:
    type: bool
    influence_conversation: true
    initial_value: false
    mappings:
    - type: custom
  problema:
    type: text
    influence_conversation: true
    mappings:
    - type: from_entity
      entity: problema
    - type: from_text
  url_problema:
    type: text
    influence_conversation: false
    mappings:
    - type: from_entity
      entity: url_problema
  slot_tipo_usuario:
    type: categorical
    values:
    - usuario
    - admin
    influence_conversation: true
    mappings:
    - type: from_entity
      entity: tipo_usuario
  tema_previsto:
    type: text
    influence_conversation: false
    mappings:
    - type: from_text
      intent: aprender_tema
    - type: custom
  nivel_satisfaccion:
    type: text
    influence_conversation: true
    mappings:
    - type: from_entity
      entity: nivel_satisfaccion
    - type: from_text
      conditions:
      - active_loop: encuesta_satisfaccion_form
        requested_slot: nivel_satisfaccion
  encuesta_satisfaccion:
    type: text
    influence_conversation: false
    mappings:
    - type: custom
  escalar_humano:
    type: bool
    initial_value: false
    influence_conversation: true
    mappings:
    - type: custom
  tipo_soporte:
    type: categorical
    values:
    - pqrs
    - interno
    influence_conversation: true
    mappings:
    - type: from_intent
      value: pqrs
      intent: soporte_pqrs
    - type: from_intent
      value: interno
      intent: soporte_interno
  correo:
    type: text
    influence_conversation: false
    mappings:
    - type: from_entity
      entity: email
  historial_academico:
    type: text
    influence_conversation: false
    mappings:
    - type: from_text
      intent: informar_historial_academico
    - type: custom
  turnos_conversacion:
    type: float
    influence_conversation: false
    initial_value: 0
    mappings:
    - type: custom
  sesion_larga:
    type: bool
    influence_conversation: false
    initial_value: false
    mappings:
    - type: custom
  soporte_form_fallback_count:
    type: float
    initial_value: 0
    influence_conversation: false
    mappings:
    - type: custom
  cedula:
    type: text
    influence_conversation: false
    mappings:
    - type: from_text
      conditions:
      - active_loop: soporte_form
        requested_slot: cedula
    - type: from_entity
      entity: cedula

forms:
  auth_login_form:
    required_slots:
    - email
    - password

  password_recovery_form:
    required_slots:
    - email

  feedback_form:
    required_slots:
    - feedback_texto
    - usuario
    - mensaje

  encuesta_satisfaccion_form:
    required_slots:
    - nivel_satisfaccion
    - comentario
    - encuesta_tipo

  soporte_form:
    required_slots:
    - nombre
    - email
    - motivo_soporte
    - prefer_contacto
    - phone
    - soporte_mensaje

responses:
  utter_preguntar_continuar_menu:
  - text: ¿Deseas realizar otra consulta?
    buttons:
    - title: Sí, volver al menú principal
      payload: /ir_menu_principal
    - title: No, terminar conversación
      payload: /terminar_conversacion
  utter_reinicio_confirmado:
  - text: 🧹 La sesión ha sido reiniciada correctamente.
  utter_ping_ok:
  - text: ✅ El servidor está activo y respondiendo correctamente.

  utter_auth_fail:
  - text: ⚠️ No pude iniciar sesión con esos datos. ¿Intentamos de nuevo o recuperamos tu contraseña?
    buttons:
    - title: 🔁 Reintentar
      payload: /enviar_credenciales
    - title: 🧷 Recuperar contraseña
      payload: /recuperar_contrasena
    - title: 👤 Hablar con humano
      payload: /necesita_humano

  utter_ask_password:
  - text: 🔑 Escribe tu contraseña.

  utter_recuperacion_enviada:
  - text: 📧 Te envié un correo con instrucciones para restablecer tu contraseña. Revisa la bandeja de entrada y spam.
    buttons:
    - title: 🔐 Volver a iniciar sesión
      payload: /auth_login_cmd
    - title: 🏠 Menú principal
      payload: /ir_menu_principal

  utter_cierre_confirmado:
  - text: ✅ Conversación finalizada. ¡Gracias por usar el asistente Zajuna! 🌟
    buttons:
    - title: 🔁 Volver al menú
      payload: /ir_menu_principal

  utter_derivando_humano:
  - text: Te conecto con un asesor humano. ⏳ Por favor, espera un momento.

  utter_reanudar_confirmado:
  - text: Perfecto, retomamos tu encuesta donde la dejaste. 🔄

  utter_reanudar_cancelado:
  - text: |
      Perfecto, dejaré tu sesión cerrada por ahora ✅.
      Cuando vuelvas, podrás iniciar una nueva consulta o retomar tus temas desde el menú principal.

  utter_cierre_cancelado_seguro:
  - text: Entendido, seguimos donde estabas. 😊

  utter_agradecimiento_satisfaccion:
  - text: |
      🙏 Muchas gracias por su valoracion🌟

  utter_esta_resuelto:
  - text: ¿Pudimos resolver tu problema? (Sí / No)

  utter_encuesta_satisfaccion:
  - text: >
      ¿Cómo calificarías la atención recibida hoy? 😊
      Opciones: satisfecho / neutral / insatisfecho

  utter_ask_nivel_satisfaccion:
  - text: ⭐ Del 1 al 5, ¿qué tan satisfecho estás? (1 = muy poco, 5 = muy satisfecho)

  utter_soporte_creado:
  - text: 🎫 Tu solicitud de soporte fue registrada correctamente. Un asesor te contactará en breve.

  utter_soporte_error:
  - text: >
      Parece que hubo un problema al procesar tu solicitud de soporte.
      ¿Quieres que lo intentemos de nuevo o prefieres que te derive a un agente humano?

  utter_deny:
  - text: Entendido. Si necesitas algo más, me dices. 🙂

  utter_cambiar_idioma_espanol:
  - text: Idioma configurado a **Español**. ¿Cómo te ayudo ahora?

  utter_cambiar_idioma_ingles:
  - text: Language switched to **English**. How can I help you now?

  utter_catalogo_cursos:
  - text: Estos son los cursos disponibles (demo). Si buscas algo específico, dime el área. 📚

  utter_guardian_help:
  - text: >
      🛡️ Este es un comando técnico para guardar un snapshot de tu sesión.
      Normalmente se usa para pruebas o diagnóstico del bot.

  utter_guardian_snapshot_ok:
  - text: ✅ He solicitado guardar un snapshot de tu sesión actual (modo técnico).

  utter_ask_email_contacto:
  - text: ¿Cuál es tu correo de contacto?

  utter_intento_form_fallido:
  - text: No logré entender del todo. ¿Podrías intentarlo de otra forma?
    buttons:
    - title: Intentar de nuevo
      payload: /necesita_humano
    - title: 💾 Terminar y guardar progreso
      payload: /terminar_conversacion_segura_autosave
  - channel: socketio
    text: ¿Quieres que te conecte con un asesor humano ahora?
    buttons:
    - title: Conectar ahora
      payload: /confirmacion_escalar_humano
    - title: Seguir aquí
      payload: /negar_escalar
    - title: Terminar guardando progreso
      payload: /terminar_conversacion_segura_autosave
  - channel: facebook
    custom:
      text: ¿Deseas hablar con un asesor humano?
      quick_replies:
      - content_type: text
        title: Sí, conectar
        payload: /confirmacion_escalar_humano
      - content_type: text
        title: No, gracias
        payload: /negar_escalar
      - content_type: text
        title: Terminar guardando progreso
        payload: /terminar_conversacion_segura_autosave

  utter_handoff_iniciado:
  - text: 🧑‍💼 Derivando tu caso a un asesor… Mantén abierto este chat. Te avisaré en cuanto esté listo.
  - channel: socketio
    text: Conectándote con un asesor… ⏳ Por favor, mantén esta ventana abierta.
  - channel: facebook
    custom:
      text: Derivando a humano… Te avisaremos aquí cuando el asesor esté listo. ⏳

  utter_cierre_cancelado:
  - text: 👌 Perfecto, seguimos aquí. ¿En qué más puedo ayudarte?
    buttons:
    - title: 🏠 Menú principal
      payload: /ir_menu_principal
    - title: 📄 Ver certificados
      payload: /consultar_certificados
    - title: 📊 Estado académico
      payload: /ver_estado_estudiante

  utter_form_fallback_warn:
  - text: >
      No logré entenderte del todo.
      ¿Puedes intentar con otras palabras? (Intento {soporte_intentos}/3)

  utter_pedir_autenticacion:
  - text: >
      🔐 Para ver esta información necesitas iniciar sesión primero.
      Por favor inicia sesión en la plataforma Zajuna y luego vuelve a preguntarme.
    buttons:
    - title: Ver cómo iniciar sesión
      payload: /ver_login_hint
    - title: Ir al inicio
      payload: /ir_menu_principal

  utter_confirmacion_consulta:
  - text: ✅ He enviado tus certificados al correo registrado.

  utter_login_hint:
  - text: >
      🔐 **Cómo iniciar sesión en Zajuna**
      1) Abre el portal: {zajuna_base_url}/login
      2) Ingresa tu usuario/correo y contraseña.
      3) Si olvidaste la clave, usa **“¿Olvidé mi contraseña?”**.
      Cuando hayas iniciado sesión, vuelve y escribe:
      👉 "consultar certificados" o "ver mi estado académico".
      Atajos:
      • Inicio de sesión: {zajuna_base_url}/login
      • Registro: {zajuna_base_url}/register
      • Recuperar contraseña: {zajuna_base_url}/password/reset
    buttons:
    - title: 🔑 Ir a Iniciar sesión
      payload: /auth_login_cmd
    - title: 🆘 Recuperar contraseña
      payload: /recuperar_contrasena
    - title: 🏠 Menú
      payload: /saludo

  utter_recuperar_acceso_cta:
  - text: >
      🆘 **Recuperación de acceso**
      1) Ve a: {zajuna_base_url}/password/reset
      2) Ingresa tu correo registrado y confirma.
      3) Revisa tu bandeja de entrada (y spam).
      4) Sigue el enlace para crear una nueva contraseña.
      ¿Listo para continuar luego?
    buttons:
    - title: ✅ Ya recuperé mi acceso
      payload: /auth_login_cmd
    - title: 🏠 Menú
      payload: /saludo
  - channel: socketio
    text: '👇 Opciones rápidas:'
    buttons:
    - title: 🎓 Estado
      payload: /ver_estado_estudiante
    - title: 📜 Certificados
      payload: /consultar_certificados
    - title: 🔐 Login
      payload: /auth_login_cmd
    - title: ❌ Terminar
      payload: /terminar_conversacion
  - channel: facebook
    custom:
      text: 'Selecciona una opción:'
      quick_replies:
      - content_type: text
        title: 🎓 Estado
        payload: /ver_estado_estudiante
      - content_type: text
        title: 📜 Certificados
        payload: /consultar_certificados
      - content_type: text
        title: 🔐 Login
        payload: /auth_login_cmd
      - content_type: text
        title: ❌ Terminar
        payload: /terminar_conversacion

  utter_cierre_confirmado_seguro:
  - text: >
      ✅ Conversación finalizada de forma segura y se guardará tu progreso actual,
      ¡Gracias por usar el asistente Zajuna! 🌟

  utter_guardando_progreso:
  - text: 💾 Guardando tu progreso antes de cerrar la conversación…

  utter_notificar_desconexion:
  - text: ⚠️ Se detectó una desconexión. Guardando tu progreso...

  utter_notificar_reconexion:
  - text: 🔄 Bienvenido de nuevo, restaurando tu sesión previa...

  utter_ask_mensaje:
  - text: Cuéntame brevemente tu problema o solicitud.

  utter_correo_enviado:
  - text: 📬 Envié un mensaje a tu tutor. Te responderá al correo registrado.

  utter_fallback:
  - text: 🤔 No entendí bien lo que dijiste. ¿Qué deseas hacer ahora?
    buttons:
    - title: 🏠 Volver al menú principal
      payload: /ir_menu_principal
    - title: 🆘 Hablar con soporte
      payload: /solicitar_soporte
    - title: ❌ Salir del chat
      payload: /terminar_conversacion

  utter_iniciar_soporte_desde_pedir_mensaje:
  - text: >
      Perfecto, te ayudo a enviar un mensaje a soporte.
      Te haré unas preguntas rápidas para entender mejor tu caso.

  utter_necesita_autenticacion:
  - text: >
      Para continuar con este proceso necesito que estés autenticado en la plataforma.
      ¿Qué te gustaría hacer?
    buttons:
    - title: Iniciar sesión ahora
      payload: /auth_login_cmd
    - title: Ver cómo iniciar sesión
      payload: /ver_login_hint
    - title: Volver al menú principal
      payload: /ir_menu_principal
    - title: Cancelar y cerrar chat
      payload: /terminar_conversacion
  - text: >
      Esta opción requiere que tengas la sesión iniciada.
      Elige una de las siguientes alternativas:
    buttons:
    - title: Abrir login
      payload: /auth_login_cmd
    - title: Necesito ayuda con el login
      payload: /ver_login_hint
    - title: Ir al menú principal
      payload: /ir_menu_principal
    - title: No, mejor terminemos
      payload: /terminar_conversacion

  utter_no_continuar_tema:
  - text: >
      Perfecto, dejamos este tema aquí 📝.
      No te preocupes, tu progreso en la conversación se mantiene.
      Si quieres, puedo ayudarte con otro contenido o mostrarte el menú principal.

  utter_problema_resuelto_no:
  - text: >
      Lamento que el problema aún no esté resuelto.
      Puedo derivarte con un agente humano o seguir intentando resolverlo aquí en el chat. ¿Qué prefieres?
    buttons:
    - title: Hablar con un humano
      payload: /escalar_humano
    - title: Seguir con el bot
      payload: /negar_escalar

  utter_continuar_con_bot:
  - text: >
      De acuerdo, seguimos intentando aquí en el chat.
      Cuéntame con más detalle qué está pasando o qué no quedó claro.

  utter_ask_nombre:
  - text: ¿Cuál es tu nombre completo?

  utter_ask_email:
  - text: ¿Cuál es tu correo electrónico de contacto?

  utter_ask_phone:
  - text: Si quieres, déjame un número de contacto (celular o teléfono).

  utter_ayuda_certificados:
  - text: >
      Puedo ayudarte con tus certificados: ver cuáles tienes disponibles,
      explicarte los tipos de certificados y guiarte para descargarlos.
      ¿Qué te gustaría hacer?
    buttons:
    - title: Ver mis certificados
      payload: /consultar_certificados
    - title: Saber qué tipos hay
      payload: /ayuda_certificados_detalle
    - title: Volver al menú principal
      payload: /ir_menu_principal

  utter_cancelar_accion:
  - text: >
      De acuerdo, cancelo la acción que estábamos realizando.
      ¿Quieres hacer algo más o volver al menú principal?
    buttons:
    - title: Volver al menú principal
      payload: /ir_menu_principal
    - title: Terminar conversación
      payload: /terminar_conversacion

  utter_cerrar_chat_confirmacion:
  - text: ¿Seguro que quieres cerrar el chat?
    buttons:
    - title: Sí, cerrar chat
      payload: /terminar_conversacion
    - title: No, seguir conversando
      payload: /negar_cierre
    - title: Comunicar con soporte
      payload: /solicitar_soporte

  utter_certificado_estudio_info:
  - text: >
      El certificado de estudio acredita que estás (or estuviste) matriculado
      en un programa académico. Normalmente incluye tus datos personales, el programa
      y el periodo. ¿Quieres que revise si tienes certificados de estudio disponibles?
    buttons:
    - title: Ver certificados de estudio
      payload: /consultar_certificados
    - title: Volver al menú
      payload: /ir_menu_principal

  utter_certificado_notas_info:
  - text: >
      El certificado de notas muestra tus calificaciones obtenidas en las asignaturas
      o módulos. Suele usarse para trámites académicos o con otras instituciones.
      ¿Deseas que te muestre las opciones para descargar tus notas?
    buttons:
    - title: Ver certificados de notas
      payload: /consultar_certificados
    - title: Volver al menú
      payload: /ir_menu_principal

  utter_certificado_laboral_info:
  - text: >
      El certificado laboral acredita tu vinculación con la institución o empresa
      (cargo, tiempo de servicio, tipo de contrato, etc.). ¿Quieres que te indique
      cómo solicitar o descargar tu certificado laboral?
    buttons:
    - title: Ver certificados laborales
      payload: /consultar_certificados
    - title: Volver al menú
      payload: /ir_menu_principal

  utter_certificado_otro_info:
  - text: >
      Entiendo, se trata de otro tipo de certificado (por ejemplo, asistencia,
      participación o algún formato especial). Puedo orientarte para ver si está disponible
      o cómo solicitarlo. Cuéntame brevemente qué tipo de certificado necesitas.
    buttons:
    - title: Ver mis certificados
      payload: /consultar_certificados
    - title: Volver al menú
      payload: /ir_menu_principal

  utter_confirmar_derivacion:
  - text: >
      Perfecto, confirmo la derivación de tu caso a un agente humano.
      En breve alguien continuará atendiéndote.
  - text: >
      Listo, he derivado tu caso a soporte humano.
      Por favor espera un momento mientras se conecta un asesor.

  utter_consulta_por_identificacion_info:
  - text: >
      Perfecto, vamos a consultar tus certificados por identificación.
      Por favor ingresa tu número de documento (cédula) tal como aparece en la plataforma.
    buttons:
    - title: No recuerdo mi documento
      payload: /ayuda_certificados
    - title: Volver al menú principal
      payload: /ir_menu_principal

  utter_consulta_por_solicitud_info:
  - text: >
      Vamos a consultar por número de solicitud o radicado.
      Escribe el código de solicitud que te enviamos cuando iniciaste el trámite.
    buttons:
    - title: No tengo el número de solicitud
      payload: /ayuda_certificados
    - title: Volver al menú principal
      payload: /ir_menu_principal

  utter_consulta_por_tipo_info:
  - text: >
      De acuerdo, consultemos por tipo de certificado.
      Dime qué tipo de certificado necesitas: estudio, notas, laboral u otro.
    buttons:
    - title: Certificado de estudio
      payload: /certificado_estudio
    - title: Certificado de notas
      payload: /certificado_notas
    - title: Certificado laboral
      payload: /certificado_laboral
    - title: Otro tipo
      payload: /certificado_otro

  utter_iniciar_retroalimentacion:
  - text: >
      Me encantaría conocer tu opinión para mejorar.
      Te haré un par de preguntas rápidas sobre tu experiencia con el asistente.
    buttons:
    - title: Dar feedback ahora
      payload: /iniciar_encuesta
    - title: Más tarde
      payload: /continuar_consulta

  utter_ask_feedback_texto:
  - text: >
      Cuéntame brevemente cómo fue tu experiencia con el asistente.
      ¿Qué te gustó y qué podríamos mejorar?

  utter_ask_usuario:
  - text: >
      Si quieres, dime tu nombre o algún identificador para asociar tu comentario
      (puedes omitirlo si prefieres mantenerte anónimo).

  utter_descargar_certificado:
  - text: >
      Claro, puedo ayudarte a descargar tu certificado.
      ¿Qué deseas hacer exactamente?
    buttons:
    - title: Ver mis certificados disponibles
      payload: /consultar_certificados
    - title: Descargar certificado específico
      payload: /consulta_por_tipo
    - title: Volver al menú principal
      payload: /ir_menu_principal

  utter_error_actividad_ayuda:
  - text: >
      Veo que tienes un error al abrir una actividad o contenido.
      ¿Puedes decirme si el problema es con una actividad específica, un cuestionario o todo el curso?
    buttons:
    - title: Solo una actividad
      payload: /error_actividad
    - title: Todo el curso
      payload: /pantalla_blanca
    - title: Otro problema
      payload: /otro_problema_tecnico

  utter_horarios_calendario_info:
  - text: >
      Puedo mostrarte información sobre tus horarios y el calendario académico.
      Ten en cuenta que para ver detalles exactos normalmente debes entrar a la plataforma.
    buttons:
    - title: Ver calendario académico
      payload: /consultar_academico
    - title: Volver al menú principal
      payload: /ir_menu_principal

  utter_redirigir_login:
  - text: >
      Veo que quieres iniciar sesión.
      Te llevo al flujo de autenticación.
    buttons:
    - title: Iniciar sesión
      payload: /auth_login_cmd
    - title: Ver ayuda para el login
      payload: /ver_login_hint

  utter_listar_certificados:
  - text: >
      Puedo listar los certificados que tienes disponibles en la plataforma.
      Si ya estás autenticado en el portal, revisa la sección de certificados
      o historial académico.
    buttons:
    - title: Quiero ver certificados
      payload: /consultar_certificados
    - title: Ayuda con certificados
      payload: /ayuda_certificados
    - title: Volver al menú principal
      payload: /ir_menu_principal

  utter_negar_autenticacion:
  - text: >
      Entiendo, por ahora no iniciarás sesión.
      Algunas funciones estarán limitadas, pero puedo ayudarte con información general.
    buttons:
    - title: Ver menú principal
      payload: /ir_menu_principal
    - title: Terminar conversación
      payload: /terminar_conversacion

  utter_otro_problema_tecnico:
  - text: >
      Entiendo, es otro tipo de problema técnico.
      Por favor descríbeme brevemente qué está ocurriendo y con qué parte de la plataforma.

  utter_pantalla_blanca_ayuda:
  - text: >
      Si ves una pantalla en blanco, suele estar relacionado con el navegador
      o la conexión. Prueba actualizar la página, borrar caché o cambiar de navegador.
      Si el problema continúa, puedo ayudarte a reportarlo a soporte.
    buttons:
    - title: Reportar a soporte
      payload: /pedir_mensaje
    - title: Volver al menú principal
      payload: /ir_menu_principal

  utter_problema_no_ingreso:
  - text: >
      Veo que no puedes ingresar a la plataforma.
      Verifica tu usuario y contraseña, y si el problema continúa puedo orientarte o derivarte a soporte.
    buttons:
    - title: Olvidé mi contraseña
      payload: /recuperar_contrasena
    - title: Necesito soporte técnico
      payload: /solicitar_soporte
    - title: Ver guía de inicio de sesión
      payload: /ver_login_hint

  utter_proceso_academico_menu:
  - text: >
      Vamos a ver tu proceso académico. ¿Qué aspecto te interesa revisar?
    buttons:
    - title: Estado como estudiante
      payload: /ver_estado_estudiante
    - title: Certificados
      payload: /consultar_certificados
    - title: Horarios / calendario
      payload: /horarios_calendario
    - title: Volver al menú principal
      payload: /ir_menu_principal

  utter_proceso_academico_secundario_menu:
  - text: >
      Este es el submenú de procesos académicos. Elige qué quieres gestionar:
    buttons:
    - title: Ver mi estado
      payload: /ver_estado_estudiante
    - title: Ver certificados
      payload: /consultar_certificados
    - title: Ver horarios/calendario
      payload: /horarios_calendario

  utter_confirmar_email:
  - text: >
      Gracias, he registrado tu correo electrónico.
      Lo usaré solo para ayudarte con esta consulta o soporte.

  utter_ver_certificados_info:
  - text: >
      Aquí puedes ver información de ejemplo sobre certificados, incluso sin
      iniciar sesión. Esto incluye formatos, tipos y ejemplos de certificados
      disponibles.
    buttons:
    - title: Ver mis certificados reales
      payload: /consultar_certificados
    - title: Ayuda con certificados
      payload: /ayuda_certificados
    - title: Volver al menú principal
      payload: /ir_menu_principal

  utter_ver_estado_estudiante_info:
  - text: >
      Aquí puedes ver información general sobre el estado del estudiante:
      activo, inactivo, en proceso, entre otros.
      Para ver tu estado real, normalmente debo consultar la plataforma.
    buttons:
    - title: Ver mi estado académico
      payload: /ver_estado_estudiante
    - title: Volver al menú principal
      payload: /ir_menu_principal

  utter_ver_link_soporte:
  - text: >
      Puedes contactar soporte a través del siguiente enlace oficial de ayuda:
      [Abrir soporte en la plataforma](https://tusitio-de-soporte.com)
    buttons:
    - title: Abrir soporte
      payload: /solicitar_soporte
    - title: Volver al menú principal
      payload: /ir_menu_principal

  utter_ver_soporte_creado_info:
  - text: >
      Te muestro la información del ticket de soporte que ya fue creado para tu caso.
      Revisa tu correo o el área de soporte de la plataforma para ver el estado y las respuestas.
    buttons:
    - title: Ver enlace de soporte
      payload: /ver_link_soporte
    - title: Volver al menú principal
      payload: /ir_menu_principal

  utter_pedir_derivacion:
  - text: >
      Veo que prefieres atención humana.
      ¿Quieres que te derive con un asesor ahora mismo?
    buttons:
    - title: Sí, con un humano
      payload: /confirmacion_escalar_humano
    - title: No, seguir contigo
      payload: /negar_escalar

  utter_pedir_correo:
  - text: Por favor, dime tu correo electrónico.

  utter_gracias_url:
  - text: Gracias por el enlace, lo tendré en cuenta para revisar el problema.

  utter_pedir_confirmacion_soporte:
  - text: >
      Veo que necesitas soporte técnico.
      ¿Quieres que cree un ticket con tus datos para que un agente te contacte?

  utter_cancelar_soporte:
  - text: >
      Perfecto, no crearé un ticket de soporte.
      Si luego lo necesitas, solo dime que quieres soporte y lo abrimos.

  utter_soporte_acceso:
  - text: >
      🔑 Veamos tu acceso. Primero, verifica si tu usuario y contraseña son correctos.
      Si ya lo hiciste, dime si ves algún mensaje de error específico.

  utter_soporte_error_plataforma:
  - text: >
      ⚠️ Entiendo, estás teniendo errores en la plataforma.
      ¿Te aparece algún mensaje de error o pantalla en blanco?

  utter_estado_estudiante_resumen:
  - text: >
      Puedo ayudarte a revisar tu estado como estudiante.
      Por ahora, esta función está conectada al portal Zajuna.

  utter_contenido_curso_resumen:
  - text: >
      El contenido del curso incluye unidades, actividades y evaluaciones.
      Puedes verlo también desde tu aula en Zajuna.

  utter_derivar_a_humano_opciones:
  - text: >
      🔄 Puedo derivarte con un agente humano para que continúe tu caso.
      Primero terminaré de registrar tu solicitud de soporte y luego te pasaré con un asesor.
      ¿Te parece bien?
    buttons:
    - title: ✅ Sí, pasar con humano
      payload: /pedir_humano_directo
    - title: 🔁 Seguir con el bot
      payload: /negar_handoff

  utter_ask_soporte_mensaje:
  - text: Describe brevemente el problema o error que te ocurrió.

  utter_ask_prefer_contacto:
  - text: ¿Prefieres que soporte te contacte por correo o por teléfono?

  utter_preguntar_tipo_soporte:
  - text: ¿Cómo quieres que registremos tu caso?
    buttons:
    - title: 📨 PQRS formal
      payload: /soporte_pqrs
    - title: 💬 Mensaje interno
      payload: /soporte_interno

  utter_info_certificado:
  - text: >
      Para consultar o descargar tu certificado del SENA, ingresa a https://certificados.sena.edu.co,
      selecciona el tipo de documento, digita tu número y sigue las instrucciones de la plataforma.

  utter_ayuda_certificados_detalle:
  - text: >
      Los certificados pueden ser de estudio, de notas, laborales u otros
      formatos especiales (asistencia, participación, etc.).
      Puedo explicarte cada tipo o ayudarte a ver cuáles tienes disponibles.
    buttons:
    - title: Ver mis certificados
      payload: /consultar_certificados
    - title: Tipos de certificados
      payload: /consulta_por_tipo
    - title: Volver al menú principal
      payload: /ir_menu_principal

  utter_pedir_tema:
  - text: >
      Cuéntame, ¿sobre qué tema del SENA quieres aprender?
      Por ejemplo: contabilidad, logística, desarrollo de software, marketing digital, etc.

  utter_aprender_tema:
  - text: >
      Perfecto, hablemos sobre ese tema.
      ¿Quieres una explicación básica, intermedia o avanzada?

  utter_default:
  - text: >
      No estoy seguro de haber entendido.
      ¿Podrías reformular tu pregunta o darme más contexto?

  utter_out_of_scope:
  - text: >
      Esa pregunta está fuera de lo que puedo responder como Tutor del SENA,
      pero puedo ayudarte con temas académicos y de formación.

  utter_resumen_generado:
  - text: 'Aquí tienes un resumen claro de lo que vimos:'

  utter_emocion_detectada:
  - text: >
      Entiendo cómo te sientes. Estoy aquí para ayudarte.

  utter_auth_denegada:
  - text: >
      Entendido, no continuaremos con la autenticación por ahora.

  utter_resumir_clase:
  - text: >
      Puedo ayudarte a resumir la clase.
      ¿Qué parte o mensaje quieres que resuma exactamente?

  utter_continuar_tema:
  - text: >
      Perfecto, continuemos con el tema.
      ¿Quieres profundizar o ver ejemplos?

  utter_tema_detectado:
  - text: "Tomado el tema. Preparando explicación…"

  utter_dime_tema:
  - text: "¿Qué tema deseas aprender?"

  utter_preguntar_sobre_explicacion:
  - text: |
      🧠 **Revisión rápida del tema**

      Hasta aquí llega la explicación del tema que acabamos de estudiar.
      Antes de avanzar, me gustaría validar algo contigo:

      **¿Esta explicación te fue útil y clara?**
    buttons:
    - title: ✅ Sí, me ayudó
      payload: /encuesta_explicacion_si
    - title: ❌ No, necesito que lo expliques mejor
      payload: /encuesta_explicacion_no

  utter_explicacion_ok:
  - text: |
      ¡Excelente! 😊
      Me alegra saber que la explicación del tema te fue útil.

      A continuación te mostraré un breve **resumen académico** de lo que vimos
      y luego te preguntaré si deseas responder una **encuesta general**
      para ayudarnos a mejorar continuamente el servicio del Tutor Virtual Zajuna.

  utter_explicacion_no_clara:
  - text: >
      Gracias por decirme 🙏.
      Puedo explicarlo de otra forma el tema que venimos viendo.

  utter_preguntar_valor_explicacion:
  - text: >
      ¿Te fue útil la explicación que te di sobre este tema?
      Puedes indicarme si te ayudó o no:
    buttons:
    - title: "👍 Sí, me ayudó"
      payload: /encuesta_valor_explicacion_si
    - title: "👎 No mucho"
      payload: /encuesta_valor_explicacion_no

  utter_encuesta_satisfaccion_negativa:
  - text: >
      Gracias por tu sinceridad, eso nos ayuda a mejorar 🙏
      ¿Te gustaría que volvamos a ver este mismo tema con otra explicación más sencilla?
    buttons:
    - title: "🔁 Sí, repetir el tema"
      payload: /encuesta_rever_tema_si
    - title: "🚫 No, gracias"
      payload: /encuesta_rever_tema_no

  utter_post_reexplicacion_encuesta:
  - text: >
      Listo, te di una nueva explicación del tema.
      ¿Ahora sientes que la información fue más clara y útil?
    buttons:
    - title: "👍 Sí, ahora sí me ayudó"
      payload: /encuesta_valor_explicacion_si
    - title: "👎 Todavía no mucho"
      payload: /encuesta_valor_explicacion_no

  utter_soporte_tecnico_menu:
  - text: >
      Veo que necesitas soporte técnico 🛠
      ¿Qué tipo de problema estás teniendo?
    buttons:
    - title: 🔑 No puedo ingresar
      payload: /problema_no_ingreso
    - title: 🧾 Pantalla en blanco
      payload: /pantalla_blanca
    - title: ❗ Error en actividad
      payload: /error_actividad
    - title: 🧩 Otro problema técnico
      payload: /otro_problema_tecnico

  utter_reexplicacion_pedir_tutor:
  - text: >
      Intenté explicarlo de otra forma 😊.
      Si aún sientes que no es suficiente, puedo derivarte con tu tutor para verlo con más calma
      o podemos seguir con el bot.
    buttons:
    - title: 👨‍🏫 Hablar con mi tutor
      payload: /contactar_tutor
    - title: 🔁 Seguir con el bot
      payload: /continuar_consulta
    - title: 🏠 Ir al menú principal
      payload: /ir_menu_principal

  utter_ofrecer_contacto_tutor:
  - text: >
      ¿Deseas contactar a tu tutor para seguir trabajando este tema?
    buttons:
    - title: ✉️ Enviar correo al tutor
      payload: /enviar_correo_tutor
    - title: 🏠 Volver al menú principal
      payload: /ir_menu_principal

  utter_contactar_tutor_opciones:
  - text: >
      Puedo ayudarte a contactar a tu tutor.
      ¿Cómo prefieres hacerlo?
    buttons:
    - title: ✉️ Enviar correo al tutor
      payload: /enviar_correo_tutor
    - title: 🔗 Ver datos de contacto / enlace
      payload: /ver_link_soporte
    - title: 🏠 Volver al menú principal
      payload: /ir_menu_principal

  utter_contactar_tutor_confirmacion:
  - text: >
      Listo ✅ He registrado que quieres contactar a tu tutor.
      Te mostraré la información necesaria o enviaré el correo según la opción que elijas.

  utter_resumen_sesion:
  - text: |
      🧾 **Resumen de tu sesión académica**

      - Tema trabajado: **{tema_actual}**
      - Revisamos el tema que solicitaste y te di una explicación estructurada.
      - Validamos si la explicación fue útil para ti.
      - Registré tu percepción para seguir mejorando el acompañamiento.

  utter_opciones_finales_aprendizaje:
  - text: |
      Para ayudarnos a mejorar el Tutor Virtual Zajuna 💙
      ¿Te gustaría responder una **encuesta general** sobre tu experiencia con el asistente?
    buttons:
    - title: "📝 Sí, responder encuesta"
      payload: /iniciar_encuesta
    - title: "🚫 No, gracias"
      payload: /no_encuesta_general
    - title: "🔚 Cerrar conversación"
      payload: /terminar_conversacion_segura

  utter_preguntar_satisfaccion:
  - text: 📊 Antes de finalizar, ¿cómo calificarías tu experiencia con Zajuna?
    buttons:
    - title: 🌟 Excelente
      payload: "/respuesta_satisfecho{'nivel_satisfaccion': 'excelente'}"
    - title: 🙂 Buena
      payload: "/respuesta_satisfecho{'nivel_satisfaccion': 'buena'}"
    - title: 😐 Regular
      payload: "/respuesta_insatisfecho{'nivel_satisfaccion': 'regular'}"
    - title: 😞 Mala
      payload: "/respuesta_insatisfecho{'nivel_satisfaccion': 'mala'}"
    - title: 💾 Terminar y guardar progreso
      payload: /terminar_conversacion_segura_autosave

  utter_encuesta_insatisfaccion:
  - text: >
      Gracias por contarnos 🙏
      Puedo derivarte a un tutor o dejar registro de tu experiencia. ¿Qué prefieres?
    buttons:
    - title: 👨‍🏫 Derivar a tutor
      payload: /contactar_tutor
    - title: 📝 Registrar y seguir con el bot
      payload: /continuar_consulta

  utter_encuesta_satisfaccion_positiva:
  - text: >
      ¡Me alegra saber que la explicación te fue útil! 🙌
      Para mejorar el tutor virtual, ¿cómo calificarías la experiencia con el chatbot en una escala de 1 a 5,
      donde 1 es "muy mala" y 5 es "excelente"?

  utter_gracias_retroalimentacion:
  - text: |
      🙏 ¡Gracias por tu comentario! Lo tendremos muy en cuenta.
      ¿Deseas continuar con otra consulta o finalizar la conversación?
    buttons:
    - title: 🏠 Volver al menú principal
      payload: /ir_menu_principal
    - title: 👋 Terminar conversación
      payload: /terminar_conversacion
    - title: 💾 Terminar y guardar progreso
      payload: /terminar_conversacion_segura_autosave

  utter_despedida_profesional_encuesta:
  - text: >
      Gracias por usar el Tutor Virtual Zajuna 💙
      Si más adelante necesitas apoyo con otro tema o con la plataforma, estaré aquí para ayudarte.

  utter_despedida_final:
  - text: >
      Gracias por usar el asistente. ¡Que tengas un excelente día! 👋

  utter_ofrecer_humano:
  - text: >
      Veo que el problema todavía no está resuelto 😕.
      Puedo derivarte con un agente humano de soporte para revisar tu caso con más detalle.
    buttons:
    - title: 👨‍💻 Hablar con un agente humano
      payload: /pedir_humano_directo
    - title: 🔁 Seguir intentando con el bot
      payload: /continuar_consulta

  utter_volver_menu_principal:
  - text: >
      Te regreso al menú principal. ¿Sobre qué te gustaría continuar?
    buttons:
    - title: 🎓 Académico
      payload: /menu_academico
    - title: 🛠 Soporte técnico
      payload: /soporte_general
    - title: 🏫 Trámites académicos / administrativos
      payload: /menu_administrativo

  utter_handoff_por_fallos:
  - text: >
      Veo que hubo varias dificultades técnicas 😕
      Te conectaré con un asesor humano para ayudarte mejor.
    buttons:
    - title: ✅ Continuar con derivación a humano
      payload: /confirmacion_escalar_humano
    - title: 💾 Terminar y guardar progreso
      payload: /terminar_conversacion_segura_autosave

  utter_handoff_en_cola:
  - text: 📨 Te he puesto en cola con un asesor humano. Te notificaremos en breve.
    buttons:
    - title: 💾 Terminar guardando progreso
      payload: /terminar_conversacion_segura_autosave
    - title: 🏠 Volver al menú
      payload: /ir_menu_principal

  utter_continuar_tema_menu:
  - text: >
      Genial, sigamos entonces 👌
      Puedes elegir una opción para continuar:
    buttons:
    - title: 🎓 Menú académico
      payload: /menu_academico
    - title: 📜 Mis certificados
      payload: /consultar_certificados
    - title: 👨‍🎓 Ver estado como estudiante
      payload: /ver_estado_estudiante
    - title: 🛠 Soporte técnico
      payload: /soporte_general
    - title: 🏠 Menú principal
      payload: /ir_menu_principal

  utter_derivar_humano_en_progreso:
  - text: >
      Conectándote con un asesor... ⌛
      Por favor espera un momento.

  utter_derivacion_cancelada:
  - text: >
      Sin problema 👍
      Continuamos por aquí. ¿Qué deseas hacer?
    buttons:
    - title: 🏠 Menú principal
      payload: /ir_menu_principal
    - title: 🎓 Ver estado académico
      payload: /ver_estado_estudiante
    - title: 📜 Consultar certificados
      payload: /consultar_certificados
    - title: 💾 Terminar y guardar progreso
      payload: /terminar_conversacion_segura_autosave

  utter_confirmar_cierre_con_autosave:
  - text: >
      Detecté que tienes una **encuesta sin completar**.
      Puedo guardarla automáticamente antes de cerrar. ¿Quieres hacerlo?
    buttons:
    - title: ✅ Sí, guardar y cerrar
      payload: /confirmar_cierre_autosave
    - title: ❌ No, descartar encuesta
      payload: /cancelar_cierre_autosave

  utter_cancelar_cierre:
  - text: >
      Perfecto 😊, continuemos entonces.
      ¿En qué más puedo ayudarte?

  utter_limpiar_autosave:
  - text: >
      Los datos temporales fueron limpiados correctamente ✅

  utter_confirmar_tema_academico:
  - text: >
      Perfecto, trabajemos el tema que acabas de mencionar. 📚
      Te daré una explicación clara y desde cero. Luego revisamos si te fue útil.

  utter_preguntar_explicacion_tema:
  - text: >
      ✅ ¿Te sirvió esta explicación del tema?
    buttons:
    - title: "Sí, me quedó claro"
      payload: /encuesta_explicacion_si
    - title: "No, aún tengo dudas"
      payload: /encuesta_explicacion_no

  utter_reconocer_dudas_tema:
  - text: >
      Gracias por decirme que aún tienes dudas, eso también hace parte del aprendizaje. 🙂
      Voy a explicarlo de otra forma, más sencilla y con otro enfoque.

  utter_preguntar_tutor_academico:
  - text: >
      ¿Te gustaría que un tutor humano revise este tema contigo de forma más personalizada?
    buttons:
    - title: "Sí, quiero hablar con un tutor"
      payload: /confirmacion_escalar_humano
    - title: "No, prefiero seguir con el bot"
      payload: /negar_escalar

  utter_preguntar_encuesta_general:
  - text: >
      Para ayudarnos a mejorar el Tutor Virtual Zajuna, ¿te gustaría responder
      una encuesta general muy corta sobre tu experiencia?
    buttons:
    - title: "📝 Contestar encuesta"
      payload: /iniciar_encuesta
    - title: "🙈 No, en otro momento"
      payload: /no_encuesta_general
    - title: "❌ Cerrar conversación"
      payload: /terminar_conversacion_segura

  utter_agradecimiento_encuesta_general:
  - text: >
      🙏 Muchas gracias por responder la encuesta y usar el Tutor Virtual Zajuna 💙
      Valoramos mucho tu retroalimentación, nos ayuda a seguir mejorando el servicio
      para ti y otros aprendices.

      Cuando quieras, podrás volver para resolver nuevas dudas académicas,
      soporte técnico o trámites administrativos.

  utter_menu_academico:
  - text: >
      Estás en el menú académico de Zajuna 🎓.
      Elige una opción o escribe directamente qué deseas aprender o consultar.
    buttons:
    - title: 📚 Aprender un tema
      payload: /aprender_tema
    - title: 📊 Estado del estudiante
      payload: /ver_estado_estudiante
    - title: 📜 Certificados
      payload: /consultar_certificados
    - title: 📈 Progreso de cursos
      payload: /consultar_progreso_curso
    - title: ⏰ Horarios
      payload: /consultar_horarios_clases
    - title: 📝 Calificaciones
      payload: /consultar_calificaciones
    - title: 👨‍🏫 Tutor asignado
      payload: /tutor_asignado
    - title: 🏠 Menú principal
      payload: /ir_menu_principal

  utter_auth_ok:
  - text: >
      ✅ Autenticación correcta. ¿Qué deseas consultar?
    buttons:
    - title: 📊 Estado del estudiante
      payload: /ver_estado_estudiante
    - title: 📜 Certificados
      payload: /consultar_certificados
    - title: 📈 Progreso de cursos
      payload: /consultar_progreso_curso
    - title: ⏰ Horarios
      payload: /consultar_horarios_clases
    - title: 📝 Calificaciones
      payload: /consultar_calificaciones
    - title: 👨‍🏫 Tutor asignado
      payload: /tutor_asignado
    - title: 🏠 Menú principal
      payload: /ir_menu_principal

  utter_menu_administrativo:
  - text: >
      Has elegido 🧾 Administrativo. ¿Qué deseas gestionar?
    buttons:
    - title: ❓ Preguntas frecuentes
      payload: /preguntas_frecuentes
    - title: 📬 PQRS / Buzón de sugerencias
      payload: /pqrs
    - title: 📑 Certificados generales
      payload: /certificados_generales
    - title: 🏠 Menú principal
      payload: /ir_menu_principal

  utter_menu_soporte:
  - text: >
      Veo que necesitas soporte técnico 🛠
      ¿Qué tipo de problema estás teniendo?
    buttons:
    - title: 🔑 No puedo ingresar
      payload: /problema_no_ingreso
    - title: 🧾 Pantalla en blanco
      payload: /pantalla_blanca
    - title: ❗ Error en actividad
      payload: /error_actividad
    - title: 🧩 Otro problema técnico
      payload: /otro_problema_tecnico
    - title: 🏠 Menú principal
      payload: /ir_menu_principal

  utter_menu_principal:
  - text: >
      ¡Hola! Soy tu asistente Zajuna 👋
      Este es el menú principal. ¿Qué deseas hacer?
    buttons:
    - title: 🎓 Académico
      payload: /menu_academico
    - title: 🛠 Soporte técnico
      payload: /soporte_general
    - title: 🏫 Trámites académicos / administrativos
      payload: /menu_administrativo

  utter_ofrecer_continuar:
  - text: >
      ¿Deseas realizar otra consulta o finalizar la conversación?
    buttons:
    - title: 🏠 Volver al menú principal
      payload: /ir_menu_principal
    - title: 👋 Finalizar conversación
      payload: /terminar_conversacion
    - title: 💾 Terminar y guardar progreso
      payload: /terminar_conversacion_segura_autosave

  utter_despedida_profesional:
  - text: >
      👋 Gracias por usar el asistente Zajuna. ¡Que tengas un excelente día! 🌟

actions:
- action_estado_estudiante
- action_tutor_asignado
- action_listar_certificados
- action_ver_certificados
- action_ingreso_zajuna
- action_recuperar_contrasena
- action_zajuna_get_certificados
- action_zajuna_get_estado_estudiante
- action_reiniciar_conversacion
- action_mostrar_token
- action_handle_with_llm
- action_route_llm_intent
- action_ping_servidor
- action_enviar_soporte
- action_derivar_y_registrar_humano
- action_conectar_humano
- action_preguntar_resolucion
- action_set_authenticated_true
- action_enviar_correo_recuperacion
- action_confirmar_cierre
- action_finalizar_conversacion
- action_cancelar_cierre
- action_ofrecer_humano
- action_handoff_cancelar
- action_auto_resume
- action_reanudar_auto
- action_confirmar_cierre_seguro
- action_autosave_encuesta
- action_guardar_autosave_mongo
- action_cargar_autosave_mongo
- action_autoresume_conversacion
- action_reset_conversacion_segura
- action_registrar_encuesta
- action_guardar_feedback
- action_ofrecer_continuar_tema
- action_set_encuesta_tipo
- action_validate_encuesta_satisfaccion_form
- action_health_check
- action_autosave_snapshot
- action_registrar_intento_form
- action_verificar_max_intentos_form
- action_derivar_humano_confirmada
- action_cancelar_derivacion
- action_soporte_submit
- action_ver_estado_estudiante
- action_verificar_estado_encuesta
- action_guardar_progreso_encuesta
- action_terminar_conversacion_segura
- action_ir_menu_principal
- action_mostrar_menu_principal_quick
- action_mostrar_certificados_carousel
- action_mostrar_login_hint_presentacion
- action_guardian_guardar_progreso
- action_guardian_cargar_progreso
- action_guardian_pausar
- action_guardian_reanudar
- action_guardian_reset
- action_notificar_desconexion
- action_notificar_inactividad
- action_notificar_reconexion
- action_guardar_estado_seguridad
- action_recuperar_estado_seguridad
- action_validate_soporte_form
- action_enviar_correo_tutor
- action_verificar_proceso_activo_autosave
- action_guardar_encuesta_incompleta
- action_confirmar_cierre_autosave
- action_cancelar_cierre_autosave
- action_escalar_a_humano
- action_verificar_proceso_activo
- action_enviar_correo
- action_cancelar_cierre_segura
- action_enviar_soporte_directo
- action_iniciar_soporte
- action_set_default_tipo_usuario
- action_analizar_estado_usuario
- action_procesar_soporte
- action_marcar_escalar_humano
- action_handoff_en_cola
- action_memory_wrapper
- action_resumen_sesion_llm
- action_incrementar_turnos_conversacion
- action_reset_turnos_conversacion
- action_consultar_certificados
- action_consultar_horarios_clases
- action_consultar_progreso_curso
- action_session_start
- action_historial_academico
- action_explicar_tema_llm
- action_reexplicar_tema_llm
