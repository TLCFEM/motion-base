FROM oven/bun:alpine AS build

COPY gui /mb/gui
WORKDIR /mb/gui

RUN bun install && bun run build

FROM oven/bun:alpine

RUN apk add --no-cache curl

HEALTHCHECK --interval=5m --timeout=10s --start-period=30s --retries=10 CMD curl -f http://localhost:3000

ENV NODE_ENV=production

COPY --from=build /mb/gui/dist /mb/gui/dist

COPY scripts/gui.sh /mb/gui/gui.sh

WORKDIR /mb/gui

ENTRYPOINT ["/bin/sh", "gui.sh"]

CMD ["https://tlcfem.top/mb/api"]
