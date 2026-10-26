import { afterEach, describe, expect, it } from "vitest";
import { applyTheme, setTheme, storedTheme, theme, toggleTheme } from "../src/theme";

afterEach(() => {
    localStorage.clear();
    document.documentElement.removeAttribute("data-theme");
    document.documentElement.style.colorScheme = "";
});

describe("theme", () => {
    it("persists and applies an explicit theme", () => {
        setTheme("dark");
        applyTheme(theme());

        expect(theme()).toBe("dark");
        expect(storedTheme()).toBe("dark");
        expect(document.documentElement.dataset.theme).toBe("dark");
        expect(document.documentElement.style.colorScheme).toBe("dark");
    });

    it("toggles between light and dark", () => {
        setTheme("light");
        toggleTheme();
        expect(theme()).toBe("dark");

        toggleTheme();
        expect(theme()).toBe("light");
    });
});
