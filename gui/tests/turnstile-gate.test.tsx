import { cleanup, fireEvent, render, screen, waitFor } from "@solidjs/testing-library";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { verify_turnstile_api } from "../src/api";
import TurnstileGate from "../src/Turnstile";
import { loadTurnstile, TURNSTILE_SITE_KEY } from "../src/turnstile";

vi.mock("../src/api", async (importOriginal) => {
    const actual = await importOriginal<typeof import("../src/api")>();
    return { ...actual, verify_turnstile_api: vi.fn() };
});

vi.mock("../src/turnstile", async (importOriginal) => {
    const actual = await importOriginal<typeof import("../src/turnstile")>();
    return { ...actual, loadTurnstile: vi.fn() };
});

const verify = vi.mocked(verify_turnstile_api);
const load = vi.mocked(loadTurnstile);

const setup = (unlock: () => void) => render(() => <TurnstileGate onVerified={unlock} />);

const mockWidget = (token: string) => {
    const renderWidget = vi.fn((_container: HTMLElement, options: { callback: (token: string) => void }) => {
        queueMicrotask(() => options.callback(token));
        return "widget-id";
    });

    load.mockResolvedValue({ render: renderWidget, reset: vi.fn(), remove: vi.fn() });
    return renderWidget;
};

beforeEach(() => {
    sessionStorage.clear();
    verify.mockReset();
    load.mockReset();
});

afterEach(() => cleanup());

describe("TurnstileGate", () => {
    it("unlocks the app after the backend accepts the token", async () => {
        const unlock = vi.fn();
        const renderWidget = mockWidget("token");
        verify.mockResolvedValue({ success: true });

        setup(unlock);

        await waitFor(() => expect(verify).toHaveBeenCalledWith("token"));
        await waitFor(() => expect(unlock).toHaveBeenCalledTimes(1));

        expect(renderWidget).toHaveBeenCalledWith(expect.any(HTMLElement), expect.objectContaining({ sitekey: TURNSTILE_SITE_KEY }));
    });

    it("reports backend failures without bypassing verification", async () => {
        const unlock = vi.fn();
        mockWidget("token");
        verify.mockRejectedValue({
            isAxiosError: true,
            response: { status: 500, data: { detail: "Unable to validate the token." } },
        });

        setup(unlock);

        await screen.findByText("Unable to validate the token.");
        expect(unlock).not.toHaveBeenCalled();
        expect(screen.queryByText("Continue without verification")).toBeNull();

        fireEvent.click(screen.getByText("Try again"));
        expect(unlock).not.toHaveBeenCalled();
    });

    it("reports rejected tokens and allows another attempt", async () => {
        const unlock = vi.fn();
        const renderWidget = mockWidget("token");
        verify.mockResolvedValue({ success: false, errors: ["invalid-input-response"] });

        setup(unlock);

        await screen.findByText(/Verification failed \(invalid-input-response\)/i);
        expect(unlock).not.toHaveBeenCalled();

        fireEvent.click(screen.getByText("Try again"));

        expect(renderWidget).toHaveBeenCalledTimes(1);
    });
});
