version: "3.1"

nlu:

  - intent: ver_certificados_info
    examples: |
      - muéstrame certificados sin login
      - ver certificados de ejemplo
      - listar certificados rápidos
      - ver certificados demo
      - quiero ver certificados de ejemplo
      - información de certificados sin iniciar sesión
      - ver certificados de muestra

  - intent: ver_estado_estudiante
    examples: |
      - ver mi estado académico
      - ¿cuál es mi estado?
      - estado del curso
      - muéstrame mi estado de estudiante
      - ver estado del aprendiz
      - consultar estado académico
      - estado académico actual
      - revisar mi progreso académico
      - cómo va mi matrícula
      - estado del estudiante
      - cómo voy en el curso
      - dime mi estado
      - quiero saber mi estado
      - estado académico
      - mi progreso académico
      - cuál es mi estado
      - cuál es mi estado como estudiante
      - status académico
      - cuál es mi estado académico
      - información sobre el estado del estudiante
      - qué significa estado académico
      - tipos de estado del estudiante
      - explícamelos estados académicos
      - cómo funciona el estado del estudiante

  - intent: horarios_calendario
    examples: |
      - ver horario
      - calendario de clases
      - fechas académicas
      - cuándo son mis clases
      - calendario del curso
      - horarios del semestre

  - intent: confirmar_autenticacion
    examples: |
      - ya inicié sesión
      - listo, ya me conecté
      - ya estoy autenticado
      - ya inicié sesión
      - listo, ya me autenticqué
      - ya me logueé
      - ya entré a la plataforma
      - ya estoy autenticado

  - intent: negar_autenticacion
    examples: |
      - no he iniciado sesión
      - todavía no me conecto
      - no estoy autenticado

  - intent: reiniciar_conversacion
    examples: |
      - reiniciar conversación
      - reinicia el chat
      - resetear conversación
      - limpiar todo
      - empezar desde cero

  - intent: limpiar_sesion
    examples: |
      - limpiar sesión
      - borrar contexto
      - eliminar datos de sesión
      - limpiar estado del chat

  - intent: mostrar_token
    examples: |
      - muéstrame mi token [usuario](tipo_usuario)
      - quiero ver el token del [admin](tipo_usuario)
      - mostrar token para el [usuario](tipo_usuario)
      - token para el [admin](tipo_usuario)
      - ver token

  - intent: ping_servidor
    examples: |
      - ping
      - probar servidor
      - está vivo el bot
      - verificar servidor
      - prueba de conexión
 
  - intent: solicitar_soporte
    examples: |
      - necesito soporte
      - quiero reportar un problema
      - ayuda, por favor
      - tengo un inconveniente
      - contactar a soporte
      - abrir un ticket
      - hablar con soporte
      - necesito soporte técnico
      - ayuda con la plataforma
      - problemas técnicos
      - soporte por favor
      - tengo un problema con el campus
      - asistencia técnica
      - me puedes ayudar con un error
      - abrir ticket de soporte
      - comunicarme con soporte
      - quiero reportar un incidente
      - quiero crear un caso de soporte
      - necesito abrir un caso técnico
      - quiero registrar un problema en la plataforma
      - deseo ayuda con un fallo del sistema
      - si, necesito soporte técnico
      - tengo un problema técnico EN ZAJUNA
      - necesito ayuda técnica rapida
      - ayuda en la plataforma

  - intent: iniciar_encuesta
    examples: |
      - quiero hacer una encuesta
      - me gustaría dar feedback
      - deseo evaluar el soporte
      - iniciar encuesta
      - empezar encuesta de satisfacción
      - abrir encuesta

  - intent: enviar_credenciales
    examples: |
      - voy a iniciar sesión
      - ingresar mis credenciales
      - iniciar sesión ahora
      - quiero ingresar mis datos
      - déjame entrar con mi usuario y contraseña

  - intent: affirm
    examples: |
      - sí
      - correcto
      - claro
      - de acuerdo
      - por supuesto
      - claro que sí
      - afirmativo
      - ok
      - perfecto
      - de una
      - correcto
      - sí, crea el ticket
      - si, crea el ticket
      - sí, por favor crea el ticket
      - sí, abre el ticket
      - sí, quiero que crees el ticket
      - adelante, crea el ticket
      - sí, haz el ticket
      - sí, genera el ticket 
      - sí, por favor genera el ticket
      - sí, crea el caso de soporte
      - sí, abre el caso de soporte
      - sí, quiero que crees el caso de soporte
      - adelante, crea el caso de soporte

  - intent: provide_email
    examples: |
      - mi correo es [usuario@ejemplo.com](email)
      - mi email es [test@gmail.com](email)
      - es [prueba@correo.com](email)

  - intent: reanudar_auto_si
    examples: |
      - sí, continuar desde donde guardaste
      - sí, retomemos desde el autosave
      - reanudar desde el último punto
      - sí, retomar sesión guardada

  - intent: reanudar_auto_no
    examples: |
      - no, empezar de nuevo
      - no quiero reanudar
      - comenzar nuevo chat
      - no retomar
      - empezar de cero
      - no quiero usar el autosave

  - intent: cancelar_cierre
    examples: |
      - no, mejor sigo
      - cancela el cierre
      - aún no
      - no quiero cerrar
      - no, continuar
      - sigamos
      - quiero seguir
      - no cierres
      - mejor continuemos
      - aún quiero continuar
      - no, mejor sigamos
      - espera, no cierres todavía
      - prefiero seguir hablando
      - no, aún necesito ayuda
      - sigamos un poco más

  - intent: reanudar_conversacion
    examples: |
      - continuar encuesta
      - seguir donde estaba
      - continuar donde iba
      - retomar conversación
      - reanudar chat
      - seguir donde íbamos

  - intent: limpiar_autosave
    examples: |
      - limpia autosave
      - borra datos guardados
      - reinicia la sesión

  - intent: problema_resuelto_si
    examples: |
      - sí quedó resuelto
      - ya quedó
      - listo, solucionado
      - todo bien ya
      - quedó resuelto

  - intent: continuar_tema_si
    examples: |
      - sí quiero seguir
      - sí, otro tema
      - quiero ver otra cosa
      - quiero continuar con otro tema
      - sigamos con otra cosa
      - continuar con el menú
      - ver más opciones
      - seguir con el asistente
      - quiero continuar con este tema
      - sigamos hablando de esto
      - seguir con el mismo tema
      - si dale
      - si, desde cero
      - dale
      - continuar
      - sí, continúa
      - si
      - sí, vavos
      - continuemos
      - sigue
      - listo continúa
      - ok sigue
      - continúa con el tema
      - bueno
      - listo
      - me parece bien
      - quiero seguir con este tema
      - continuar con este tema
      - seguir hablando de esto
      - quiero más información sobre esto
      - profundizar en este tema
      - continuar con el mismo tema

  - intent: explorar_temas
    examples: |
      - quiero ver cursos
      - qué temas puedo aprender
      - explorar contenidos
      - muéstrame los cursos
      - qué programas tienen
      - ver oferta académica
      - cursos disponibles
      - quiero aprender algo nuevo
      - ver cursos disponibles
      - ver catálogo completo
      - muéstrame el catálogo
      - catálogo de cursos detallado
      - catálogo

  - intent: cambiar_idioma_ingles
    examples: |
      - quiero usar el chat en inglés
      - change to english
      - switch to english
      - responde en inglés
      - cambiar idioma a inglés
      - I prefer English
      - talk to me in English

  - intent: cambiar_idioma_espanol
    examples: |
      - volver a español
      - regresar a idioma español
      - hablar en español
      - ponlo en español
      - cambia al español
      - quiero español
      - switch back to spanish

  - intent: ir_menu_principal
    examples: |
      - ir al menú
      - voy al menú
      - menú principal
      - regresar al menú
      - volver al menú principal
      - ir al menú
      - regresar al menú
      - mostrar menú principal
      - ir al inicio
      - muéstrame el menú
      - ir al menú principal
      - volver al menú
      - regresar al inicio
      - muéstrame el menú
      - abrir menú principal
      - ver opciones
      - quiero el menú
      - volver a las opciones
      - mostrar menú
      - regresar al menú
      - volver al menú principal
      - quiero el menú principal
      - volver a opciones
      - inicio por favor
      - menú rápido
      - ir al menú rápido

  - intent: terminar_conversacion
    examples: |
      - terminar conversación
      - quiero terminar la conversación
      - finalizar chat
      - terminar chat
      - cerrar chat
      - quiero cerrar el chat
      - cerrar conversación
      - cerrar este chat
      - salir del chat
      - salir del asistente
      - quiero salir
      - quiero cerrar la conversación
      - ya no necesito más ayuda
      - podemos terminar aquí
      - hasta aquí está bien
      - eso es todo, gracias
      - ya no necesito ayuda
      - deseo salir del sistema
      - terminar sesión
      - salir del flujo

  - intent: guardar_snapshot
    examples: |
      - guarda un snapshot
      - haz un snapshot de la sesión
      - guardar snapshot
      - guardar estado de la conversación
      - forzar autosave
      - guardar progreso técnico
      - crear snapshot de guardian
      - ejecutar autosave

  - intent: ayuda_guardian
    examples: |
      - ayuda guardian
      - qué hace guardian
      - para qué sirve el snapshot
      - explícame el autosave
      - ayuda con snapshot

  - intent: deny
    examples: |
      - no
      - no gracias
      - mejor no
      - negativo
      - prefiero que no
      - no quiero
      - no por ahora
      - nah
      - cancela
      - ahora no
      - prefiero luego
      - no, no crees el ticket
      - mejor no abras el ticket
      - no, no quiero que crees el ticket
      - no, no abras el caso de soporte
      - no, no quiero que crees el caso de soporte
      - no, gracias

  - intent: fallback
    examples: |
      - no entiendo
      - qué puedo hacer
      - ayuda
      - menú
      - repetir opciones
      - vuelve a mostrar opciones
      - repite, por favor
      - no sé cómo responder

  - intent: auth_login_cmd
    examples: |
      - login
      - abrir login
      - abrir inicio de sesión
      - autenticación
      - comando de login

  - intent: saludo
    examples: |
      - hola
      - buenos días
      - buenas
      - qué tal
      - hey bot
      - hola de nuevo
      - buenas tardes
      - buenas noches
      - hola chatbot
      - hola, ¿me ayudas?
      - holi
      - qué más
      - buen día
      - hola, qué tal?
      - qué onda
      - hola!
      - hola
      - hola, ¿cómo estás?
      - hola, como estas
      - hola, qué tal
      - buenas noches!
      - buenas tardes!
      - buenas días!
      - que tal te va
      - qué hay de nuevo
      - holaa
      - holaaa
      - que hay de nuevo?
      - que me cuentas?
      - qué tal todo?
      - que me cuentas
      - qué tal todo
      - hola, soy [Carlos](nombre)
      - buenos días, mi nombre es [María](nombre)
      - hola, me llamo [Andrés](nombre)
      - soy [Luisa](nombre), necesito ayuda
      - hla
      - ola
      - holi
      - hola buenos días
      - hola buenas tardes
      - hola buenas noches 
      - holo    
      - holis
      - holaaaaaaaaaaaaaa
      - holaaa buenos dias
      - holaaa buenas tardes
      - holaaa buenas nochess
      - hellou
      - hey
      - hi there
      - hala
      - HALA

  - intent: recuperar_contrasena
    examples: |
      - olvidé mi contraseña
      - no recuerdo mi clave
      - recuperar acceso
      - restablecer contraseña
      - ayuda con mi contraseña
      - recuperar contraseña
      - necesito recuperar el acceso
      - no puedo entrar a mi cuenta

  - intent: terminar_conversacion_segura
    examples: |
      - quiero cerrar el chat pero guarda mi progreso
      - cerrar conversación de forma segura
      - terminar pero guardar lo que llevo
      - salir y guardar la encuesta
      - quiero terminar la conversación de forma segura
      - finalizar pero que quede guardado
      - cerrar chat con autosave
      - terminar conversación segura

  - intent: cancelar_cierre_segura
    examples: |
      - no quiero cierre seguro
      - no cierres de forma segura
      - cancelar cierre pero seguir en el chat
      - continuar en el chat
      - seguir con la conversación
      - no cerrar todavía
      - prefiero seguir

  - intent: guardian_pausar_conversacion
    examples: |
      - pausar conversación
      - terminar por ahora
      - guarda y pausa
      - guardar y pausar
      - detener por ahora
      - pausar el chat

  - intent: guardian_reanudar_conversacion
    examples: |
      - reanudar
      - reanudar chat guardado
      - reanudar sesión guardada
      - recuperar conversación guardada

  - intent: guardian_guardar_progreso
    examples: |
      - guarda mi progreso
      - salvar estado
      - guardar avance

  - intent: notificar_desconexion
    examples: |
      - Me desconecté
      - Se cayó la conexión
      - Perdí la sesión
      - Hubo un corte de red

  - intent: notificar_inactividad
    examples: |
      - Estuve ausente
      - Dejé de usar el chat
      - No he respondido hace rato
      - Me quedé inactivo

  - intent: notificar_reconexion
    examples: |
      - Volví al chat
      - Ya regresé
      - Me reconecté
      - Estoy de nuevo aquí

  - intent: recuperar_estado_seguridad
    examples: |
      - Recupera mi sesión
      - Restaura el progreso
      - Carga el estado anterior

  - intent: pantalla_blanca
    examples: |
      - veo todo blanco
      - pantalla en blanco
      - la página queda en blanco
      - se queda congelado en blanco
      - tengo la pantalla en blanco
      - se queda la pantalla en blanco
      - solo veo una pantalla blanca
      - la plataforma se queda en blanco
      - aparece pantalla en blanco
      - pantalla completamente en blanco
      - pantalla blanca al ingresar
      - pantalla blanca al cargar el curso
      - white screen
      - white page
      - blank screen
      - la pantalla se queda blanca
      - no carga y queda la pantalla blanca
      - se queda la pantalla congelada en blanco
      - pantalla negra
      - se queda la pantalla negra
      - veo pantalla negra
      - black screen
      - pantalla oscura
      - pantalla completamente negra

  - intent: error_actividad
    examples: |
      - error al abrir una actividad
      - me sale error al acceder a contenido
      - no puedo abrir la actividad
      - actividad no abre
      - error en el cuestionario
      - se bloquea al abrir la actividad
      - no deja entregar la actividad

  - intent: otro_problema_tecnico
    examples: |
      - otro tipo de error técnico
      - diferente problema técnico
      - es otro fallo
      - tengo un problema distinto
      - error raro en el sistema
      - no sé qué error es
      - un problema diferente
      - tengo otro problema técnico

  - intent: respuesta_satisfecho
    examples: |
      - sí, quedé satisfecho
      - todo bien, gracias
      - estoy satisfecho
      - me sirvió, gracias
      - quedé contento con la ayuda

  - intent: respuesta_insatisfecho
    examples: |
      - no quedé satisfecho
      - no funcionó
      - no se resolvió mi problema
      - no me gustó la atención

  - intent: enviar_correo_tutor
    examples: |
      - enviar correo al tutor
      - escribir a mi tutor
      - contactar a mi tutor por correo
      - mandar email al tutor

  - intent: continuar_consulta
    examples: |
      - consultar otro tema
      - seguir con otra consulta
      - ver otra cosa
      - seguir preguntando

  - intent: negar_cierre
    examples: |
      - no quiero cerrar el chat
      - no cierres la conversación
      - no quiero que se cierre
      - no quiero salir todavía
      - no quiero salir del chat
      - quiero seguir en el chat

  - intent: confirmar_cierre_segura
    examples: |
      - sí, ciérralo y guarda
      - sí, terminar y guardar
      - confirmo el cierre seguro
      - ok, cierra y guarda
      - está bien, termina guardando
      - confirma el cierre seguro

  - intent: terminar_conversacion_segura_autosave
    examples: |
      - quiero cerrar el chat de forma segura
      - terminar conversación pero guardando progreso
      - salir y guardar lo que llevo
      - pausar conversación con autosave
      - quiero terminar pero guarda mi progreso
      - cerrar sesión con autosave
      - terminar ahora pero sin perder la encuesta

  - intent: confirmar_cierre_autosave
    examples: |
      - sí, cerrar y guardar
      - confirmar cierre con autosave
      - sí, termina de forma segura
      - ok, cierra la sesión y guarda
      - sí, terminar ahora con autosave
      - correcto, finalizar todo guardando

  - intent: cancelar_cierre_autosave
    examples: |
      - no, mejor seguimos
      - no quiero cerrar todavía
      - cancela el cierre seguro
      - quiero continuar con la conversación
      - no, continuar con el chat
      - aún no quiero salir
      - sigamos hablando

  - intent: certificado_estudio
    examples: |
      - quiero un certificado de estudio
      - necesito mi certificado de estudio
      - certificado de estudiante
      - constancia de estudio
      - certificado de que estoy estudiando
      - certificado de matrícula
      - certificado académico de estudio
     
  - intent: certificado_notas
    examples: |
      - quiero un certificado de notas
      - necesito mi certificado de calificaciones
      - certificado de notas
      - historial de notas
      - certificado de calificaciones del curso
      - constancia de notas
      - certificado con mis calificaciones
      - certificado de calificaciones
      - quiero certificado de notas
      
  - intent: certificado_laboral
    examples: |
      - necesito un certificado laboral
      - certificado de trabajo
      - constancia laboral
      - certificado de experiencia laboral
      - certificado para mi empresa
      - certificado de que trabajo aquí
      - certificado laboral
      
  - intent: certificado_otro
    examples: |
      - es otro tipo de certificado
      - necesito otro tipo de certificado
      - no está en la lista
      - es un certificado diferente
      - otro certificado
      - certificado especial
      - otro tipo de certificado
      - necesito un certificado especial
      - mi certificado no está en la lista

  - intent: descargar_certificado
    examples: |
      - descargar certificado
      - quiero descargar mi certificado
      - bajar mi certificado en PDF
      - descargar mis certificados
      - necesito el certificado en PDF
      - descargar constancia

  - intent: ayuda_certificados
    examples: |
      - ayuda con certificados
      - no sé qué certificado elegir
      - explícarme los tipos de certificados
      - información sobre certificados
      - qué certificado me sirve
      - necesito orientación sobre certificados
      - necesito ayuda con los certificados
      - no entiendo los certificados
      - explícamelos certificados
      - qué certificados puedo sacar
      - no sé qué certificado escoger
      - quiero información sobre certificados
      - qué tipos de certificados hay
      - explícamelos tipos de certificados
      - qué diferencia hay entre los certificados
      - qué tipos de certificado manejan
      - información detallada de los certificados

  - intent: consulta_por_identificacion
    examples: |
      - quiero consultar por identificación
      - buscar certificado con mi cédula
      - consultar certificado por documento
      - usar mi número de identificación
      - consulta con mi número de documento
      - ver certificados con mi cédula
      - consultar certificado con mi cédula
      - buscar mis certificados por documento
      - consulta con mi cédula

  - intent: consulta_por_solicitud
    examples: |
      - consultar por número de solicitud
      - tengo un número de solicitud
      - buscar certificado con el número de solicitud
      - consulta usando mi radicado
      - revisar certificado por código de solicitud
      - buscar certificado por código de solicitud
      - revisar certificado con el radicado
      - usar el número de solicitud
      - consulta con mi radicado

  - intent: consulta_por_tipo
    examples: |
      - consultar por tipo de certificado
      - buscar certificado por tipo
      - elegir el tipo de certificado
      - filtrar por tipo de certificado
      - ver certificados según el tipo
      - quiero filtrar por tipo de certificado
      - consulta por tipo de constancia

  - intent: contactar_tutor
    examples: |
      - quiero contactar a mi tutor
      - cómo puedo escribirle a mi tutor
      - contactar a mi tutor
      - hablar con mi tutor
      - enviar mensaje a mi tutor
      - necesito comunicarme con mi tutor
      - quiero enviar un correo a mi tutor
      - necesito escribirle a mi tutor

  - intent: continue
    examples: |
      - continúa por favor
      - puedes continuar
      - seguir con lo que estabas
      - continúa con la explicación
      - continúa con lo que estabas diciendo
      - sigue con la explicación
      - sigue adelante
      - continue
      - continue please
      - sigue por favor

  - intent: dar_retroalimentacion
    examples: |
      - quiero dar retroalimentación
      - quiero dar feedback
      - me gustaría dejar un comentario
      - quiero evaluar el servicio
      - quiero evaluar el soporte
      - deseo dar mi opinión
      - quiero dejar una sugerencia
      - quiero dejar una queja
      - quiero responder la encuesta
      - me gustaría dar mi retroalimentación
      - deseo evaluar el servicio
      - quiero evaluar el asistente
      - quiero dejar mi opinión

  - intent: pedir_mensaje
    examples: |
      - quiero enviar un mensaje
      - quiero enviar un mensaje a soporte
      - enviar mensaje al soporte
      - deseo contactar a soporte por mensaje
      - escribir un mensaje sobre mi problema
      - quiero mandar un mensaje al soporte
      - quiero dejar un mensaje
      - quiero explicar mi problema por mensaje

  - intent: enviar_correo
    examples: |
      - enviar correo
      - quiero enviar un correo
      - mandar email
      - enviar un mensaje por correo
      - enviar correo al soporte
      - enviar correo de ayuda

  - intent: continuar_tema_no
    examples: |
      - no quiero seguir con este tema
      - no, ya terminé con este tema
      - no quiero continuar
      - no, gracias, ya está bien
      - prefiero no seguir con el tema
      - no quiero ver otra cosa
      - ya terminé
      - finalizar conversación

  - intent: cancelar
    examples: |
      - cancelar
      - cancelar acción
      - no quiero seguir con esto
      - olvida lo anterior
      - anular proceso
      - detener lo que estás haciendo
      - no quiero hacer eso
      - detener proceso
      - anular cierre
      - no continúes con eso

  - intent: cerrar_chat
    examples: |
      - cerrar solo el chat
      - cerrar la ventana de chat
      - quiero cerrar la ventana de chat
      - cerrar la conversación pero seguir en la plataforma
      - cerrar este chat de la página

  - intent: confirmar_derivacion
    examples: |
      - confirmar derivación
      - sí, pásame con un asesor
      - sí, con un asesor
      - adelante, deriva el caso
      - sí, deriva la conversación
      - sí, pásame con un agente
      - quiero que me pases con soporte
      - sí, continúa con la derivación
      - está bien, deriva a humano

  - intent: nlu_fallback
    examples: |
      - no sé qué decir
      - no estoy seguro
      - no tengo idea
      - no sé qué significa eso
      - no sé, explícame
      - no sé exactamente
      - qué significa eso
      - no estoy seguro qué hacer

  - intent: sugerir_tutor
    examples: |
      - necesito ayuda con algo más complejo
      - no entiendo la explicación
      - no estoy seguro si continuar
      - no me siento conforme con esto
      - me gustaría apoyo adicional

  - intent: detectar_emocion
    examples: |
      - Estoy muy frustrado
      - Me siento confundido
      - Estoy molesto
      - Me siento inseguro
      - Estoy desmotivado
      - Estoy confundido
      - No entiendo nada
      - Estoy frustrado

  - intent: ingreso_zajuna
    examples: |
      - quiero entrar a Zajuna
      - cómo ingreso a Zajuna
      - iniciar sesión en Zajuna
      - quiero iniciar sesión
      - iniciar sesión
      - quiero entrar a la plataforma
      - quiero loguearme
      - cómo inicio sesión
      - acceder a mi cuenta
      - entrar con mi usuario
      - quiero hacer login
      - empezar sesión
      - abrir mi sesión
      - ¿cómo inicio sesión?
      - no sé entrar
      - cómo hago login
      - ver guía de inicio de sesión
      - muéstrame los pasos para iniciar sesión
      - ¿cómo me autentico?
      - ayuda con el login
      - creo que necesito iniciar sesión
      - necesito autenticarme
      - debo iniciar sesión primero
      - antes tengo que loguearme
      - entiendo que debo autenticarme
      - primero debo iniciar sesión

  - intent: ver_tutor_asignado
    examples: |
      - quiero ver mi tutor asignado
      - quién es mi tutor
      - ver tutor asignado

  - intent: menu_administrativo
    examples: |
      - administrativo
      - quiero hacer un trámite administrativo
      - facilitame mi certificado
      - quiero ver arbol administrativo
      - trámites administrativos
      - necesito información administrativa
      - proceso académico
      - procesos administrativos
      - quiero ver mi proceso académico
      - proceso estudiantil
      - trámites académicos
      - ayuda con el proceso académico

  - intent: menu_academico
    examples: |
      - académico
      - tema académico
      - dudas académicas
      - necesito ayuda con el curso
      - ayuda académica
      - tengo dudas de la clase
      - quiero ver el menú académico
      - menú académico
      - abrir sección académica
      - área académica
      - información académica
      - submenú académico
      - menú académico secundario
      - ver submenú de académico
      - abrir submenú académico

  - intent: consultar_contenido_curso
    examples: |
      - quiero ver el contenido del curso
      - qué temas incluye el curso
      - ver contenido académico
      - ver las unidades del curso

  - intent: despedida
    examples: |
      - adiós
      - chao
      - nos vemos al rato
      - nos vemos luego
      - hasta luego
      - nos vemos
      - gracias por tu ayuda
      - gracias, adiós
      - gracias por todo
      - hasta la próxima
      - gracias, chao
      - gracias por la ayuda
      - gracias, nos vemos luego
      - gracias por tu asistencia
      - muy gentil, adiós
      - gracias por tu apoyo
      - nos vemos pronto

  - intent: guardar_estado
    examples: |
      - guardas por favor el progreso
      - guardar estado
      - guarda donde voy

  - intent: pedir_humano
    examples: |
      - quiero hablar con un humano
      - pásame con un asesor
      - necesito una persona de soporte
      - quiero soporte humano
      - hablar con un agente
      - necesito un agente humano
      - contactame con una persona
      - quiero hablar con alguien
      - pasar con un agente humano
      - hablar con un asesor
      - necesito un humano
      - atención humana por favor
      - conéctame con un agente
      - me atiende una persona
      - quiero hablar con un asesor
      - pasar a un humano
      - necesito agente humano
      - deseo derivación a humano
      - necesito hablar con alguien
      - quiero un agente humano
      - pásame con una persona
      - escalar a humano
      - atención personalizada
      - con humano por favor
      - soporte humano
      - necesito un agente
      - atención humana
      - soporte con persona
      - pasar con un humano
      - escalar el caso
      - derivar a humano
      - hablar con humano
      - pásame con soporte humano
      - quiero soporte humano ahora
      - sí, conéctame por favor
      - sí, quiero hablar con humano
      - continuar con agente
      - aceptar derivación
      - sí, pásame con humano
      - por favor con un asesor
      - quiero hablar con un agente
      - sí, con un humano
      - confirmo derivación a humano
      - adelante, escálalo
      - sí, necesito asistencia humana

  - intent: problema_no_resuelto
    examples: |
      - mi problema no se ha resuelto
      - sigue sin funcionar
      - eso no me ayudó
      - problema_resuelto_no
      - no, el problema no se resolvió
      - no se solucionó
      - sigo con el problema
      - no quedó resuelto
      - aún tengo el mismo problema
      - necesito más ayuda

  - intent: negar_handoff
    examples: |
      - no, no quiero hablar con un humano
      - prefiero seguir contigo
      - sigamos con el bot
      - no quiero que me pasen con un humano
      - no quiero derivación
      - no, no me pases con un asesor
      - no necesito un humano
      - mejor sigo con el bot
      - no, no escales el caso
      - quiero continuar aquí
      - no quiero ser derivado
      - no deseo hablar con un agente
      - prefiero continuar contig
      - no, sigo contigo
      - no quiero humano
      - mejor continúo con el bot
      - no conectar con humano
      - cancelar derivación
      - no, así está bien
      - no, no escales
      - no quiero hablar con humano
      - no quiero que me pases con humano
      - no quiero que me pases con un humano

  - intent: enviar_soporte
    examples: |
      - quiero contactar soporte
      - necesito ayuda con el acceso
      - enviar ticket a soporte
      - tengo un problema técnico y deseo reportarlo
      - quiero que crees un ticket de soporte
      - registra mi problema en soporte

  - intent: soporte_tecnico
    examples: |
      - requiero soporte técnico
      - soporte técnico por favor
      - necesito ayuda técnica
      - tengo un problema técnico con la plataforma
      - necesito ayuda del área técnica

  - intent: ver_link_soporte
    examples: |
      - ver enlace de soporte
      - link de soporte
      - ver link de ayuda
      - muéstrame el enlace de soporte
      - ver página de soporte

  - intent: ver_soporte_creado_info
    examples: |
      - ver ticket creado
      - ver confirmación de soporte
      - mostrar ticket de soporte
      - ver el soporte que ya se creó
      - quiero ver el estado del soporte

  - intent: enviar_soporte_directo
    examples: |
      - enviar soporte ahora
      - enviar el ticket de soporte
      - mandar el reporte directo
      - enviar mi solicitud a soporte
      - ya está listo, envíalo a soporte
      - envía el soporte por favor
      - confirmar envío del soporte

  - intent: menu_soporte
    examples: |
      - soporte
      - quiero soporte
      - necesito ayuda de un técnico
      - tengo un problema técnico
      - problemas con la plataforma
      - ayuda con el sistema
      - abrir menú de soporte
      - ver opciones de soporte

  - intent: soporte_acceso
    examples: |
      - no puedo ingresar a zajuna
      - no puedo acceder a la plataforma
      - no me deja entrar
      - tengo problemas de acceso
      - error al iniciar sesión
      - no puedo iniciar sesión en la plataforma
      - mi usuario o contraseña no funcionan
      - la plataforma no da opcion de entrar
      - no logre iniciar sesión
      - no puedo acceder
      - no puedo loguearme
      - no puedo entrar a zajuna
      - no me deja entrar a la plataforma
      - tengo problemas de acceso
      - no puedo ingresar
      - la plataforma no me deja entrar
      - no logro iniciar sesión
      - no pude acceder
      - al entrar me da error
      - no pude loguearme
      - no me deja entrar a mi cuenta
      - no puedo iniciar sesión
      - no logro entrar a la plataforma
      - no supe loguearme

  - intent: soporte_error_plataforma
    examples: |
      - la plataforma está fallando
      - me sale un error en zajuna
      - tengo errores en la plataforma
      - la página no carga bien
      - algo falla en la plataforma
      - me aparece un mensaje de error en zajuna

  - intent: soporte_pqrs
    examples: |
      - quiero hacer una PQRS
      - registrarlo como PQRS
      - quiero un PQRS formal
      - enviar una pqrs
      - quiero registrar una queja formal
      - deseo hacer una petición formal
      - quiero radicar una queja o reclamo

  - intent: soporte_interno
    examples: |
      - solo como mensaje interno
      - mensaje simple a soporte
      - registrar como mensaje interno
      - no hace falta pqrs, solo mensaje
      - solo quiero dejar un mensaje
      - solo para registro interno
      - que quede como mensaje interno nada más

  - intent: aprender_tema
    examples: |
      - Quiero aprender sobre administración de recursos humanos
      - Explícame administración de recursos humanos
      - Enséñame sobre contabilidad
      - Quiero estudiar algo de marketing
      - Quiero aprender un tema académico
      - Explícame un tema del SENA
      - ¿Qué puedo aprender hoy?
      - quiero aprender ciencias administrativas y contables
      - enseñame sobre gerencia de proyectos
      - quiero aprender sobre desarrollo de software
      - enséñame algo de diseño gráfico
      - quiero aprender sobre redes y telecomunicaciones
      - explícamelo todo sobre logística
      - quiero estudiar algo de salud ocupacional
      - enséñame sobre gestión ambiental
      - quiero aprender sobre turismo y hotelería
      - explícamelo todo sobre seguridad industrial
      - quiero aprender sobre electricidad industrial
      - enséñame algo de mecánica automotriz
      - quiero aprender sobre soldadura
      - explícamelo todo sobre gastronomía
      - enseñame algo de agricultura
      - aprender ciencias de la salud
      - quiero aprender sobre gestión de la calidad
      - explícamelo todo sobre mantenimiento industrial
      - enséñame algo de construcción
      - quiero aprender sobre energía renovable
      - explícamelo todo sobre electrónica
      - quiero estudiar algo de administración de empresas
      - enséñame sobre finanzas y contabilidad
      - quiero aprender sobre comercio internacional
      - explícamelo todo sobre marketing digital
      - quiero estudiar algo de desarrollo web
      - enséñame sobre bases de datos
      - quiero aprender sobre ciberseguridad
      - explícamelo todo sobre inteligencia artificial
      - quiero estudiar algo de análisis de datos
      - enséñame sobre gestión de proyectos ágiles
      - quiero aprender sobre diseño UX/UI
      - explícamelo todo sobre cloud computing
      - quiero estudiar algo de internet de las cosas (IoT)
      - enséñame sobre realidad aumentada y virtual
      - quiero aprender sobre blockchain
      - explícamelo todo sobre robótica
      - quiero estudiar algo de impresión 3D
      - enséñame sobre big data
      - quiero aprender sobre machine learning
      - explícamelo todo sobre desarrollo móvil
      - quiero estudiar algo de automatización industrial
      - enséñame sobre energías alternativas
      - consultar de  ciencias de la telematica y la comunicacion
      - quiero aprender sobre gestión de recursos humanos
      - explícamelo todo sobre administración financiera
      - Administración de Recursos Humanos
      - Contabilidad básica
      - Costos y presupuestos
      - Servicio al cliente
      - Emprendimiento
      - desde cero
      - quiero empezar desde cero
      - aprender desde cero
      - quiero aprender [contabilidad](tema)
      - enséñame [marketing](tema)
      - aprender tema
      - quiero estudiar un tema

  - intent: out_of_scope
    examples: |
      - esto no tiene nada que ver
      - hablemos de fútbol
      - cuéntame un chiste
      - tema fuera del curso
      - algo que no es de zajuna
      - quiero hablar de otra cosa que no sea zajuna
      - no quiero hablar de la plataforma
      - esto es irrelevante para zajuna
      - tengo una pregunta fuera del tema

  - intent: solicitar_certificado
    examples: |
      - necesito un certificado
      - instrucciones para descargar mi certificado
      - cómo saco mi certificado del SENA
      - quiero sacar un certificado del sena
      - cómo puedo obtener mi certificado
      - quiero solicitar un certificado
      - quiero generar mi certificado

  - intent: resumir_clase
    examples: |
      - hazme un resumen de la clase
      - resume lo que vimos en la lección
      - dame un resumen del contenido
      - quiero un resumen de la lección
      - haz un resumen de lo aprendido
      - resume los puntos clave de la clase
      - dame un resumen de los temas vistos
      - quiero un resumen del material del curso
      - hazme un resumen del tema estudiado
      - resume lo más importante de la lección
      - dame un resumen del contenido del curso
      - quiero un resumen de lo que aprendí
      - haz un resumen de los conceptos principales
      - resume los aspectos más relevantes de la clase
      - dame un resumen de los puntos principales del tema
      - quiero un resumen de los contenidos vistos
      - hazme un resumen de los temas tratados
      - resume lo esencial de la lección
      - dame un resumen de lo fundamental del curso
      - quiero un resumen de los conocimientos adquiridos 
      - resúmeme la clase
      - haz un resumen de lo que vimos
      - podrías resumir esta explicación
      - resume la sesión anterior
      - haz un resumen del tema
      - dame un resumen de la clase de hoy
      - resúmeme todo lo que explicaste

  - intent: explicar_tema
    examples: |
      - explícamelo otra vez
      - puedes explicarlo de nuevo
      - quiero que me expliques el tema otra vez
      - necesito que me lo expliques otra vez
      - repite la explicación por favor
      - vuelve a explicarme el tema
      - quiero que me lo expliques de nuevo
      - puedes repetir la explicación
      - necesito que me lo expliques de nuevo
      - repite por favor la explicación
      - vuelve a explicarme el tema otra vez
      - explícamelo otra vez por favor
      - puedes explicarlo de nuevo por favor
      - quiero que me expliques el tema otra vez por favor
      - necesito que me lo expliques otra vez por favor
      - repite la explicación por favor
      - vuelve a explicarme el tema por favor

  - intent: consultar_progreso_curso
    examples: |
      - quiero ver mi progreso en el curso
      - ver progreso curso
      - ver avance del curso
      - consultar progreso académico
      - revisar mi progreso en el curso
      - quiero consultar mi avance en el curso
      - ver mi progreso académico
      - cómo está mi avance en el curso
      - revisar progreso del curso
      - quiero ver cómo voy en el curso

  - intent: solicitar_ayuda_tema
    examples: |
      - necesito ayuda con un tema específico
      - quiero ayuda sobre un tema del curso 
      - ayuda con un tema académico
      - necesito apoyo en un tema del curso
      - quiero asistencia con un tema específico
      - ayuda con un tema del curso 
      - necesito ayuda en un tema del curso
      - quiero apoyo sobre un tema académico
      - asistencia con un tema del curso
      - apoyo en un tema específico del curso
      - necesito asistencia con un tema del curso

  - intent: consultar_horarios_clases
    examples: |
      - quiero ver los horarios de mis clases
      - consultar horarios académicos
      - ver horarios de clases
      - revisar mi horario de estudio
      - quiero consultar los horarios de mis clases
      - ver mi horario académico
      - cómo están organizados mis horarios de clase
      - revisar horarios de estudio
      - quiero ver cómo están mis horarios de clase
      - consultar mi horario académico

  - intent: consultar_certificados
    examples: |
      - quiero consultar mis certificados
      - ver mis certificados
      - revisar certificados disponibles
      - consultar certificados emitidos
      - quiero ver mis certificados emitidos
      - revisar mis certificados
      - consultar certificados que tengo
      - quiero ver los certificados que tengo
      - ver mis certificados emitidos
      - deseo consultar mis certificados
      - muéstrame mis certificados
      - consultar certificados
      - ver certificados
      - mis certificados disponibles
      - ¿qué certificados tengo?
      - muéstrame los certificados
      - ver diplomas emitidos
      - necesito mi constancia
      - certificados en PDF
      - ¿dónde descargo mis certificados
      - certificados del curso
      - consultar constancias
      - mostrar certificados
      - revisar certificados
      - revisar mis certificados de estudio
      - ver certificados del SENA
      - consultar certificados del sena
      - ver mis certificados del sena
      - quiero descargar mis certificados
      - necesito descargar mi certificado
      - necesito descargar un certificado de estudio
      - cómo veo mis certificados
      - dónde puedo ver mis certificados
      - quiero ver qué certificados tengo
      - quiero ver los certificados que he obtenido
      - consultar mis certificados de cursos
      - ver certificados de los cursos que hice
      - ver certificados aprobados
      - revisar mis certificados disponibles
      - ver mis certificados en zajuna
      - consultar certificados en zajuna
      - revisar certificados de formación
      - quiero ver mis certificados académicos
      - abrir el listado de certificados
      - muéstrame el listado de certificados
      - ver certificados disponibles
      - listar certificados
      - muéstrame todos mis certificados
      - ver todos los certificados
      - mostrar listado de certificados

  - intent: llm_fallback
    examples: |
      - continúa con lo que estabas explicando
      - sigue con el tema anterior
      - puedes explicarlo mejor
      - no entendí bien, explícamelo otra vez
      - dame más detalle por favor
      - amplía la explicación
      - quiero que sigas explicando
      - cuéntame más sobre eso
      - continúa la explicación
      - sigue con la clase

  - intent: informar_historial_academico
    examples: |
      - quiero ver mi historial académico
      - consultar historial académico
      - ver mis calificaciones anteriores
      - revisar mi historial de cursos
      - quiero consultar mi historial académico
      - ver mis notas anteriores
      - cómo está mi historial académico
      - revisar historial de cursos
      - quiero ver cómo he avanzado académicamente
      - consultar mis calificaciones anteriores

  - intent: enviar_url
    examples: |
      - revisa [https://zajuna.edu](url)
      - te paso el enlace [http://example.com/recurso](url)

  - intent: encuesta_valor_explicacion_si
    examples: |
      - sí, me sirvió
      - si fue útil
      - sí me ayudó
      - me fue útil
      - la explicación fue clara
      - me ayudó bastante
      - entendí bien el tema

  - intent: encuesta_explicacion_si
    examples: |
      - sí, me ayudó
      - si me sirvió
      - sí, me fue útil
      - sí, entendí
      - sí, estuvo claro
      - sí, la explicación está bien

  - intent: encuesta_explicacion_no
    examples: |
      - no me ayudó
      - no entendí
      - no, no fue clara
      - no me quedó bien claro
      - no me sirvió mucho
      - no, sigue confuso
      
  - intent: mis_cursos
    examples: |
      - ver mis cursos
      - mostrar mis cursos
      - mis contenidos
      - quiero ver los cursos que tengo

  - intent: reanudar_mas_tarde
    examples: |
      - luego sigo
      - quiero reanudar más tarde
      - después continúo
      - más tarde sigo con el tema

  - intent: no_encuesta_general
    examples: |
      - no quiero responder la encuesta
      - no, responderé luego
      - luego respondo la encuesta
      - no deseo contestar la encuesta
      - no quiero hacer la encuesta ahora

  - intent: encuesta_nivel_general
    examples: |
      - 1
      - 2
      - 3
      - 4
      - 5
      - la califico con 1
      - la califico con 2
      - la califico con 3
      - la califico con 4
      - la califico con 5
      - mi calificación es 1
      - mi calificación es 2
      - mi calificación es 3
      - mi calificación es 4
      - mi calificación es 5
