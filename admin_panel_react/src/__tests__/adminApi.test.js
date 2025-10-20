import { rest } from "msw";
import { server } from "@/test/mocks/server";
import axiosClient from "@/services/axiosClient";

// mock explícito del storage de tokens
jest.mock("../tokenStorage", () => ({
    setToken: jest.fn(),
    setRefreshToken: jest.fn(),
    clearToken: jest.fn(),
}));

import { setToken, setRefreshToken } from "../tokenStorage";
import { login, clearAuthToken } from "../authApi";

describe("authApi.login", () => {
    beforeAll(() => {
        // asegúrate que axios tenga baseURL durante tests
        axiosClient.defaults.baseURL = "http://localhost:8000";
    });

    afterEach(() => {
        clearAuthToken(); // limpia Authorization entre tests
        jest.clearAllMocks();
    });

    test("setea Authorization y guarda tokens", async () => {
        // Mock del endpoint prioritario /auth/login
        server.use(
            rest.post("http://localhost:8000/auth/login", async (req, res, ctx) => {
                return res(
                    ctx.status(200),
                    ctx.json({
                        access_token: "JWT_TEST",
                        refresh_token: "REFRESH_TEST",
                        user: { id: "u1", email: "email@test.com" },
                    }),
                );
            }),
        );

        const result = await login({ email: "email@test.com", password: "123" });
        expect(result.token).toBe("JWT_TEST");
        expect(result.refresh_token).toBe("REFRESH_TEST");

        // setToken / setRefreshToken fueron llamados
        expect(setToken).toHaveBeenCalledWith("JWT_TEST");
        expect(setRefreshToken).toHaveBeenCalledWith("REFRESH_TEST");

        // header Authorization aplicado
        expect(axiosClient.defaults.headers.common.Authorization).toBe("Bearer JWT_TEST");
    });
});