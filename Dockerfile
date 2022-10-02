FROM node:18 as gui

COPY . /mb
WORKDIR /mb/gui

RUN sed -i 's/127.0.0.1/0.0.0.0/g' /mb/gui/src/index.tsx

RUN curl -f https://get.pnpm.io/v6.16.js | node - add --global pnpm && pnpm install && pnpm build

FROM python:3.10.7-slim as dependency

COPY . /mb
WORKDIR /mb

RUN apt-get update && apt-get install -y python3-pip

RUN pip3 install -r requirements.txt

FROM python:3.10.7-slim

COPY . /mb
WORKDIR /mb

COPY --from=gui /mb/gui/dist ./mb/app/dist
COPY --from=dependency /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
RUN sed -i 's/MONGO_HOST = localhost/MONGO_HOST = mongo/g' /mb/mb/.env
RUN python3 -c 'from mb import rewrite; rewrite()'

CMD ["python3", "mb.py", "workers", "4", "host", "0.0.0.0"]
