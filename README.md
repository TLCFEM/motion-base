# motion-base

[![codecov](https://codecov.io/gh/TLCFEM/motion-base/branch/master/graph/badge.svg?token=E6TCZUQ6AX)](https://codecov.io/gh/TLCFEM/motion-base)
[![front-size](https://img.shields.io/docker/image-size/tlcfem/motion-base-front?label=front%20end)](https://hub.docker.com/r/tlcfem/motion-base-front)
[![back-size](https://img.shields.io/docker/image-size/tlcfem/motion-base-back?label=back%20end)](https://hub.docker.com/r/tlcfem/motion-base-back)


`motion-base` is a web application that aims to provide a unified entry point for accessing and processing ground motion
records from different national databases.

It comes with a web interface and a Python client that can be used to access the data programmatically.

**Check out the [demo](http://170.64.176.26/) site.**

![screenshot](docs/screenshot.png)

## Main Functionalities

- [x] Parse and index ground motion records from different databases in a uniform format.
- [x] Search and select ground motion records based on different criteria, including magnitude, PGA, event time, event location, etc.
- [x] Provide ad hoc processing, including up-/down-sampling, normalization, filtering and computation of response spectra.
- [x] Converting acceleration record to velocity/displacement record that is consistent with specific time integration methods.

## Quick Start

Please ensure `docker`, `curl`, and `jq` are installed on the system.
The following command will download the `example.sh` script and execute it.
It will pull the images and upload the example data to the application.

```bash
curl -s https://raw.githubusercontent.com/TLCFEM/motion-base/refs/heads/master/scripts/example.sh -o example.sh && bash example.sh
```

Please always check the content of the script (especially from the Internet) before executing it.
The following is a walkthrough of the script.

[![walkthrough](docs/demo.gif)](https://asciinema.org/a/FYpQv4PFufAEArqzWBOyodzeQ)

## Installation

### as a developer

```bash
# 1. clone the project
git clone https://github.com/TLCFEM/motion-base.git
cd motion-base
# 2. create a virtual environment and install python dependencies
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev,client]
# 3. install node.js dependencies
cd gui
pnpm install
cd ..
```

There are no extra steps needed to set up the development environment.
To run the application locally, use the following command:

```bash
# 1. mongodb and rabbitmq
docker compose -f docker/docker-compose.yml up -d
# 2. backend
python ./mb_runner.py
# 3. celery workers
python ./mb_runner.py celery
# 4. frontend
cd gui
pnpm dev
```

Use `back.Dockerfile` and `front.Dockerfile` to build the docker images for the backend and frontend, respectively.

### as a host

To host the application, two files are needed: `.env` and `docker-compose-production.yml`.

```bash
mkdir motion-base && cd motion-base
wget https://raw.githubusercontent.com/TLCFEM/motion-base/master/docker/.env
wget https://raw.githubusercontent.com/TLCFEM/motion-base/master/docker/docker-compose-production.yml

# edit the .env file to set the correct values
# or create those environment variables in other means
docker compose -f docker-compose-production.yml up -d
```

It shall run out of the box, but it is recommended to check the settings and adjust accordingly.

It is recommended to use one process per container and scale the application horizontally.
To do so, one can check the example given in file `docker/docker-compose-production-nginx.yaml`.
To use it, `docker/nginx.conf.sh` should also be available.

```bash
mkdir motion-base && cd motion-base
wget https://raw.githubusercontent.com/TLCFEM/motion-base/master/docker/.env
wget https://raw.githubusercontent.com/TLCFEM/motion-base/master/docker/nginx.conf.sh
wget https://raw.githubusercontent.com/TLCFEM/motion-base/master/docker/docker-compose-production-nginx.yml

docker compose -f docker-compose-production-nginx.yml up -d
```

Please feel free to use other tools to deploy the application, such as Kubernetes, Docker Swarm, etc.

### as an analyst

```bash
# 1. clone the project
git clone https://github.com/TLCFEM/motion-base.git
cd motion-base
# 2. create a virtual environment and install python dependencies
python -m venv .venv
source .venv/bin/activate
pip install .[client]
```

It is then possible to use the client to access the data.

```python
import anyio

from mb.client import MBClient

api_url = "http://somewhere.the.application.is.hosted"


async def search():
    async with MBClient(api_url) as client:
        results = await client.search({"min_magnitude": 6.0, "min_pga": 200.0})
        for r in results:
            print(r)


if __name__ == "__main__":
    anyio.run(search)
```

## Raw Data Source

The raw data, once downloaded from sources, can be uploaded to the application.

```python
import anyio

from mb.client import MBClient

# assuming the application is running locally
api_url = "http://localhost:8000"
# using the default credentials
username = "test"
password = "password"
region = "jp"


# assume current folder contains the files to be uploaded
async def upload():
    async with MBClient(api_url, username, password) as client:
        await client.upload(region, '.')


if __name__ == "__main__":
    anyio.run(upload)
```

### Japan

The raw data is available
at [Strong Motion Seismograph Networks](https://www.kyoshin.bosai.go.jp/kyoshin/data/index_en.html).
The waveform files in ASCII format `*.EW`, `*.NS`, and `*.UD` can be uploaded and parsed.

### New Zealand

The raw data is available at [Strong Motion Data Products](https://www.geonet.org.nz/data/types/strong_motion).
The waveform files `*.V1A` and `*.V2A` can be uploaded and parsed.
