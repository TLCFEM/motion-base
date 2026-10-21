# Python Client

`mb.client.MBClient` is an asynchronous client for querying, downloading, and uploading records.
It returns Pydantic record objects that can be processed, plotted, and exported without additional parsing.

The client is not published on PyPI.
Install it from a clone of the repository.

```bash
git clone https://github.com/TLCFEM/motion-base.git
cd motion-base
pip install .[client]
```

The `client` extra adds `httpx2`, `matplotlib`, `rich`, `click`, and `beautifulsoup4`.
The base package requires Python 3.11 or newer.

## Creating a Client

`MBClient` is an async context manager.
Entering the context checks the server's `/alive` endpoint and raises `RuntimeError` when the health check does not return `200`; connection errors propagate from `httpx2`.

```python
import asyncio

from mb.client import MBClient


async def main():
    async with MBClient(
        "https://tlcfem.top/mb/api",
        username="test",
        password="password",
        timeout=20,
        semaphore=10,
    ) as client:
        print(await client.me())


asyncio.run(main())
```

| Argument | Meaning |
| --- | --- |
| `host_url` | API base URL, without a required trailing slash |
| `username` | Username for authenticated operations |
| `password` | Password for authenticated operations |
| `max_file_size` | Maximum upload size in MB, or `0` for no limit |
| `timeout` | Passed to `httpx2.AsyncClient`; the default is no timeout |
| `semaphore` | Maximum concurrent requests, default `10` |

The demo server is intended for demonstrations only.
Use a local or self-hosted deployment for bulk downloads and uploads.

## Querying

`search()` posts a `QueryConfig` to `/query` and returns a list of metadata records.
It returns `None` when the request fails.

```python
from mb.app.response import PaginationConfig, QueryConfig

records = (
    await client.search(
        QueryConfig(
            region="jp",
            min_magnitude=6.0,
            min_pga=200.0,
            pagination=PaginationConfig(
                page_size=50,
                sort_by="-maximum_acceleration",
            ),
        )
    )
    or []
)

for record in records:
    print(record.id, record.file_name, record.maximum_acceleration)
```

The returned records contain metadata only.
They do not contain waveform samples until they are downloaded.

`retrieve_all()` uses the Elasticsearch-backed `/search` endpoint and walks matching records through `search_after` pagination.

```python
query = QueryConfig(
    min_magnitude=7.0,
    pagination=PaginationConfig(page_size=100),
)

async for record in client.retrieve_all(query):
    print(record.id, record.event_time)
```

`retrieve_all()` does not load waveforms either.
When passing a plain dictionary instead of a `QueryConfig`, include a `pagination` object because the method updates `pagination.search_after`.

See [Search](Search.md) for every query field and pagination rule.

## Downloading Waveforms

`download()` accepts a record ID, a UUID, an `MBRecord`, or a list of any of those.
Downloaded records are stored in `client.download_pool` and are available by iterating the client.

```python
await client.download(records)

print(len(client))

for record in client:
    print(record.id, len(record.waveform))
```

A download adds `waveform`, `time_interval`, `raw_data`, `raw_data_unit`, and `offset` to the record.
The client requests acceleration in `cm/s/s`.
The `processed_data_unit` label can mirror the source record's raw unit even though the numeric waveform is converted, so check it before relying on automatic Pint conversion for New Zealand records.

`download()` returns the client, so its pool and counters remain available after each call.
List downloads run concurrently through the client semaphore.

```python
await client.download(records[0])
await client.download(records[1])
```

Clear the pool between unrelated batches.

```python
client.clear()
```

Failed downloads are printed and skipped.
The client does not raise for an individual HTTP failure during a batch download.

## Working With Records

`MBRecord` extends the server's `RecordResponse` model.

| Method or property | Purpose |
| --- | --- |
| `id` | Stable record identifier |
| `waveform` | Floating-point acceleration samples |
| `time_interval` | Sampling interval in seconds |
| `normalise()` | Scale the waveform to a peak absolute value of one |
| `to_spectrum()` | Compute `frequency_interval` and `spectrum` |
| `to_response_spectrum(damping, period)` | Compute displacement, velocity, and acceleration spectra |
| `to_table(unit=None)` | Return time and acceleration arrays |
| `to_table_file(path, unit=None)` | Write a two-column text file |
| `plot_waveform(fig=None)` | Plot the current waveform |
| `plot_spectrum(fig=None)` | Compute and plot the FFT spectrum |
| `plot_response_spectrum(damping_ratio=0.05, period_bracket=...)` | Compute and plot response spectra |

Plot methods return a Matplotlib `Figure` and do not display it.
Call `matplotlib.pyplot.show()` in interactive scripts, or save the figure with `fig.savefig()`.

```python
import matplotlib.pyplot as plt
import numpy as np

record = client.download_pool[0]
record.normalise()
record.to_response_spectrum(0.05, np.arange(0, 5, 0.01))
record.to_table_file("record.txt")

fig = record.plot_waveform()
fig.savefig("record.png")
plt.close(fig)
```

`to_table_file()` writes two whitespace-separated columns with 14 decimal places.
When `unit` is provided, the client uses Pint to convert from `processed_data_unit`; confirm that label matches the numeric unit first.
Normalized records are dimensionless and should not be converted.

`plot_spectrum()` and `plot_response_spectrum()` mutate the record by populating the corresponding arrays.
The arrays stay available after plotting, so they can be exported or compared across records.

## Uploading Records

Uploads require a username and password with upload permission.
The client posts files to `/jp/upload` or `/nz/upload` and, in background mode, records the returned task IDs.

```python
async with MBClient(
    "http://localhost:8000",
    username="test",
    password="password",
    max_file_size=100,
) as client:
    await client.upload("jp", "data/jp_test.knt.tar.gz")
    await client.status()
```

`upload()` accepts a file, a directory, or a generator of paths.
Directories are walked recursively.
Archives ending in `.tar.gz` or `.zip` are included, as are New Zealand `.V1A` and `.V2A` files.
Files larger than `max_file_size` are skipped silently.

`status()` polls every two seconds until all tracked tasks are finished.
A finished task disappears from the API and is removed from the client's task dictionary.

Uploading is asynchronous by default.
In background mode, `upload()` returns after the HTTP upload completes, not after parsing finishes.
Call `status()` to wait for parsing.
The task disappears just before the archive is bulk-indexed, so allow a moment before relying on `/search`.

See [Ingestion](Ingestion.md) for accepted archive layouts and crawler commands.

## Authentication and User Information

The client obtains a bearer token automatically when a username and password are configured.
The token is refreshed shortly before it expires.

`me()` returns the current user profile.

```python
async with MBClient(
    "http://localhost:8000",
    username="test",
    password="password",
) as client:
    user = await client.me()
    print(user["username"], user["email"])
```

Without credentials, public operations such as search, download, and jackpot still work.
Server-side `/process` is public too, but the client does not wrap that endpoint.
Uploads fail with a message instead of raising when credentials are missing.

## Random Records

`jackpot()` retrieves one random waveform from `/waveform/jackpot`.

```python
record = await client.jackpot()
if record is not None:
    record.plot_waveform()
```

This is useful for smoke tests and demos.
It returns `None` when the server cannot provide a record.

## Error Handling

The client favors simple return values for read operations and exceptions for transport-level failures.

| Situation | Behavior |
| --- | --- |
| Health check returns a non-`200` status | Raises `RuntimeError` |
| Connection or transport failure | Propagates an `httpx2` exception |
| Search returns a non-`200` status | Prints a message and returns `None` |
| Jackpot returns a non-`200` status | Prints a message and returns `None` |
| Individual batch download returns a non-`200` status | Prints a message and skips the record |
| Upload returns a non-`202` status | Raises `RuntimeError` |
| `me()` returns a non-`200` status | Raises `RuntimeError` |

Use a finite `timeout` for production automation so a stalled connection cannot block a job indefinitely.

## Concurrency

The client uses an `anyio` semaphore to limit in-flight requests.
Set `semaphore` according to the capacity of the server and the network.

List downloads, directory uploads, and generator uploads create task groups and inherit the semaphore.
Large batches are therefore concurrent but bounded.

`retrieve_all()` is sequential by design because each page depends on the previous `search_after` cursor.
Parallelize work across independent queries or consumers when throughput matters.

## Executable Notebook

The [client notebook](client.ipynb) walks through creation, querying, downloading, plotting, and local processing with saved outputs.
It uses the public demo server and is a good starting point for interactive exploration.
The notebook can be run from the repository after installing the client extra.

For endpoint-level details, see the [API Reference](API.md).
For filtering and response-spectrum details, see [Processing](Processing.md).
