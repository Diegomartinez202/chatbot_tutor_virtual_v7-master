module.exports = {
    testEnvironment: "node",
    setupFilesAfterEnv: ["<rootDir>/src/setupTests.js"],
    moduleNameMapper: {
        "^@/(.*)$": "<rootDir>/src/$1",
    },
    transform: {
        "^.+\\.[jt]sx?$": "babel-jest",
    },
};