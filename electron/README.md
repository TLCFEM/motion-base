# Motion Base Desktop

This directory contains the Electron shell for the Motion Base interface in
[`../gui-ark`](../gui-ark). The desktop application bundles the production build
of the web interface and loads it from a private `motion-base://` scheme.

## Requirements

- Node.js 24 or newer
- pnpm (npm is used as a fallback when pnpm is unavailable)

Install the Electron dependencies first.

```bash
cd electron
pnpm install
```

The first build also installs the `gui-ark` dependencies if they are missing.

## Development

```bash
pnpm start
```

`start` builds `gui-ark`, copies the result to `electron/dist`, and launches the
Electron application. Any change to the web interface requires restarting this
command.

The application expects a Motion Base API server. It uses
`http://127.0.0.1:8000` by default; use the **Change Server** button in the header
to connect to another deployment such as `https://tlcfem.top/mb/api`.

To bake a different default API URL into the bundle, set `MB_API_URL` while
building.

```bash
MB_API_URL=https://example.com/mb/api pnpm start
```

## Packaging

```bash
pnpm package   # unpacked application in out/
pnpm make      # installers in out/make/
```

The build step is shared by all commands. The following environment variables
are available for special cases:

| Variable | Purpose |
| --- | --- |
| `MB_API_URL` | Replace the default API base URL in the built JavaScript |
| `MB_UI_DIR` | Build a web interface from a directory other than `../gui-ark` |
| `MB_SKIP_UI_BUILD=1` | Reuse the existing `gui-ark/dist` instead of rebuilding |
| `MB_PACKAGE_MANAGER` | Package manager used for the `gui-ark` build |

## Application behaviour

- The interface is served through the privileged `motion-base://` scheme. This
  allows the bundled markdown files to be fetched normally and avoids the
  restrictions of `file://`.
- External links open in the default browser; navigation away from the bundled
  interface is blocked.
- The renderer runs sandboxed with context isolation enabled and no Node.js
  integration.
- OpenStreetMap tiles and the configured API server require network access.
