FROM node:18 as gui

COPY . /mb
WORKDIR /mb/gui

RUN curl -f https://get.pnpm.io/v6.16.js | node - add --global pnpm && pnpm install && pnpm build

FROM python:3.10.7-slim as dependency

COPY ./requirements.txt /mb
WORKDIR /mb

RUN apt-get update && apt-get install -y python3-pip

RUN pip3 install -r requirements.txt

FROM python:3.10.7-slim

COPY . /mb
WORKDIR /mb

COPY --from=gui /mb/gui/dist ./mb/app/dist
COPY --from=dependency /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages

CMD ["python3", "mb.py", "workers", "4"]
