import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { http, responseMessage, verify_turnstile_api } from "../src/api";
import { hasTurnstileSession, parseTurnstileEnabled, rememberTurnstileSession } from "../src/turnstile";

beforeEach(() => sessionStorage.clear());
afterEach(() => vi.restoreAllMocks());

describe("verify_turnstile_api", () => {
    it("posts the token as a form field", async () => {
        const post = vi.spyOn(http, "post").mockResolvedValue({ data: { success: true } } as any);

        await expect(verify_turnstile_api("token value")).resolves.toEqual({ success: true });

        expect(post).toHaveBeenCalledTimes(1);
        const [url, payload] = post.mock.calls[0];
        expect(url).toBe("/turnstile");
        expect(payload).toBeInstanceOf(URLSearchParams);
        expect((payload as URLSearchParams).get("turnstile_token")).toBe("token value");
    });
});

describe("responseMessage", () => {
    it("prefers the backend's error detail", () => {
        expect(responseMessage({ isAxiosError: true, response: { data: { detail: "Verification failed." } } })).toBe(
            "Verification failed.",
        );
    });
});

describe("Turnstile mode", () => {
    it("is disabled in development and enabled in production by default", () => {
        expect(parseTurnstileEnabled(undefined, false)).toBe(false);
        expect(parseTurnstileEnabled(undefined, true)).toBe(true);
    });

    it("honours an explicit override", () => {
        expect(parseTurnstileEnabled("true", false)).toBe(true);
        expect(parseTurnstileEnabled("1", false)).toBe(true);
        expect(parseTurnstileEnabled("false", true)).toBe(false);
        expect(parseTurnstileEnabled("0", true)).toBe(false);
    });
});

describe("Turnstile session", () => {
    it("remembers a successful verification", () => {
        expect(hasTurnstileSession()).toBe(false);

        rememberTurnstileSession();

        expect(hasTurnstileSession()).toBe(true);
    });

    it("expires remembered verifications", () => {
        rememberTurnstileSession();

        const key = sessionStorage.key(0)!;
        const session = JSON.parse(sessionStorage.getItem(key)!);
        session.verifiedAt = Date.now() - 31 * 60 * 1000;
        sessionStorage.setItem(key, JSON.stringify(session));

        expect(hasTurnstileSession()).toBe(false);
    });
});
