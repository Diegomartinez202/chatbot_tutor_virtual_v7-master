# Chatbot Tutor Virtual v7

Este proyecto implementa un chatbot tutor virtual con interacción en tiempo real, utilizando **React** para el frontend y **Rasa** para el backend.

---

## 📝 Estructura de Componentes

### Flujo de interacción

1. **Usuario envía mensaje**  
   El usuario escribe su consulta en el chat.

2. **ChatPage**  
   Página principal que contiene el chat.

3. **ChatUI**  
   Componente que maneja la interfaz del chat, renderizando mensajes.

4. **Hooks**  
   - `useAuth`: Maneja autenticación del usuario.  
   - `useAvatarPreload`: Pre-carga avatares para mejorar UX.  
   - `useChatSettingsListener`: Escucha cambios en la configuración del chat.  
   - `useTrainBot`: Permite entrenar el bot con nuevas respuestas.  
   - `useUploadIntents`: Subida de intenciones para el entrenamiento del bot.

5. **API Rasa Backend**  
   El backend procesa la intención y genera la respuesta del bot.

6. **Respuesta del bot**  
   El mensaje generado se envía al ChatUI y se muestra al usuario.

---

## 🚀 Levantamiento de Perfiles

Para iniciar los contenedores de Docker de cada perfil:

```bash
# Backend
docker run -d -p 8010:8000 --name chatbot_backend_container chatbot_backend

# Frontend
docker run -d -p 3000:3000 --name chatbot_frontend_container chatbot_frontend

🔗 Tecnologías utilizadas

React.js

Rasa NLU

Docker

Axios (API requests)

CSS moderno con estilos responsivos

Chatbot Tutor Virtual — Hooks y Componentes de Conexión

Este documento describe los hooks y componentes principales para la conexión y manejo de mensajes del chat en el proyecto chatbot_tutor_virtual_v7.

📂 Estructura de Hooks
1. useAuth

Ruta: src/hooks/useAuth.js

Descripción: Hook para validar el token JWT y obtener información del usuario autenticado.

Funcionalidad:

Extrae el token del localStorage.

Decodifica el JWT y verifica expiración.

Retorna un objeto con:

{
  isAuthenticated: boolean,
  expired: boolean,
  user: { email, rol } | undefined,
  token: string | undefined
}


Uso:

import { useAuth } from '@/hooks/useAuth';
const { isAuthenticated, user } = useAuth();

2. useAvatarPreload

Ruta: src/hooks/useAvatar.js

Descripción: Hook para precargar imágenes de avatar y evitar flickering.

Uso:

import { useAvatarPreload } from '@/hooks/useAvatar';
useAvatarPreload('/ruta/a/avatar.png');

3. useChatSettingsListener

Ruta: src/hooks/useChatSettingsListener.js

Descripción: Hook para escuchar cambios de configuración de chat desde un iframe o ventana padre.

Eventos manejados: theme, contrast, lang

Uso:

import useChatSettingsListener from '@/hooks/useChatSettingsListener';

useChatSettingsListener({
  onTheme: (theme) => setTheme(theme),
  onContrast: (contrast) => setContrast(contrast),
  onLang: (lang) => setLang(lang)
});

4. useTrainBot

Ruta: src/hooks/useTrainBot.js

Descripción: Hook para disparar entrenamiento del bot vía API.

Uso:

import { useTrainBot } from '@/hooks/useTrainBot';
const mutation = useTrainBot();
mutation.mutate();

5. useUploadIntents

Ruta: src/hooks/useUploadIntents.js

Descripción: Hook para subir intents al bot vía API.

Uso:

import { useUploadIntents } from '@/hooks/useUploadIntents';
const mutation = useUploadIntents();
mutation.mutate();

📂 Componentes Principales de Chat
1. ChatUI

Ruta: src/components/chat/ChatUI.jsx

Descripción: Componente principal del UI del chat.

Funcionalidades:

Muestra mensajes de usuario y bot con avatares.

Soporta mensajes de texto, imágenes, botones, tarjetas y quick replies.

Integración con Rasa REST y envío de mensajes.

Indicador de escritura “typing…”.

Control de acciones rápidas (QuickActions) y validación de origen seguro.

Integración con micrófono (MicButton) y envío de mensajes por Enter.

Props principales:

{
  embed?: boolean,
  placeholder?: string
}

2. ChatPage

Ruta: src/pages/ChatPage.jsx

Descripción: Página completa de chat que envuelve ChatUI.

Funcionalidades:

Health check de conexión con Rasa (REST o WS).

Control de acceso según autenticación.

Flag para modo embed.

Manejo de estado: connecting | ready | error.

Soporte para pasar un connectFn personalizado.

Props principales:

{
  forceEmbed?: boolean,
  avatarSrc?: string,
  title?: string,
  connectFn?: () => Promise<void>,
  embedHeight?: string,
  children?: ReactNode
}

🛠 Servicios Relacionados

connectRasaRest: función para enviar mensajes a Rasa vía REST.

connectWS: función opcional para WebSocket.

connectChatHealth: health check universal REST/WS.

📝 Notas Importantes

Los avatares tienen fallback automático en caso de error.

Las acciones rápidas y botones deshabilitan el grupo una vez clickeados para evitar duplicados.

El hook useChatSettingsListener permite sincronizar tema, contraste y lenguaje desde un host externo.

ChatPage maneja flags de QA (Harness) y soporte de embed de manera flexible.

Todos los hooks que usan @tanstack/react-query (useTrainBot y useUploadIntents) manejan onError y loguean errores.


Chatbot Tutor Virtual — Flujo de Hooks y Componentes
┌─────────────────────┐
│  Usuario / Frontend │
└─────────┬───────────┘
          │
          ▼
   ┌──────────────┐
   │  ChatPage    │
   │ (wrapper UI) │
   └─────┬────────┘
         │
         │ Props: avatarSrc, title, embedHeight
         │ Flags: forceEmbed
         ▼
   ┌──────────────┐
   │  ChatUI      │
   │ (component)  │
   └─────┬────────┘
         │
         │ Renderiza:
         │ - Mensajes (User / Bot)
         │ - Avatares
         │ - QuickActions / Buttons
         │ - MicButton
         ▼
┌───────────────────────────┐
│   Hooks usados en ChatUI  │
└─────────┬─────────────────┘
          │
          │
 ┌────────┴────────┐   ┌──────────────┐
 │ useAuth          │   │ useAvatarPre │
 │ - Verifica token │   │ - Preload    │
 │ - Retorna user   │   │   imágenes   │
 └────────┬────────┘   └───────┬──────┘
          │                    │
          ▼                    ▼
   ┌───────────────┐    ┌──────────────┐
   │ useChatSet    │    │ useTrainBot  │
   │ SettingsList  │    │ - Entrena bot│
   │ - Escucha     │    │   con API    │
   │   theme/lang  │    └───────┬──────┘
   └───────┬───────┘            │
           ▼                    ▼
   ┌───────────────┐    ┌──────────────┐
   │ useUploadInt  │    │ connectRasa  │
   │ - Subir Intents│    │ - REST API  │
   └───────┬───────┘    │ - Envia msg │
           ▼             └─────────────┘
    ┌──────────────┐
    │ Rasa Backend │
    │ - Procesa    │
    │   mensajes   │
    │ - Responde   │
    └───────┬──────┘
            │
            ▼
    ┌──────────────┐
    │ Respuesta Bot│
    │ (Texto / UI) │
    └──────────────┘
            │
            ▼
     Usuario recibe respuesta

🔹 Explicación rápida del flujo

Usuario envía mensaje desde la interfaz (ChatUI dentro de ChatPage).

ChatUI usa hooks:

useAuth → controla autenticación.

useAvatarPreload → evita parpadeos de imagen.

useChatSettingsListener → sincroniza tema, idioma y contraste desde host.

useTrainBot y useUploadIntents → envían cambios de entrenamiento al backend.

ChatUI conecta con Rasa vía connectRasaRest (o WebSocket si aplica).

Rasa Backend procesa el mensaje y devuelve respuesta.

ChatUI renderiza la respuesta con mensajes, avatares y botones interactivos.



🧭 Flujos de acceso del sistema
🔐 1️⃣ Acceso mediante Zajuna SSO
[Usuario] 
   │
   │ Hace clic en "Ingresar con Zajuna"
   ▼
[LoginPage.jsx]
   │
   │ └── Llama a redirectToZajunaSSO() desde AuthContext
   ▼
[AuthContext.jsx]
   │
   │ └── Redirige a la URL definida en .env:
   │      VITE_ZAJUNA_SSO_URL=https://sso.zajuna.com/login
   ▼
[Proveedor Zajuna]
   │
   │ └── Usuario se autentica con sus credenciales institucionales
   │      y Zajuna redirige de vuelta a:
   │      → https://tuapp.com/auth/callback?access_token=XYZ
   ▼
[AuthCallback.jsx]
   │
   │ ├─ Extrae el token del URL
   │ ├─ Guarda token en localStorage y AuthContext
   │ ├─ Llama a apiMe() para obtener el rol del usuario
   │ └─ Redirige según el rol:
   │       - admin/soporte → /dashboard
   │       - usuario → /chat
   ▼
[Sistema interno]
   │
   └── Sesión activa, navegación permitida con token válido

🧩 2️⃣ Acceso como invitado (sin registro)
[Usuario]
   │
   │ Hace clic en "Entrar como invitado (sin registro)"
   ▼
[LoginPage.jsx]
   │
   │ └── Ejecuta handleGuest() → navigate("/chat")
   ▼
[ChatPage.jsx]
   │
   │ └── Carga vista del chat sin token ni autenticación
   │      (modo lectura o uso básico según permisos)
   ▼
[Sistema interno]
   │
   └── Usuario invitado con acceso limitado

⚙️ Variables de entorno involucradas (.env)
# URL del proveedor SSO Zajuna
VITE_ZAJUNA_SSO_URL=https://sso.zajuna.com/login

# Habilita el inicio local con usuario/contraseña (true/false)
VITE_ENABLE_LOCAL_LOGIN=false

# Muestra u oculta el botón de invitado (true/false)
VITE_SHOW_GUEST=true

🧠 Resumen funcional
Modo de acceso	Componente principal	Redirección final	Autenticación	Variables de entorno
🔵 Zajuna SSO	LoginPage → AuthCallback	/chat o /dashboard	OAuth / SSO externo	VITE_ZAJUNA_SSO_URL
🟢 Invitado	LoginPage	/chat	No requiere token	VITE_SHOW_GUEST