import { defineConfig } from "vitest/config";
import solid from "vite-plugin-solid";

export default defineConfig({
    plugins: [solid()],
    server: {
        port: 3000,
    },
    build: {
        target: "esnext",
        chunkSizeWarningLimit: 5000,
    },
    base: "./",
    test: {
        environment: "jsdom",
        globals: true,
        include: ["tests/**/*.test.ts", "tests/**/*.test.tsx"],
    },
});
