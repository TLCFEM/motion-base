FROM node:20-slim as gui

COPY gui /mb/gui
WORKDIR /mb/gui

RUN sed -i 's/127.0.0.1/0.0.0.0/g' /mb/gui/src/API.tsx

RUN npm install -g pnpm && pnpm install && pnpm build

CMD ["pnpm", "serve", "--host"]
