// assets.js

// ---------------------------
// Helpers de base/abs
// ---------------------------
const getBaseUrl = () => {
  try {
    const baseEnv = import.meta.env?.BASE_URL || "/";
    return String(baseEnv).replace(/\/+$/, "/");
  } catch {
    const origin = window.location.origin;
    const baseTag = document.querySelector("base")?.getAttribute("href") || "/";
    return new URL(baseTag, origin).href.replace(/\/+$/, "/");
  }
};

const BASE = getBaseUrl();

/**
 * Si path es absoluto (empieza con "/" o "http(s)://"), NO lo toca.
 * Si es relativo, lo resuelve respecto a BASE.
 */
const abs = (path) => {
  if (!path) return path;
  const p = String(path);
  if (/^(?:https?:)?\/\//i.test(p)) return p; // http(s):// o //cdn
  if (p.startsWith("/")) return p;            // absoluto dentro del host
  const cleanPath = p.replace(/^\/+/, "");
  try {
    return `${BASE}${cleanPath}`;
  } catch {
    console.warn(`Ruta inválida: ${path}`);
    return cleanPath;
  }
};

/** Normaliza rutas de .env o constantes */
const normalizeAssetPath = (p, fallback = "") => {
  const s = (p ?? "").toString().trim();
  if (!s) return fallback;
  // si ya es absoluta o URL, respetar
  if (/^(?:https?:)?\/\//i.test(s) || s.startsWith("/")) return s;
  // si viene relativo, pásalo por abs() (respeta BASE del build Vite)
  return abs(s);
};

// ---------------------------
// Variables de entorno (alineadas con tu Nginx)
// ---------------------------
// En tu .env:
//   VITE_BOT_AVATAR=/bot-avatar.png
//   VITE_BOT_LOADING=/bot-loading.png
const ENV_BOT_AVATAR  = normalizeAssetPath(import.meta?.env?.VITE_BOT_AVATAR,  "/bot-avatar.png");
const ENV_BOT_LOADING = normalizeAssetPath(import.meta?.env?.VITE_BOT_LOADING, "/bot-loading.png");

// ---------------------------
// API pública previa (conservada)
// ---------------------------
const assets = {
  // Usar primero .env, si no hay, cae en raíz
  BOT_AVATAR: ENV_BOT_AVATAR,
  BOT_LOADING: ENV_BOT_LOADING,
  USER_AVATAR: abs("favicon-32x32.png"),
};

// ---------------------------
// Densidad / srcset helpers (conservados)
// ---------------------------
const getDpr = () => {
  try {
    return Math.min(3, Math.max(1, Math.round(window.devicePixelRatio || 1)));
  } catch {
    return 1;
  }
};

const makeSrcSetPNG = (basename, { include3x = true } = {}) => {
  const oneX = abs(`${basename}.png`);
  const twoX = abs(`${basename}@2x.png`);
  const threeX = abs(`${basename}@3x.png`);
  return include3x ? `${oneX} 1x, ${twoX} 2x, ${threeX} 3x` : `${oneX} 1x, ${twoX} 2x`;
};

const pictureSources = (basename, { includePNG2x3x = true } = {}) => {
  const svg = abs(`${basename}.svg`);
  const png1x = abs(`${basename}.png`);
  const srcset = includePNG2x3x ? makeSrcSetPNG(basename) : `${png1x} 1x`;
  return [
    { type: "image/svg+xml", srcSet: svg },
    { type: "image/png", srcSet: srcset },
  ];
};

const densify = (path /* con .png */, { dpr = getDpr() } = {}) => {
  if (!/\.png(\?|#|$)/i.test(path)) return path;
  const dot = path.lastIndexOf(".");
  if (dot <= 0) return path;
  const base = path.slice(0, dot);
  const ext = path.slice(dot);
  if (dpr >= 3) return `${base}@3x${ext}`;
  if (dpr >= 2) return `${base}@2x${ext}`;
  return path;
};

const preloadImageWithFallback = (urls = []) =>
  new Promise((resolve, reject) => {
    if (!urls.length) return reject(new Error("No URLs"));
    let idx = 0;
    const tryNext = () => {
      if (idx >= urls.length) return reject(new Error("All fallbacks failed"));
      const url = urls[idx++];
      const img = new Image();
      img.onload = () => resolve(url);
      img.onerror = tryNext;
      img.src = url;
    };
    tryNext();
  });

const preloadAssets = async (urls = []) => {
  await Promise.allSettled(
    urls.map(
      (u) =>
        new Promise((res) => {
          const img = new Image();
          img.onload = img.onerror = () => res(true);
          img.src = u;
        })
    )
  );
};

// ---------------------------
// Builders (conservados) – ahora respetan env/absolutos
// ---------------------------
const buildAssetSet = (
  basename,
  {
    preferSVG = true,
    includePNG2x3x = true,
  } = {}
) => {
  const png1x = abs(`${basename}.png`);
  const src = preferSVG ? abs(`${basename}.svg`) : densify(png1x);
  const srcSet = includePNG2x3x ? makeSrcSetPNG(basename) : undefined;
  const sources = pictureSources(basename, { includePNG2x3x });
  return { src, srcSet, sources, png1x };
};

const buildBotAvatarSet = () => {
  // si .env trae absoluto, respétalo
  if (ENV_BOT_AVATAR.startsWith("/") || /^(?:https?:)?\/\//i.test(ENV_BOT_AVATAR)) {
    return { src: ENV_BOT_AVATAR, png1x: ENV_BOT_AVATAR, sources: [], srcSet: undefined };
  }
  return buildAssetSet("bot-avatar");
};

const buildBotLoadingSet = () => {
  if (ENV_BOT_LOADING.startsWith("/") || /^(?:https?:)?\/\//i.test(ENV_BOT_LOADING)) {
    return { src: ENV_BOT_LOADING, png1x: ENV_BOT_LOADING, sources: [], srcSet: undefined };
  }
  return buildAssetSet("bot-loading");
};

const buildUserAvatarSet = () => buildAssetSet("favicon-32x32"); // ejemplo

// ---------------------------
// smartPick con fallbacks /embed (alineado a tu nginx)
// ---------------------------
const smartPick = async (basename /* sin ext */) => {
  // Si el basename viene con leading slash o URL, pruébalo tal cual
  if (basename.startsWith("/") || /^(?:https?:)?\/\//i.test(basename)) {
    const only = [basename];
    try {
      const ok = await preloadImageWithFallback(only);
      return ok;
    } catch {
      return only[0];
    }
  }

  // Caso típico: "bot-avatar" o "bot-loading"
  const svgRoot   = normalizeAssetPath(`/${basename}.svg`);
  const png1Root  = normalizeAssetPath(`/${basename}.png`);
  const png2Root  = normalizeAssetPath(`/${basename}@2x.png`);
  const png3Root  = normalizeAssetPath(`/${basename}@3x.png`);

  const svgEmbed  = normalizeAssetPath(`/embed/${basename}.svg`);
  const png1Embed = normalizeAssetPath(`/embed/${basename}.png`);
  const png2Embed = normalizeAssetPath(`/embed/${basename}@2x.png`);
  const png3Embed = normalizeAssetPath(`/embed/${basename}@3x.png`);

  // Orden: preferimos raíz, luego /embed (o al revés, según prefieras)
  const candidates = [svgRoot, png3Root, png2Root, png1Root, svgEmbed, png3Embed, png2Embed, png1Embed];

  try {
    const ok = await preloadImageWithFallback(candidates);
    return ok;
  } catch {
    // último recurso: raíz 1x
    return png1Root;
  }
};

// ---------------------------
// Exports
// ---------------------------
export default assets;
export {
  abs,
  BASE,
  // helpers
  getDpr,
  makeSrcSetPNG,
  pictureSources,
  densify,
  preloadAssets,
  preloadImageWithFallback,
  buildAssetSet,
  buildBotAvatarSet,
  buildBotLoadingSet,
  buildUserAvatarSet,
  smartPick,
};
