# motion-base Documentation

`motion-base` is a self-hostable strong-motion database with a web interface, an HTTP API, and an async Python client.
It ingests raw archives from national networks, normalizes records into one schema, and makes them searchable, processable, and downloadable.

![motion-base web interface](./screenshot.png)

## Start Here

| Goal | Page |
| --- | --- |
| Understand the system design | [Architecture](Architecture.md) |
| Deploy or develop locally | [Deployment](Deployment.md) |
| Upload or crawl new records | [Ingestion](Ingestion.md) |
| Search and paginate records | [Search](Search.md) |
| Process waveforms and compute spectra | [Processing](Processing.md) |
| Automate work with Python | [Python Client](PythonClient.md) |
| Look up HTTP endpoints | [API Reference](API.md) |

## Quick Links

- [Live demo](https://tlcfem.top/mb/)
- [Interactive API documentation](https://tlcfem.top/mb/api/docs)
- [Root README](../README.md)
- [Executable client notebook](client.ipynb)
- [DeepWiki](https://deepwiki.com/TLCFEM/motion-base)

## What It Does

- Imports NIED (Japan) and GeoNet/NZSM (New Zealand) records into a uniform format.
- Indexes metadata in Elasticsearch and stores complete records in MongoDB.
- Filters by region, magnitude, PGA, event/station location, date, station code, direction, and file name.
- Downloads waveforms and returns machine-readable JSON.
- Resamples, filters, normalizes, and removes leading samples on demand.
- Computes FFT spectra and displacement, velocity, and acceleration response spectra.
- Provides an async Python client for bulk search, download, upload, and plotting.
- Runs parsing in background workers through Taskiq and RabbitMQ.

## Documentation Conventions

- API paths are relative to the deployment base URL, such as `https://tlcfem.top/mb/api` or `http://localhost:8000`.
- Timestamps use ISO 8601 format and should include a timezone when possible.
- PGA values are expressed in Gal, which is equivalent to `cm/s²`.
- Distances are expressed in meters.
- Filter cutoffs are expressed in hertz.
- `MBClient` examples assume an existing server and the `client` extra installed.

## Source Layout

| Path | Contents |
| --- | --- |
| `src/mb/` | FastAPI application, records, parsers, processing, client, and task queue integration |
| `src/crawler/` | NIED and GeoNet archive crawlers |
| `gui/` | SolidJS web interface |
| `electron/` | Optional desktop shell around the built web interface |
| `docker/` | Compose files, nginx helper, environment template, and Kubernetes manifests |
| `tests/` | Pytest suite, sample records, and load-test configuration |
| `docs/` | This flat documentation set and its images |

## Getting Help

Report bugs and feature requests through [GitHub Issues](https://github.com/TLCFEM/motion-base/issues).
The project welcomes parsers for additional national databases, processing improvements, and documentation fixes.
