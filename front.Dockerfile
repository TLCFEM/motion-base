FROM oven/bun:alpine AS build

COPY gui /mb/gui
WORKDIR /mb/gui

RUN bun install --production && bun run build

FROM oven/bun:alpine

ENV NODE_ENV=production

COPY --from=build /mb/gui/dist /mb/gui/dist

RUN for file in /mb/gui/dist/assets/*.js; do sed -i "s#src/assets/#./assets/#g" "$file"; done

COPY gui/src/assets/brief.md /mb/gui/dist/assets/brief.md
COPY gui/src/assets/client.md /mb/gui/dist/assets/client.md
COPY gui/src/assets/client_files /mb/gui/dist/assets/client_files
COPY scripts/gui.sh /mb/gui/gui.sh

WORKDIR /mb/gui

ENTRYPOINT ["/bin/sh", "gui.sh"]

CMD ["https://mb.tlcfem.top:8443"]
