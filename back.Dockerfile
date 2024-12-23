FROM python:3.11-slim AS dependency

COPY requirements.txt /mb/requirements.txt
WORKDIR /mb

RUN pip install --no-cache-dir --upgrade -r requirements.txt

FROM python:3.11-slim

COPY --from=dependency /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

COPY src/mb /mb/mb
COPY mb_runner.py /mb
WORKDIR /mb

RUN useradd -m runner
USER runner

ENV PYTHONOPTIMIZE=2

ENTRYPOINT ["python3", "mb_runner.py"]

CMD ["host", "0.0.0.0"]
