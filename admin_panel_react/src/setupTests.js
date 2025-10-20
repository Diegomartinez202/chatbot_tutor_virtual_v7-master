import { server } from "./test/mocks/server";

// Falla si se hace una request no mockeada (nos ayuda a detectar rutas mal puestas)
beforeAll(() => server.listen({ onUnhandledRequest: "error" }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());