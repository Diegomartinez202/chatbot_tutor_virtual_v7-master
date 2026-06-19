module.exports = {
    root: true,
    env: {
        browser: true,
        es2021: true,
    },
    extends: [
        "eslint:recommended",
        "plugin:react/recommended",
        "prettier" // 👈 Desactiva reglas que interfieren con Prettier
    ],
    parserOptions: {
        ecmaVersion: 2021,
        sourceType: "module",
        ecmaFeatures: {
            jsx: true
        }
    },
    plugins: ["react", "react-hooks"],
    rules: {
        "react/react-in-jsx-scope": "off", // ✅ Si usas React 17+
    },
    settings: {
        react: {
            version: "detect",
        },
    },
};