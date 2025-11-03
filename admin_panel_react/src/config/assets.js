// assets.js

const getBaseUrl = () => {
    try {
        const baseEnv = import.meta.env?.BASE_URL || "/";
        return baseEnv.replace(/\/+$/, "/"); 
    } catch {
      
        const origin = window.location.origin;
        const baseTag = document.querySelector("base")?.getAttribute("href") || "/";
        return new URL(baseTag, origin).href.replace(/\/+$/, "/");
    }
};

const BASE = getBaseUrl();

const abs = (path) => {
    const cleanPath = path.replace(/^\/+/, ""); 
    try {
        return `${BASE}${cleanPath}`;
    } catch {
        console.warn(`Ruta inválida: ${path}`);
        return cleanPath;
    }
};

const assets = {
    BOT_AVATAR: abs("bot-avatar.png"),
    BOT_LOADING: abs("bot-loading.png"),
    USER_AVATAR: abs("favicon-32x32.png"),
};

const getDpr = () => {
    try { return Math.min(3, Math.max(1, Math.round(window.devicePixelRatio || 1))); }
    catch { return 1; }
};

const makeSrcSetPNG = (basename , { include3x = true } = {}) => {
    const oneX = abs(`${basename}.png`);
    const twoX = abs(`${basename}@2x.png`);
    const threeX = abs(`${basename}@3x.png`);
    return include3x ? `${oneX} 1x, ${twoX} 2x, ${threeX} 3x` : `${oneX} 1x, ${twoX} 2x`;
};

const pictureSources = (basename , { includePNG2x3x = true } = {}) => {
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

const preloadImageWithFallback = (urls = []) => new Promise((resolve, reject) => {
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
        urls.map((u) => new Promise((res) => {
            const img = new Image();
            img.onload = img.onerror = () => res(true);
            img.src = u;
        }))
    );
};

const buildAssetSet = (basename , {
    preferSVG = true,
    includePNG2x3x = true,
} = {}) => {
    const png1x = abs(`${basename}.png`);
    const src = preferSVG ? abs(`${basename}.svg`) : densify(png1x);
    const srcSet = includePNG2x3x ? makeSrcSetPNG(basename) : undefined;
    const sources = pictureSources(basename, { includePNG2x3x });
    return { src, srcSet, sources, png1x };
};

const buildBotAvatarSet = () => buildAssetSet("bot-avatar");
const buildBotLoadingSet = () => buildAssetSet("bot-loading");
const buildUserAvatarSet = () => buildAssetSet("favicon-32x32"); // ejemplo

const smartPick = async (basename /* sin ext */) => {
    const svg = abs(`${basename}.svg`);
    const png1 = abs(`${basename}.png`);
    const png2 = abs(`${basename}@2x.png`);
    const png3 = abs(`${basename}@3x.png`);
    // orden de prueba
    const candidates = [svg, png3, png2, png1];
    try {
        const ok = await preloadImageWithFallback(candidates);
        return ok;
    } catch {
        return png1; 
    }
};

export default assets;
export {
    abs,
    BASE,
    // helpers nuevos
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
