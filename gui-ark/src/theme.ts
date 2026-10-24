//  Copyright (C) 2022-2026 Theodore Chang
//
//  This program is free software: you can redistribute it and/or modify
//  it under the terms of the GNU General Public License as published by
//  the Free Software Foundation, either version 3 of the License, or
//  (at your option) any later version.

import { createSignal } from "solid-js";

export type Theme = "light" | "dark";

const STORAGE_KEY = "mb-theme";

export function systemTheme(): Theme {
    if (typeof window === "undefined" || typeof window.matchMedia !== "function") return "light";
    return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export function storedTheme(): Theme | null {
    if (typeof window === "undefined") return null;

    try {
        const value = window.localStorage.getItem(STORAGE_KEY);
        return value === "light" || value === "dark" ? value : null;
    } catch {
        return null;
    }
}

export function initialTheme(): Theme {
    const stored = storedTheme();
    if (stored) return stored;

    const current = typeof document === "undefined" ? undefined : document.documentElement.dataset.theme;
    return current === "light" || current === "dark" ? current : systemTheme();
}

export const [theme, setThemeSignal] = createSignal<Theme>(initialTheme());

export function applyTheme(value: Theme) {
    if (typeof document === "undefined") return;

    document.documentElement.dataset.theme = value;
    document.documentElement.style.colorScheme = value;
    document.querySelector('meta[name="theme-color"]')?.setAttribute("content", value === "dark" ? "#0b1220" : "#f3f6f7");
}

export function setTheme(value: Theme) {
    try {
        window.localStorage.setItem(STORAGE_KEY, value);
    } catch {
        // Storage can be unavailable in private or embedded contexts.
    }

    setThemeSignal(value);
}

export function toggleTheme() {
    setTheme(theme() === "dark" ? "light" : "dark");
}

export function followsSystem() {
    return storedTheme() === null;
}

export function watchSystemTheme(): () => void {
    if (typeof window === "undefined" || typeof window.matchMedia !== "function") return () => undefined;

    const query = window.matchMedia("(prefers-color-scheme: dark)");
    const update = (event: MediaQueryListEvent) => {
        if (followsSystem()) setThemeSignal(event.matches ? "dark" : "light");
    };

    query.addEventListener?.("change", update);
    return () => {
        query.removeEventListener?.("change", update);
    };
}
