# Architecture

`motion-base` separates metadata search, raw record storage, and expensive parsing.
The result is a small set of stateless HTTP processes backed by shared storage and an asynchronous task queue.

![Component overview](./components.svg)

## Core Components

| Component | Responsibility |
| --- | --- |
| FastAPI (`src/mb/app`) | Authentication, querying, waveform delivery, processing, upload orchestration, and user administration. |
| SolidJS UI (`gui`) | Search table, map, waveform plots, processing controls, statistics, and embedded documentation. |
| MongoDB | Source of truth for full records, users, upload tasks, and Taskiq results. |
| Elasticsearch | Metadata index for `/search`, `/stats`, deep pagination, and purge workflows. |
| RabbitMQ | Message broker that carries parsing jobs. |
| Taskiq worker | Parses archives and writes records outside the HTTP request cycle. |
| S3-compatible cache | Shared temporary storage for uploaded archives, backed by SeaweedFS or RustFS. |
| Processing modules | Parsers, filters, FFT, response spectra, and unit conversion. |

The FastAPI app lives under `src/mb/app/main.py`.
The frontend is a static build and can be served by any web server.
The Electron directory is an optional desktop shell for that build.

## Read Path

1. A client sends a `QueryConfig` object to `/query` or `/search`.
2. `/query` reads metadata from MongoDB and supports simple offset pagination.
3. `/search` reads metadata from Elasticsearch and supports `search_after` pagination.
4. The client receives record metadata without waveform arrays.
5. The client posts one or more record IDs to `/waveform` to download acceleration data.
6. `/process` loads one record and applies the requested transformation in the API process.

Queries never return waveforms by default.
This keeps search responses small and lets clients download only the records they need.
The `/waveform` endpoint converts stored raw samples into floating-point values and returns a time interval with the data.

## Ingestion Path

1. A client authenticates and posts an archive to `/jp/upload` or `/nz/upload`.
2. `commit_files()` stores the archive in the S3-compatible cache.
3. The API checks for a live Taskiq worker.
4. With a worker present, the API creates an `UploadTask` and sends the archive URI to RabbitMQ.
5. Without a worker, the API schedules an in-process background task instead.
6. The parser reads the archive, emits normalized records, and handles nested archives.
7. Each record is saved to MongoDB.
8. Metadata is bulk-indexed into Elasticsearch after parsing.
9. The `UploadTask` reports progress while files are processed and is deleted when parsing completes.

Taskiq uses RabbitMQ as its broker and MongoDB as its result backend.
Retries are handled by `SmartRetryMiddleware` for connection and timeout failures.
The API detects workers by checking the consumer count on the `taskiq` queue.
See [Ingestion](Ingestion.md) for upload formats, task monitoring, and crawler usage.

## Data Model

MongoDB contains three application collections.

| Collection | Contents |
| --- | --- |
| `Record` | Complete metadata plus raw samples, raw unit, offset, and scale factor. |
| `User` | Username, email, password hash, disabled flag, upload permission, and delete permission. |
| `UploadTask` | Task ID, process ID, archive path, total item count, and current progress. |

Taskiq also stores task results in `taskiq_results`.

A record has deterministic identity and deduplication support.

- `id` is a UUID5 derived from file name, region, category, update time, and direction.
- `file_hash` is the SHA-256 hash of the source content.
- `overwrite_existing=true` removes an existing record with the same hash before inserting the new one.
- `region` is `jp` or `nz`.
- `category` identifies the source collection, such as `knt`, `kik`, `processed`, or `unprocessed`.

Record metadata includes event time, event location, depth, magnitude, station code, station location, station elevation, record time, sampling frequency, duration, direction, and PGA.
Locations are stored as `[longitude, latitude]`.
PGA is stored in Gal.

Raw samples stay in MongoDB.
Elasticsearch receives metadata only, excluding `raw_data`, `raw_data_unit`, `scale_factor`, and `offset`.
This keeps the search index compact.

## Search Design

MongoDB and Elasticsearch have different strengths.

| Backend | Endpoint | Strengths |
| --- | --- | --- |
| MongoDB | `POST /query` | Simple filters, exact counts when requested, and geospatial queries with `$geoWithin`. |
| Elasticsearch | `POST /search` | Large result sets, deep pagination, aggregations, and case-insensitive regular expressions. |

Elasticsearch maps event and station locations as `geo_point`.
Sortable fields are magnitude, PGA, event time, and depth.
The default order is `-maximum_acceleration`.
See [Search](Search.md) for the full request format.

## Processing Design

Processing is stateless.
The server loads a record, applies the requested configuration, and returns a new response object without writing the result back to MongoDB.
This makes repeated experiments safe and keeps the stored archive immutable.

The processing pipeline can perform the following steps.

1. Convert raw integer samples to floating-point acceleration.
2. Normalize the waveform when requested.
3. Remove leading samples.
4. Optionally upsample, design a windowed FIR filter, and convolve it with the signal.
5. Optionally downsample by decimation.
6. Optionally compute a one-sided FFT amplitude spectrum.
7. Optionally compute response spectra with a linear single-degree-of-freedom oscillator.

See [Processing](Processing.md) for parameters and formulas.

## Storage and Consistency

MongoDB is the source of truth.
Elasticsearch is a derived index.
A successful write therefore requires both operations to finish before search results reflect the new record.
If indexing fails, the record remains available through MongoDB-backed `/query` but may be missing from `/search`.
Re-indexing can be performed through `POST /index` with a raw Elasticsearch bulk body.

The upload cache is required when the API and workers run in separate containers.
`MB_FS_PERSISTENT` keeps cached archives after successful parsing for debugging or replay.
Without it, successful worker uploads are removed from the cache and failed worker uploads stay for retry.

## Deployment Topology

The smallest useful deployment needs MongoDB, Elasticsearch, RabbitMQ, and the backend.
The frontend is needed for the web interface.
A Taskiq worker is optional but strongly recommended for large uploads.

The provided production Compose file runs the following services.

| Service | Role |
| --- | --- |
| `mongo` | Record storage and Taskiq result backend |
| `rabbitmq` | Task broker |
| `elasticsearch` | Search and aggregations |
| `mb-back` | FastAPI backend |
| `mb-front` | Static frontend |
| `mb-worker` | Taskiq worker |
| `seaweedfs` | S3-compatible upload cache |
| `mongo-express` | Optional MongoDB administration UI |

A production nginx variant adds a reverse proxy and scales the backend.
See [Deployment](Deployment.md) for commands, environment variables, and operational hardening.
