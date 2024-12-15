FROM oven/bun:alpine AS build

COPY gui /mb/gui
WORKDIR /mb/gui

RUN bun install && bun run build

FROM oven/bun:alpine

COPY --from=build /mb/gui/dist /mb/gui/dist

COPY gui/src/assets/client.md /mb/gui/dist/assets/client.md
COPY gui/src/assets/client_files /mb/gui/dist/assets/client_files
COPY scripts/gui.sh /mb/gui/gui.sh

WORKDIR /mb/gui

ENTRYPOINT ["/bin/sh", "gui.sh"]

CMD ["170.64.176.26"]
