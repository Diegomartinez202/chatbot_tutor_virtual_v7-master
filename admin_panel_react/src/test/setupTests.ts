///src/test/setupTests.ts
import "@testing-library/jest-dom";
import { afterEach } from "vitest";
import { cleanup } from "@testing-library/react";

// Limpia el DOM entre tests
afterEach(() => {
    cleanup();
});

// (Opcional) polyfills si los necesitas
// global.matchMedia = global.matchMedia || (() => ({ matches: false, addListener: () => {}, removeListener: () => {} }));

