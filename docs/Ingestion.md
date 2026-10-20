# Ingesting Records

Records enter `motion-base` through HTTP uploads or through the bundled provider crawlers.
Every archive is parsed into the same internal schema, saved to MongoDB, and indexed in Elasticsearch.

## Supported Sources

| Source | Region | Accepted inputs | Categories |
| --- | --- | --- | --- |
| [NIED / K-NET, KiK-net](https://www.kyoshin.bosai.go.jp/) | Japan | `.tar.gz` archives or loose ASCII waveform files | `knt`, `kik`, or `unknown` |
| [GeoNet / NZSM](https://www.geonet.org.nz/data/types/strong_motion) | New Zealand | `.tar.gz`, `.zip`, or loose waveform files | `processed` or `unprocessed` |

Japan uses the NIED ASCII formats with `.EW`, `.NS`, and `.UD` extensions, including numbered variants such as `.EW1` and `.EW2`.
New Zealand uses `.V1A` and `.V2A` files, including `.BIN` variants.
Nested archives are supported up to ten levels deep.

## Authentication

Uploads require an active user with `can_upload`.
The default superuser is configured through `MB_SUPERUSER_USERNAME` and `MB_SUPERUSER_PASSWORD`.

```bash
BASE=http://localhost:8000
TOKEN=$(curl -s -X POST "$BASE/user/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test&password=password" | jq -r .access_token)
```

Change the default credentials before exposing a deployment to the public.

## Uploading Archives

### Japan

```bash
curl -s -X POST "$BASE/jp/upload?wait_for_result=false&overwrite_existing=true" \
  -H "Authorization: Bearer $TOKEN" \
  -F "archives=@jp_test.knt.tar.gz"
```

NIED archives are gzip-compressed tarballs.
Loose `.EW`, `.NS`, and `.UD` files are also accepted and packed into a tarball by the server.
Zip archives are not supported for Japan uploads.

The parser reads event, station, sampling, direction, scale, and PGA fields from the ASCII header.
Event and record times are interpreted in `Asia/Tokyo`.
Raw samples are stored as integers with the source unit and scale factor.
An offset equal to the negative mean sample value is recorded for later conversion.

The category is inferred from the archive name.
Archives containing `knt` become `knt`, archives containing `kik` become `kik`, and other names become `unknown`.

### New Zealand

```bash
curl -s -X POST "$BASE/nz/upload?wait_for_result=false&overwrite_existing=true" \
  -H "Authorization: Bearer $TOKEN" \
  -F "archives=@nz_test.zip"
```

GeoNet uploads may be zip files, gzip-compressed tarballs, or loose `.V1A` and `.V2A` files.
The parser follows the GeoNet strong-motion file format and supports files containing one or three components.
`V2A` files are categorized as `processed` and `V1A` files as `unprocessed`.

Event and record times are read as New Zealand local time.
Raw data is stored in millimeters per second squared and converted to Gal for search metadata.

### Behavior

Both upload endpoints return `202 Accepted` in both processing modes.

| Mode | Query value | Response |
| --- | --- | --- |
| Background | `wait_for_result=false` | `task_ids` for progress polling |
| Synchronous | `wait_for_result=true` | Parsed record file names |

Background mode is the normal choice.
The API dispatches to a Taskiq worker when one is connected and falls back to an in-process FastAPI background task otherwise.
In-process parsing can occupy the API process for large archives, so run a worker in production.

`overwrite_existing=true` deletes any previously stored record whose SHA-256 content hash matches.
With `false`, the parser skips the hash-based delete; the deterministic record ID still controls whether the saved document replaces an existing one.

## Monitoring Uploads

```bash
curl -s "$BASE/task/status/$TASK_ID"
```

A task reports `total_size` and `current_size`.
Finished tasks are removed when parsing completes, so a `404` response usually means parsing is done.
Bulk indexing into Elasticsearch follows immediately, so `/search` may lag `/query` by a moment.

The Python client provides convenience wrappers.

```python
from mb.client import MBClient

async with MBClient(
    "http://localhost:8000", username="test", password="password"
) as client:
    await client.upload("jp", "data/jp_test.knt.tar.gz")
    await client.status()
```

Client uploads accept a single file, a directory, or a generator of paths.
Directories are walked recursively and files are filtered to `.tar.gz`, `.zip`, and New Zealand waveform extensions.
Use `max_file_size` to skip files larger than a desired size in megabytes.

## Crawling Provider Archives

Two command-line crawlers mirror the source archives before upload.
Both are resumable through state files in the chosen root directory.
Both also ship as standalone Linux binaries in the release artifacts and as `tlcfem/motion-base:crawler`.

### NIED Crawler

```bash
python src/crawler/nied_crawler.py USERNAME PASSWORD \
  --mode all \
  --root ./NIED \
  --parallel 20 \
  --retry 3
```

The NIED crawler requires a registered account because downloads use HTTP basic authentication.
It supports `parse`, `crawl`, and `all` modes.
`parse` mirrors the remote directory tree, and `crawl` downloads the archived waveform files.
The default targets are `kik/data/` and `knet/data/`.
Use `--targets` to limit parsing to specific remote paths.
Use `--dry-run` to print the resolved configuration without downloading, and `--silent` to skip resume prompts.

### GeoNet Crawler

```bash
python src/crawler/nzsm_crawler.py \
  --mode all \
  --root ./NZSM \
  --parallel 20 \
  --retry 3
```

The GeoNet crawler does not need credentials.
It supports `parse`, `crawl`, `all`, and `pack` modes.
`pack` groups downloaded waveform files into zip archives of up to 500 files in an output directory.

```bash
python src/crawler/nzsm_crawler.py --mode pack --root ./NZSM --output ./OUTPUT
```

Use `--targets` to start from specific remote paths such as `2016` or `2007/09_Sep`.

### Crawler Container

```bash
docker run --rm -it -v "$PWD:/data" -w /data \
  tlcfem/motion-base:crawler \
  nied_crawler USERNAME PASSWORD --mode all --root ./NIED
```

The crawler image places both commands on `PATH`.
Replace `nied_crawler` with `nzsm_crawler` for New Zealand.

## Verification

After an upload, verify record counts and inspect a sample.

```bash
curl -s "$BASE/total"
curl -s -X POST "$BASE/query?count_total=true" \
  -H "Content-Type: application/json" \
  -d '{"pagination": {"page_size": 3}}'
```

A successfully indexed record should appear in both `/query` and `/search`.
If it appears only in `/query`, check Elasticsearch connectivity and the worker logs.

## Operational Notes

- The S3-compatible cache must be shared by the API and all workers.
- The frontend build and the API must agree on the public base URL.
- Reverse proxies and CDNs may impose request body limits, so raise them for large archives.
- `MB_FS_PERSISTENT` keeps processed archives for replay or debugging.
- Failed worker jobs are retained in the cache for retry when persistence is disabled.
- Taskiq retries connection and timeout failures automatically.
- Data remains subject to the source provider's license and terms of use.
