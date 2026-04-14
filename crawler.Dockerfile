FROM python:3.12-slim

RUN pip install --no-cache-dir click aiohttp beautifulsoup4

COPY src/crawler /crawler

RUN for f in $(find /crawler -name "*.py"); do \
dest="/usr/local/bin/$(basename "${f%.py}")"; \
cp "$f" "$dest" && chmod +x "$dest"; \
done

RUN ls -halt /usr/local/bin
