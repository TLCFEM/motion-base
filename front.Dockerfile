FROM node:20-slim AS build

COPY gui /mb/gui
WORKDIR /mb/gui

RUN npm install -g npm@latest pnpm && pnpm install && pnpm build

FROM node:20-slim

COPY --from=build /mb/gui/dist /mb/gui/dist
COPY scripts/gui.sh /mb/gui/gui.sh

WORKDIR /mb/gui

RUN npm install -g serve

ENTRYPOINT ["bash", "gui.sh"]

CMD ["170.64.176.26", "-l", "4173"]
