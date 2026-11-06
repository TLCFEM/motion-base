//  Copyright (C) 2022-2026 Theodore Chang
//
//  This program is free software: you can redistribute it and/or modify
//  it under the terms of the GNU General Public License as published by
//  the Free Software Foundation, either version 3 of the License, or
//  (at your option) any later version.

import { Component, createSignal, onCleanup, onMount, Show } from "solid-js";
import { responseMessage, verify_turnstile_api } from "./api";
import mb_logo from "./assets/logo.svg";
import { theme } from "./theme";
import { loadTurnstile, rememberTurnstileSession, TURNSTILE_SITE_KEY, TurnstileApi } from "./turnstile";

type Status = "loading" | "ready" | "verifying" | "error";

const TurnstileGate: Component<{ onVerified: () => void }> = (props) => {
    const [status, setStatus] = createSignal<Status>("loading");
    const [error, setError] = createSignal("");
    const [widgetId, setWidgetId] = createSignal<string>();

    let container: HTMLDivElement | undefined;
    let api: TurnstileApi | undefined;
    let active = true;
    let finished = false;

    function finish() {
        if (finished) return;
        finished = true;
        props.onVerified();
    }

    function resetWidget() {
        api?.reset(widgetId());
    }

    async function verify(token: string) {
        if (!active || !token) return;

        setStatus("verifying");
        setError("");

        try {
            const result = await verify_turnstile_api(token);
            if (!active) return;

            if (result.success) {
                rememberTurnstileSession();
                finish();
                return;
            }

            setError(
                result.errors?.length
                    ? `Verification failed (${result.errors.join(", ")}). Please try again.`
                    : "Verification failed. Please try again.",
            );
            setStatus("error");
            resetWidget();
        } catch (err) {
            if (!active) return;

            setError(responseMessage(err) || "Unable to verify the challenge. Please try again.");
            setStatus("error");
            resetWidget();
        }
    }

    async function mountWidget() {
        setError("");
        setStatus("loading");

        try {
            api = await loadTurnstile();
            if (!active || !container) return;

            if (widgetId()) {
                api.reset(widgetId());
                setStatus("ready");
                return;
            }

            const id = api.render(container, {
                sitekey: TURNSTILE_SITE_KEY,
                theme: theme() === "dark" ? "dark" : "light",
                callback: (token) => void verify(token),
                "error-callback": () => {
                    if (!active) return;
                    setError("The verification widget encountered an error. Please try again.");
                    setStatus("error");
                },
                "expired-callback": () => {
                    if (!active) return;
                    setError("The verification expired. Please try again.");
                    setStatus("error");
                },
                "timeout-callback": () => {
                    if (!active) return;
                    setError("The verification timed out. Please try again.");
                    setStatus("error");
                },
            });
            setWidgetId(id);
            setStatus("ready");
        } catch (err) {
            if (!active) return;
            setError(responseMessage(err) || "Unable to load Cloudflare Turnstile.");
            setStatus("error");
        }
    }

    function retry() {
        if (!api || !widgetId()) {
            void mountWidget();
            return;
        }

        setError("");
        setStatus("ready");
        resetWidget();
    }

    onMount(() => void mountWidget());

    onCleanup(() => {
        active = false;
        if (api && widgetId()) api.remove(widgetId()!);
    });

    return (
        <div class="turnstile-gate">
            <section
                class="turnstile-card"
                aria-labelledby="turnstile-title"
                aria-busy={status() === "loading" || status() === "verifying"}
            >
                <img class="turnstile-mark" src={mb_logo} alt="" aria-hidden="true" />
                <h1 id="turnstile-title">Verify you are human</h1>
                <p class="turnstile-intro">Complete the quick security check to access the Motion Base database.</p>

                <div class="turnstile-widget" ref={container} />

                <Show when={status() === "loading"}>
                    <p class="turnstile-status" aria-live="polite">
                        Loading verification…
                    </p>
                </Show>
                <Show when={status() === "verifying"}>
                    <p class="turnstile-status" aria-live="polite">
                        Verifying…
                    </p>
                </Show>
                <Show when={error()}>
                    <p class="error-text" role="alert">
                        {error()}
                    </p>
                </Show>

                <div class="turnstile-actions">
                    <Show when={status() === "error"}>
                        <button class="btn" onClick={retry}>
                            Try again
                        </button>
                    </Show>
                </div>

                <p class="turnstile-note">
                    Protected by{" "}
                    <a href="https://www.cloudflare.com/products/turnstile/" target="_blank" rel="noreferrer">
                        Cloudflare Turnstile
                    </a>
                    .
                </p>
            </section>
        </div>
    );
};

export default TurnstileGate;
