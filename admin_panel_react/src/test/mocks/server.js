import { setupServer } from "msw/node";

// Arrancamos el server sin handlers globales;
// cada test define sus handlers con server.use(...)
export const server = setupServer();