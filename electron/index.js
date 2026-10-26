const { app, BrowserWindow, Menu, dialog, protocol, session, shell } = require("electron");
const fs = require("node:fs");
const fsp = require("node:fs/promises");
const path = require("node:path");

// Handle creating/removing shortcuts on Windows when installing/uninstalling.
if (require("electron-squirrel-startup")) {
    app.quit();
}

app.setName("Motion Base");

const APP_SCHEME = "motion-base";
const APP_HOST = "app";
const APP_ORIGIN = `${APP_SCHEME}://${APP_HOST}`;
const APP_URL = `${APP_ORIGIN}/index.html`;
const UI_ROOT = path.join(__dirname, "dist");
const ICON_PATH = path.join(__dirname, "assets", "icon.png");
const PROJECT_URL = "https://github.com/TLCFEM/motion-base";

// The frontend is loaded through a custom, standard scheme instead of file://.
// This keeps fetch() working for the bundled markdown files and gives the page
// a stable, secure origin for localStorage and network requests.
protocol.registerSchemesAsPrivileged([
    {
        scheme: APP_SCHEME,
        privileges: {
            standard: true,
            secure: true,
            supportFetchAPI: true,
            corsEnabled: true,
            stream: true,
        },
    },
]);

const MIME_TYPES = {
    ".css": "text/css; charset=utf-8",
    ".gif": "image/gif",
    ".html": "text/html; charset=utf-8",
    ".ico": "image/x-icon",
    ".jpeg": "image/jpeg",
    ".jpg": "image/jpeg",
    ".js": "text/javascript; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".map": "application/json; charset=utf-8",
    ".md": "text/markdown; charset=utf-8",
    ".mjs": "text/javascript; charset=utf-8",
    ".otf": "font/otf",
    ".pdf": "application/pdf",
    ".png": "image/png",
    ".svg": "image/svg+xml",
    ".ttf": "font/ttf",
    ".txt": "text/plain; charset=utf-8",
    ".wasm": "application/wasm",
    ".webp": "image/webp",
    ".woff": "font/woff",
    ".woff2": "font/woff2",
};

let mainWindow = null;

function response(status, body, type = "text/plain; charset=utf-8") {
    return new Response(body, {
        status,
        headers: { "content-type": type },
    });
}

function resolveAsset(requestUrl) {
    const url = new URL(requestUrl);

    if (url.host !== APP_HOST) return null;

    let pathname;
    try {
        pathname = decodeURIComponent(url.pathname);
    } catch {
        return null;
    }

    if (pathname === "" || pathname === "/") pathname = "/index.html";
    else if (pathname.endsWith("/")) pathname += "index.html";

    const filePath = path.resolve(UI_ROOT, `.${pathname}`);
    const relative = path.relative(UI_ROOT, filePath);

    if (relative === "" || relative === ".." || relative.startsWith(`..${path.sep}`) || path.isAbsolute(relative)) {
        return null;
    }

    return { filePath, pathname };
}

function registerAppProtocol() {
    protocol.handle(APP_SCHEME, async (request) => {
        const asset = resolveAsset(request.url);

        if (!asset) return response(400, "Bad request");

        try {
            const data = await fsp.readFile(asset.filePath);
            const extension = path.extname(asset.filePath).toLowerCase();
            const immutable = asset.pathname.startsWith("/assets/");

            return new Response(request.method === "HEAD" ? null : data, {
                status: 200,
                headers: {
                    "content-type": MIME_TYPES[extension] || "application/octet-stream",
                    "cache-control": immutable ? "public, max-age=31536000, immutable" : "no-cache",
                },
            });
        } catch (error) {
            if (error && (error.code === "ENOENT" || error.code === "EISDIR")) {
                return response(404, "Not found");
            }

            console.error(`Failed to serve ${asset.filePath}:`, error);
            return response(500, "Internal server error");
        }
    });
}

function isAppUrl(rawUrl) {
    try {
        const url = new URL(rawUrl);
        return url.protocol === `${APP_SCHEME}:` && url.host === APP_HOST;
    } catch {
        return false;
    }
}

function isExternalUrl(rawUrl) {
    try {
        const url = new URL(rawUrl);
        return url.protocol === "https:" || url.protocol === "http:";
    } catch {
        return false;
    }
}

function openExternal(rawUrl) {
    if (!isExternalUrl(rawUrl)) return;

    shell.openExternal(rawUrl).catch((error) => {
        console.error(`Failed to open ${rawUrl}:`, error);
    });
}

function installApplicationMenu() {
    const template = [];

    if (process.platform === "darwin") {
        template.push({ role: "appMenu" });
    }

    template.push(
        { role: "fileMenu" },
        { role: "editMenu" },
        { role: "viewMenu" },
        { role: "windowMenu" },
        {
            role: "help",
            submenu: [
                {
                    label: "Project Home",
                    click: () => openExternal(PROJECT_URL),
                },
                {
                    label: "Report an Issue",
                    click: () => openExternal(`${PROJECT_URL}/issues`),
                },
            ],
        },
    );

    Menu.setApplicationMenu(Menu.buildFromTemplate(template));
}

function configureSession() {
    // The bundled interface does not need any privileged platform permissions.
    session.defaultSession.setPermissionRequestHandler((_webContents, _permission, callback) => callback(false));
    session.defaultSession.setPermissionCheckHandler(() => false);
}

const createWindow = () => {
    mainWindow = new BrowserWindow({
        width: 1440,
        height: 900,
        minWidth: 960,
        minHeight: 600,
        show: false,
        title: "Motion Base",
        backgroundColor: "#f3f6f7",
        autoHideMenuBar: process.platform !== "darwin",
        icon: fs.existsSync(ICON_PATH) ? ICON_PATH : undefined,
        webPreferences: {
            contextIsolation: true,
            nodeIntegration: false,
            sandbox: true,
            webSecurity: true,
            spellcheck: false,
        },
    });

    mainWindow.once("ready-to-show", () => {
        mainWindow.show();
    });

    // Never open web content inside the application window. Links in the
    // interface are handed to the user's default browser instead.
    mainWindow.webContents.setWindowOpenHandler(({ url }) => {
        openExternal(url);
        return { action: "deny" };
    });

    mainWindow.webContents.on("will-navigate", (event, url) => {
        if (isAppUrl(url)) return;

        event.preventDefault();
        openExternal(url);
    });

    mainWindow.webContents.on("will-redirect", (event, url) => {
        if (isAppUrl(url)) return;

        event.preventDefault();
        openExternal(url);
    });

    mainWindow.webContents.on("will-attach-webview", (event) => {
        event.preventDefault();
    });

    mainWindow.on("closed", () => {
        mainWindow = null;
    });

    mainWindow.loadURL(APP_URL).catch((error) => {
        console.error("Failed to load the Motion Base interface:", error);
        dialog.showErrorBox(
            "Motion Base could not load",
            `The bundled interface could not be loaded.\n\n${error instanceof Error ? error.message : String(error)}`,
        );
        app.quit();
    });
};

const hasSingleInstanceLock = app.requestSingleInstanceLock();

if (!hasSingleInstanceLock) {
    app.quit();
} else {
    app.on("second-instance", () => {
        if (!mainWindow) return;

        if (mainWindow.isMinimized()) mainWindow.restore();
        mainWindow.show();
        mainWindow.focus();
    });

    app.whenReady().then(() => {
        if (!fs.existsSync(path.join(UI_ROOT, "index.html"))) {
            dialog.showErrorBox(
                "Motion Base could not start",
                "The web interface is missing from the application bundle.\n\n" +
                    'Run "pnpm run build:ui" in the electron directory before starting the application.',
            );
            app.quit();
            return;
        }

        if (process.platform === "win32") {
            app.setAppUserModelId("top.tlcfem.motion-base");
        }

        app.setAboutPanelOptions({
            applicationName: "Motion Base",
            applicationVersion: app.getVersion(),
            copyright: "Copyright © 2022-2026 Theodore Chang",
            website: PROJECT_URL,
        });

        registerAppProtocol();
        configureSession();
        installApplicationMenu();
        createWindow();

        // On macOS it is common to re-create a window in the app when the
        // dock icon is clicked and there are no other windows open.
        app.on("activate", () => {
            if (BrowserWindow.getAllWindows().length === 0) {
                createWindow();
            }
        });
    });
}

// Quit when all windows are closed, except on macOS. There, it is common
// for applications and their menu bar to stay active until the user quits
// explicitly with Cmd + Q.
app.on("window-all-closed", () => {
    if (process.platform !== "darwin") {
        app.quit();
    }
});
