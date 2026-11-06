//  Copyright (C) 2022-2026 Theodore Chang
//
//  This program is free software: you can redistribute it and/or modify
//  it under the terms of the GNU General Public License as published by
//  the Free Software Foundation, either version 3 of the License, or
//  (at your option) any later version.

export const TURNSTILE_SCRIPT_URL = "https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit";

/**
 * Parse the optional Turnstile switch, falling back to the current Vite mode.
 * Development builds skip verification by default; production builds require it.
 */
export function parseTurnstileEnabled(value: string | undefined, production: boolean): boolean {
    const flag = value?.trim().toLowerCase();
    if (flag === "true" || flag === "1") return true;
    if (flag === "false" || flag === "0") return false;
    return production;
}

export const TURNSTILE_ENABLED = parseTurnstileEnabled(import.meta.env.VITE_TURNSTILE_ENABLED, import.meta.env.PROD);

/**
 * Public Turnstile site key for the Motion Base deployment. Override it with VITE_TURNSTILE_SITE_KEY when self-hosting.
 *
 * @see https://developers.cloudflare.com/turnstile/get-started/client-side-rendering/
 */
export const TURNSTILE_SITE_KEY = (import.meta.env.VITE_TURNSTILE_SITE_KEY ?? "").trim() || "0x4AAAAAACDz9riiGytnlsJR";

const SESSION_KEY = "mb-turnstile-verified";
const SESSION_TTL = 30 * 60 * 1000;

export interface TurnstileOptions {
    sitekey: string;
    theme?: "auto" | "light" | "dark";
    language?: string;
    size?: "normal" | "compact" | "flexible";
    callback: (token: string) => void;
    "error-callback"?: (code?: string) => void;
    "expired-callback"?: () => void;
    "timeout-callback"?: () => void;
}

export interface TurnstileApi {
    render: (container: HTMLElement, options: TurnstileOptions) => string;
    reset: (widgetId?: string) => void;
    remove: (widgetId: string) => void;
}

declare global {
    interface Window {
        turnstile?: TurnstileApi;
    }
}

let loader: Promise<TurnstileApi> | undefined;

/** Load and initialise the Turnstile script once, reusing it for later gate mounts. */
export function loadTurnstile(): Promise<TurnstileApi> {
    if (typeof window === "undefined") return Promise.reject(new Error("Cloudflare Turnstile requires a browser."));
    if (window.turnstile) return Promise.resolve(window.turnstile);
    if (loader) return loader;

    const promise = new Promise<TurnstileApi>((resolve, reject) => {
        const existing = document.querySelector<HTMLScriptElement>(`script[data-turnstile="true"]`);
        const script = existing ?? document.createElement("script");

        const succeed = () => {
            if (window.turnstile) resolve(window.turnstile);
            else reject(new Error("Cloudflare Turnstile did not initialise."));
        };
        const fail = () => reject(new Error("Unable to load Cloudflare Turnstile."));

        script.addEventListener("load", succeed, { once: true });
        script.addEventListener("error", fail, { once: true });

        if (!existing) {
            script.src = TURNSTILE_SCRIPT_URL;
            script.async = true;
            script.defer = true;
            script.dataset.turnstile = "true";
            document.head.appendChild(script);
        }
    });

    loader = promise.catch((error) => {
        loader = undefined;
        throw error;
    });

    return loader;
}

export function hasTurnstileSession(): boolean {
    if (typeof window === "undefined") return false;

    try {
        const stored = window.sessionStorage.getItem(SESSION_KEY);
        if (!stored) return false;

        const session = JSON.parse(stored) as { siteKey?: string; verifiedAt?: number };
        return (
            session.siteKey === TURNSTILE_SITE_KEY &&
            typeof session.verifiedAt === "number" &&
            Date.now() - session.verifiedAt < SESSION_TTL
        );
    } catch {
        return false;
    }
}

export function rememberTurnstileSession() {
    if (typeof window === "undefined") return;

    try {
        window.sessionStorage.setItem(SESSION_KEY, JSON.stringify({ siteKey: TURNSTILE_SITE_KEY, verifiedAt: Date.now() }));
    } catch {
        // Storage can be unavailable in private or embedded contexts.
    }
}
