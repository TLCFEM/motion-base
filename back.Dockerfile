FROM python:3.12-slim AS dependency

COPY requirements.txt /mb/requirements.txt
WORKDIR /mb

RUN pip install --no-cache-dir --no-compile --upgrade -r requirements.txt

RUN apt-get update && apt-get install -y --no-install-recommends binutils && rm -rf /var/lib/apt/lists/*

# RUN find /usr/local/lib/python*/site-packages -type d \( -name "tests" -o -name "test" -o -name "testing" -o -name "__pycache__" \) -not -path "*/numpy/testing" -prune -exec rm -rf {} +
# RUN find /usr/local/lib/python*/site-packages -type f \( -name "*.md" -o -name "*.rst" -o -name "*.txt" \) -not -path "*/pint/*.txt" -delete
RUN find /usr/local/lib/python*/site-packages -name "*.so" -exec strip --strip-unneeded {} +

FROM python:3.12-slim

COPY --from=dependency /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages

COPY src/mb /mb/mb
COPY mb_runner.py /mb
WORKDIR /mb

RUN useradd -m runner
USER runner

ENV PYTHONOPTIMIZE=1

ENTRYPOINT ["python3", "mb_runner.py"]

CMD ["host", "0.0.0.0"]
