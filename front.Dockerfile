FROM node:18 as gui

COPY gui /mb/gui
WORKDIR /mb/gui

RUN sed -i 's/127.0.0.1/0.0.0.0/g' /mb/gui/src/index.tsx

RUN npm install -g pnpm && pnpm install && pnpm build

CMD ["pnpm", "start"]
