FROM node:20-slim as build

COPY gui /mb/gui
WORKDIR /mb/gui

RUN sed -i 's/127.0.0.1/172.104.155.229/g' src/API.tsx

RUN npm install -g pnpm && pnpm install && pnpm build

FROM node:20-slim as gui

COPY --from=build /mb/gui/dist /mb/gui/dist

WORKDIR /mb/gui

RUN npm install -g serve

CMD ["npx", "serve", "-n", "-s", "dist", "-l", "4173"]
