FROM node:20-slim as gui

COPY gui /mb/gui
WORKDIR /mb/gui

RUN npm install -g pnpm && pnpm install && pnpm build

CMD ["pnpm", "serve", "--host"]
