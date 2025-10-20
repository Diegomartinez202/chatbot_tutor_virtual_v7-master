/* eslint-disable no-console */
const required = ["PLAYWRIGHT_BASE_URL"];
const missing = required.filter((k) => !process.env[k]);

if (missing.length) {
    console.error(`❌ Faltan variables requeridas: ${missing.join(", ")}`);
    process.exit(1);
}

const anyLogin =
    process.env.PLAYWRIGHT_LOGIN_PATH ||
    process.env.PLAYWRIGHT_LOGIN_USER ||
    process.env.PLAYWRIGHT_LOGIN_PASS;

if (anyLogin) {
    const trio = ["PLAYWRIGHT_LOGIN_PATH", "PLAYWRIGHT_LOGIN_USER", "PLAYWRIGHT_LOGIN_PASS"];
    const missLogin = trio.filter((k) => !process.env[k]);
    if (missLogin.length) {
        console.error(
            `❌ Faltan variables de login: ${missLogin.join(", ")} (cuando se usa login, deben estar las 3)`
        );
        process.exit(1);
    }
}

console.log("✅ Variables de entorno OK para screenshots:prod");