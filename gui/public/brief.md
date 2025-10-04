# motion-base

***Click the buttons on the top right to 1) get random records, 2) search records by criteria, and/or 3) process records.***

## What

`motion-base` is a proof-of-concept application to parse and process ground motion records.
It utilizes modern database tools such as [`Elasticsearch`](https://www.elastic.co/elasticsearch)
(for indexing and searching) and [`MongoDB`](https://www.mongodb.com/) (for storage).

`motion-base` provides the following main functionalities.

- [x] Parse and index ground motion records from different databases in a uniform format.
- [x] Search and select ground motion records based on different criteria, including magnitude, PGA, event time, event location, etc.
- [x] Provide ad hoc processing, including up-/down-sampling, normalization, filtering and computation of response spectra.
- [x] Provide standard machine-readable format for the processed data and a programmatic interface to allow further processing in large scale.
- [x] Convert acceleration record to velocity/displacement record that is consistent with specific time integration methods.

## Why

A recent paper [10.1080/13632469.2024.2372814](https://doi.org/10.1080/13632469.2024.2372814) discusses the need of
filtering the target ground motion records before using them in dynamic analyses.
The main conclusion is that, as a safety measure and general rule of thumb, any ground motion records need to be filtered
based on the properties of the system being analyzed and the time integration method used.

However, extracting, parsing and filtering ground motion records from different databases is not a trivial task.
For example, [PEER](https://ngawest2.berkeley.edu/) (USA) is restrictive and its interface is quite outdated and not easy to search and download records.
[NIED](https://www.kyoshin.bosai.go.jp/) (Japan) provides a feature-rich interface but lacks a programmatic API.
[NZSM](https://data.geonet.org.nz/seismic-products/strong-motion/volume-products/) (New Zealand) only provides a static HTTP server, searching is not possible and downloading can only be done by crawling.
All these databases provide raw data in similar but slightly different formats.

`motion-base` is aimed to address these issues by providing a uniform interface to search and download ground motion records from different databases.
The raw data acquired from various databases can be uploaded and parsed into a uniform format.
The data can then be indexed, queried, processed and downloaded in the machine-readable JSON format.
Because the presence of a programmatic interface, the data can be processed in large scale.

## How

### To deploy a local instance within X minutes

One can deploy a local instance using the following command.
It will download the `example.sh` script and execute it.
It will pull the docker images and deploys a local instance for illustration.
It then uploads the example data to the application.

```bash
curl -s https://raw.githubusercontent.com/TLCFEM/motion-base/refs/heads/master/scripts/example.sh -o example.sh && bash example.sh
```

Please ensure `docker`, `curl`, and `jq` are installed on the system.
Please always check the content of the script (especially from the Internet) before executing it.
The following is a walkthrough of the script.

[<p align="center"><img src="https://raw.githubusercontent.com/TLCFEM/motion-base/refs/heads/master/docs/demo.gif"></p>](https://asciinema.org/a/FYpQv4PFufAEArqzWBOyodzeQ)

### To develop the application locally

The following tools are required: `docker`, `pnpm`, `node` and `python3`.

```bash
# clone the project
git clone https://github.com/TLCFEM/motion-base.git
cd motion-base

# create a virtual environment using whatever tool you prefer
# python3 -m venv .venv
# source .venv/bin/activate

# install python dependencies
pip install -e .[dev,client]

# install node.js dependencies
cd gui && pnpm install && cd ..
```

#### Backend

To run the backend, execute the script `mb_runner.py` in the root directory.

```bash
python3 ./mb_runner.py
```

If you are familiar with [`FastAPI`](https://fastapi.tiangolo.com/), you can find other equivalent ways to run the backend.

#### Frontend

To run the frontend, execute the following command in the `gui` directory.

```bash
pnpm dev
```

## Currently Supported Databases

### Japan

The raw data is available at [Strong Motion Seismograph Networks](https://www.kyoshin.bosai.go.jp/).
The waveform files in ASCII format `*.EW`, `*.NS`, and `*.UD` can be uploaded and parsed.

### New Zealand

The raw data is available at [Strong Motion Data Products](https://www.geonet.org.nz/data/types/strong_motion).
The waveform files `*.V1A` and `*.V2A` can be uploaded and parsed.
