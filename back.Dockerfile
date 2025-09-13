FROM python:3.13-slim AS dependency

COPY requirements.txt /mb/requirements.txt
WORKDIR /mb

RUN pip install --no-cache-dir --upgrade -r requirements.txt

FROM python:3.13-slim

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

COPY --from=dependency /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages

COPY src/mb /mb/mb
COPY mb_runner.py /mb
WORKDIR /mb

RUN useradd -m runner
USER runner

ENV PYTHONOPTIMIZE=2

ENTRYPOINT ["python3", "mb_runner.py"]

CMD ["host", "0.0.0.0"]
