FROM python:3.11-slim as dependency

COPY requirements.txt /mb/requirements.txt
WORKDIR /mb

RUN apt-get update && apt-get install -y python3-pip

RUN pip3 install -r requirements.txt

FROM python:3.11-slim

COPY src/mb /mb/mb
COPY mb_runner.py /mb
WORKDIR /mb

COPY --from=dependency /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

CMD ["python3", "mb_runner.py", "host", "0.0.0.0"]
