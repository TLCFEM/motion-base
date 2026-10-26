#!/usr/bin/env node

"use strict";

const { spawnSync } = require("node:child_process");
const { cpSync, existsSync, readdirSync, readFileSync, rmSync, writeFileSync } = require("node:fs");
const path = require("node:path");

const electronRoot = path.resolve(__dirname, "..");
const repositoryRoot = path.resolve(electronRoot, "..");
const uiRoot = path.resolve(process.env.MB_UI_DIR || path.join(repositoryRoot, "gui"));
const uiDist = path.join(uiRoot, "dist");
const outputRoot = path.join(electronRoot, "dist");
const defaultApiUrl = "http://127.0.0.1:8000";

const isWindows = process.platform === "win32";

function run(command, args, options = {}) {
    console.log(`> ${[command, ...args].join(" ")}`);

    const result = spawnSync(command, args, {
        cwd: options.cwd,
        env: { ...process.env, ...options.env },
        stdio: "inherit",
        shell: isWindows,
    });

    if (result.error) throw result.error;
    if (result.status !== 0) {
        throw new Error(`Command failed with exit code ${result.status}: ${command} ${args.join(" ")}`);
    }
}

function hasCommand(command) {
    const result = spawnSync(command, ["--version"], { stdio: "ignore", shell: isWindows });
    return !result.error && result.status === 0;
}

function resolvePackageManager() {
    if (process.env.MB_PACKAGE_MANAGER) {
        return { command: process.env.MB_PACKAGE_MANAGER, prefix: [] };
    }

    if (hasCommand("pnpm")) return { command: "pnpm", prefix: [] };
    if (hasCommand("npm")) return { command: "npm", prefix: [] };
    if (hasCommand("corepack")) return { command: "corepack", prefix: ["pnpm"] };

    throw new Error("Could not find pnpm, npm, or corepack. Install one of them and try again.");
}

function replaceApiUrl(directory) {
    const apiUrl = process.env.MB_API_URL?.trim().replace(/\/+$/, "");

    if (!apiUrl || apiUrl === defaultApiUrl) return;

    let files = 0;

    for (const entry of readdirSync(directory, { withFileTypes: true })) {
        const target = path.join(directory, entry.name);

        if (entry.isDirectory()) {
            files += replaceApiUrl(target);
        } else if (entry.isFile() && entry.name.endsWith(".js")) {
            const source = readFileSync(target, "utf8");

            if (source.includes(defaultApiUrl)) {
                writeFileSync(target, source.replaceAll(defaultApiUrl, apiUrl));
                files += 1;
            }
        }
    }

    return files;
}

function main() {
    if (!existsSync(path.join(uiRoot, "package.json"))) {
        throw new Error(`The web interface was not found at ${uiRoot}. Set MB_UI_DIR to the gui directory.`);
    }

    if (process.env.MB_SKIP_UI_BUILD === "1") {
        console.log("Skipping the web interface build because MB_SKIP_UI_BUILD=1.");
    } else {
        if (!existsSync(path.join(uiRoot, "node_modules"))) {
            console.log("Installing web interface dependencies...");
            const packageManager = resolvePackageManager();
            run(packageManager.command, [...packageManager.prefix, "install"], { cwd: uiRoot });
        }

        console.log(`Building the web interface in ${uiRoot}...`);
        const packageManager = resolvePackageManager();
        run(packageManager.command, [...packageManager.prefix, "run", "build"], { cwd: uiRoot });
    }

    if (!existsSync(path.join(uiDist, "index.html"))) {
        throw new Error(`The web interface build did not produce ${path.join(uiDist, "index.html")}.`);
    }

    rmSync(outputRoot, { recursive: true, force: true });
    cpSync(uiDist, outputRoot, { recursive: true });

    const replaced = replaceApiUrl(outputRoot);
    if (replaced > 0) {
        console.log(`Using ${process.env.MB_API_URL} as the default API server.`);
    }

    console.log(`Copied the web interface to ${outputRoot}.`);
}

try {
    main();
} catch (error) {
    console.error(error instanceof Error ? error.message : error);
    process.exit(1);
}
