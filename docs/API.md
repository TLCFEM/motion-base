# API Reference

The backend is a FastAPI application and exposes JSON endpoints under a configurable base URL.
The public demo uses `https://tlcfem.top/mb/api`.
A local development server defaults to `http://localhost:8000`.
Interactive OpenAPI documentation is served at `/docs` relative to the base URL.

Most read endpoints are public.
Uploads, indexing, deletions, and user administration require a bearer token.
The default superuser is created from the `MB_SUPERUSER_*` environment variables.

## Authentication

Request a token with form-encoded credentials.

```bash
BASE=https://tlcfem.top/mb/api
TOKEN=$(curl -s -X POST "$BASE/user/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test&password=password" | jq -r .access_token)
```

Send the token as `Authorization: Bearer $TOKEN` on protected endpoints.
Tokens expire after `MB_ACCESS_TOKEN_EXPIRE_MINUTES`, which defaults to 120 in the Compose environment.

## Endpoint Summary

| Method | Path | Authentication | Purpose |
| --- | --- | --- | --- |
| `GET` | `/alive` | Public | Health check |
| `GET` | `/` | Public | Redirect to OpenAPI documentation |
| `GET` | `/total` | Public | Count all records |
| `POST` | `/total` | Public | Count records for one or more query configurations |
| `GET` | `/stats` | Public | Elasticsearch aggregations for magnitude, PGA, and year |
| `POST` | `/query` | Public | MongoDB-backed metadata query |
| `POST` | `/search` | Public | Elasticsearch-backed metadata query |
| `POST` | `/waveform` | Public | Download waveforms by record ID |
| `GET` | `/raw/jackpot` | Public | Download a random raw record |
| `GET` | `/waveform/jackpot` | Public | Download a random waveform |
| `GET` | `/spectrum/jackpot` | Public | Download a random FFT spectrum |
| `POST` | `/process` | Public | Apply processing to one record |
| `DELETE` | `/purge` | `can_delete` | Preview or delete records selected by a query |
| `POST` | `/index` | `can_upload` | Send a raw bulk request to Elasticsearch |
| `POST` | `/jp/upload` | `can_upload` | Upload Japanese archives |
| `POST` | `/nz/upload` | `can_upload` | Upload New Zealand archives |
| `GET` | `/task/status/{task_id}` | Public | Read one upload task |
| `POST` | `/task/status` | Public | Read several upload tasks |
| `POST` | `/user/token` | Public | Acquire an access token |
| `GET` | `/user/whoami` | Active user | Read the current user |
| `POST` | `/user/check` | Public | Check whether a username and email are available |
| `POST` | `/user/new` | Admin | Create a user |
| `DELETE` | `/user/{user_id}` | Admin | Delete a user |
| `POST` | `/turnstile` | Public | Validate a Cloudflare Turnstile token |

Admin means the user has both `can_upload` and `can_delete`.

## Status and Counts

### `GET /alive`

Returns a small liveness response.

```json
{"message": "I'm alive!"}
```

### `GET /total`

Returns the total number of records.

```json
{"total": [187846]}
```

### `POST /total`

Accepts one `QueryConfig` or a list of `QueryConfig` objects.
The response contains one count per configuration.

```bash
curl -s -X POST "$BASE/total" \
  -H "Content-Type: application/json" \
  -d '[{"min_magnitude": 6}, {"min_pga": 100}]'
```

```json
{"total": [52341, 84210]}
```

### `GET /stats`

Returns Elasticsearch histograms for magnitude, PGA, and event year.
The aggregation only includes records with magnitude between 1 and 10.
The response follows the raw Elasticsearch aggregation shape.

```json
{
  "magnitude": {"buckets": [{"key": 6.0, "doc_count": 1234}]},
  "pga": {"buckets": [{"key": 100.0, "doc_count": 5678}]},
  "year": {"buckets": [{"key_as_string": "2011-01-01T00:00:00.000Z", "doc_count": 9012}]}
}
```

## Searching Records

### `POST /query`

Queries MongoDB and returns metadata with offset pagination.
The optional `count_total=true` query parameter computes an exact total and may be expensive for geospatial queries.
MongoDB results return a `null` `endpoint` field.

### `POST /search`

Queries Elasticsearch and returns metadata with `search_after` pagination.
It always returns the total hit count and a cursor for the next page.
Use this endpoint for deep or large result sets.

Both endpoints accept the same `QueryConfig` body.
See [Search](Search.md) for all fields, defaults, pagination rules, and examples.

### Metadata Shape

A metadata record contains the following fields when present.

| Field | Meaning |
| --- | --- |
| `id` | Stable record identifier |
| `file_name` | Original source file name |
| `category` | Source category such as `knt`, `kik`, `processed`, or `unprocessed` |
| `region` | `jp` or `nz` |
| `uploaded_by` | User ID that uploaded the record |
| `magnitude` | Event magnitude |
| `maximum_acceleration` | Peak ground acceleration in Gal |
| `event_time` | Event origin time |
| `event_location` | Event location as `[longitude, latitude]` |
| `depth` | Event depth in kilometers |
| `station_code` | Station identifier |
| `station_location` | Station location as `[longitude, latitude]` |
| `station_elevation` | Station elevation |
| `station_elevation_unit` | Unit of station elevation |
| `record_time` | Time the record was recorded |
| `last_update_time` | Provider update time |
| `sampling_frequency` | Sampling frequency |
| `sampling_frequency_unit` | Unit of sampling frequency |
| `duration` | Record duration in seconds |
| `direction` | Component direction such as `EW`, `NS`, `UD`, or `UP` |
| `scale_factor` | Raw sample scale factor when available |
| `endpoint` | Endpoint that produced the response, set by waveform and search responses when available |

## Downloading Waveforms

### `POST /waveform`

Accepts one record ID or a list of record IDs.
The response contains records with raw samples, floating-point waveforms, and a time interval.

```bash
curl -s -X POST "$BASE/waveform" \
  -H "Content-Type: application/json" \
  -d '["d7348417-57b8-5f9f-bb88-aaf8f54c2ba4"]'
```

```json
{
  "records": [
    {
      "id": "d7348417-57b8-5f9f-bb88-aaf8f54c2ba4",
      "file_name": "20161113_110259_WTMC_20.V2A",
      "endpoint": "/waveform",
      "raw_data": [0, 0, 0],
      "raw_data_unit": "millimeter / second ** 2",
      "processed_data_unit": "millimeter / second ** 2",
      "time_interval": 0.005,
      "waveform": [0.0, 0.0, 0.0]
    }
  ]
}
```

Waveforms are converted to `cm/s/s` before transmission.
The `processed_data_unit` label can reflect the source record's raw unit, so treat the numeric `waveform` values as `cm/s/s`.
Use `raw_data_unit` for the original sample unit and `time_interval` to reconstruct the time axis.

### Jackpot Endpoints

| Endpoint | Response |
| --- | --- |
| `GET /raw/jackpot` | One random record including integer samples |
| `GET /waveform/jackpot?normalised=false` | One random floating-point waveform |
| `GET /spectrum/jackpot` | One random one-sided FFT spectrum |

These endpoints are useful for demos, smoke tests, and random sampling.
They return `204 No Content` when the database is empty.

## Processing Records

### `POST /process`

Applies a `ProcessConfig` body to the record identified by the `record_id` query parameter.
Processing is stateless and does not modify the stored record.

```bash
curl -s -X POST "$BASE/process?record_id=d7348417-57b8-5f9f-bb88-aaf8f54c2ba4" \
  -H "Content-Type: application/json" \
  -d '{"with_filter": true, "with_spectrum": true, "with_response_spectrum": true}'
```

The response extends the waveform shape with `process_config`, `spectrum`, `period`, `displacement_spectrum`, `velocity_spectrum`, and `acceleration_spectrum` as requested.
A `400` response is returned when the cutoff frequencies are invalid.
A `404` response is returned when the record does not exist.
See [Processing](Processing.md) for parameter semantics and pipeline order.

## Uploading Records

### `POST /jp/upload` and `POST /nz/upload`

Both endpoints accept multipart form data with one or more `archives` fields.
Both require an authenticated user with `can_upload`.

| Query parameter | Default | Meaning |
| --- | --- | --- |
| `wait_for_result` | `false` | Parse synchronously and return record names instead of task IDs |
| `overwrite_existing` | `true` | Replace records whose content hash already exists |

Both endpoints return `202 Accepted`.
When `wait_for_result=false`, the response contains `task_ids` for progress polling.
When `wait_for_result=true`, the response contains the parsed record file names and no task IDs.
See [Ingestion](Ingestion.md) for accepted formats and complete examples.

### `GET /task/status/{task_id}`

Returns progress for one upload task.

```json
{
  "id": "2f4311c5-7d55-4e11-9d18-3f78b8080f4e",
  "create_time": "2026-10-20T10:35:00",
  "total_size": 120,
  "current_size": 45
}
```

Progress is `current_size / total_size`.
A finished task is deleted, so a `404` response usually means parsing completed or the task never existed.

### `POST /task/status`

Accepts a JSON list of task IDs and returns a `tasks` list in the same order.
Finished or unknown tasks appear as `null`.

```json
{"tasks": [{"id": "2f4311c5-7d55-4e11-9d18-3f78b8080f4e", "create_time": "2026-10-20T10:35:00", "total_size": 120, "current_size": 45}, null]}
```

## Administration

### `DELETE /purge`

Selects records with a `QueryConfig` body and requires `can_delete`.
With `confirm=false`, it returns the matching Elasticsearch result without deleting anything.
With `confirm=true`, it deletes the matching documents from Elasticsearch and MongoDB.

> Treat `confirm=false` as a preview and inspect the selection carefully before running the destructive form.

### `POST /index`

Sends a raw Elasticsearch bulk body for the `record` index.
The request body must contain a `records` list with alternating action and document entries.
This endpoint requires `can_upload` and is intended for maintenance and re-indexing.

```json
{"records": [{"index": {"_id": "record-id"}}, {"id": "record-id", "magnitude": 7.0}]}
```

## Users

| Endpoint | Body or form | Notes |
| --- | --- | --- |
| `POST /user/token` | `username`, `password` | Returns `access_token` and `token_type` |
| `GET /user/whoami` | None | Returns the active user profile |
| `POST /user/check` | `username`, `email` | Returns `409` if either is already registered |
| `POST /user/new` | `username`, `email`, `password`, `first_name`, `last_name` | Admin only |
| `DELETE /user/{user_id}` | None | Admin only |

Passwords must contain at least eight characters with an uppercase letter, a lowercase letter, a number, and a special character.
New users receive both upload and delete permissions by default.

## Miscellaneous

### `POST /turnstile`

Accepts a form field named `turnstile_token` and validates it with Cloudflare.
The endpoint returns `500` when `TURNSTILE_SECRET` is not configured.

## Errors

The API uses standard HTTP status codes.

| Code | Typical cause |
| --- | --- |
| `400` | Invalid processing cutoff, inactive user, or invalid request |
| `401` | Missing, expired, or invalid bearer token |
| `404` | Record or task not found |
| `409` | Username or email already exists |
| `422` | Request validation failure |

Validation errors follow the FastAPI error shape with a `detail` list.
