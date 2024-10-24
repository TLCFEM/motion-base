FROM oven/bun:alpine AS build

COPY gui /mb/gui
WORKDIR /mb/gui

RUN bun install && bun run build

FROM oven/bun:alpine

COPY --from=build /mb/gui/dist /mb/gui/dist
COPY scripts/gui.sh /mb/gui/gui.sh

WORKDIR /mb/gui

ENTRYPOINT ["/bin/sh", "gui.sh"]

CMD ["170.64.176.26"]
