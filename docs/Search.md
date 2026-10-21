# Searching Records

`motion-base` offers two search endpoints over the same metadata schema.
Use `/query` for ordinary MongoDB queries and `/search` for large result sets and deep pagination.

| Endpoint | Backend | Pagination | Total count |
| --- | --- | --- | --- |
| `POST /query` | MongoDB | `page_number` offset | Only with `count_total=true` |
| `POST /search` | Elasticsearch | Offset below 10,000 or `search_after` | Always returned |

Both endpoints accept a `QueryConfig` JSON object.
Both return metadata only, without waveform samples.

## Query Fields

All fields are optional.
Omitted fields do not restrict the result.

| Field | Type | Meaning |
| --- | --- | --- |
| `region` | `"jp"` or `"nz"` | Restrict to one source region |
| `min_magnitude` | number | Minimum event magnitude, from 0 to 10 |
| `max_magnitude` | number | Maximum event magnitude, from 0 to 10 |
| `category` | string | Source category such as `knt`, `kik`, `processed`, or `unprocessed` |
| `event_location` | `[longitude, latitude]` | Center point for event-distance filtering |
| `station_location` | `[longitude, latitude]` | Center point for station-distance filtering |
| `max_event_distance` | number | Event search radius in meters |
| `max_station_distance` | number | Station search radius in meters |
| `from_date` | ISO 8601 datetime | Earliest event time, inclusive |
| `to_date` | ISO 8601 datetime | Latest event time, inclusive |
| `min_pga` | number | Minimum peak ground acceleration in Gal |
| `max_pga` | number | Maximum peak ground acceleration in Gal |
| `file_name` | string | Case-insensitive regular expression on the source file name |
| `station_code` | string | Case-insensitive regular expression on the station code |
| `direction` | string | Case-insensitive regular expression on the component direction |
| `pagination` | object | Pagination and sorting options |

`event_location` and `station_location` are geographic points in longitude-latitude order.
When a location is present without a distance, the radius defaults to `100000` meters.
`from_date` and `to_date` apply to `event_time`, not to upload time.

`file_name`, `station_code`, and `direction` are regular expressions, not literal strings.
Escape regex characters when matching a literal name such as `2016.05`.
Invalid expressions can cause the request to fail.

## Pagination

Pagination is nested under `pagination`.

| Field | Default | Meaning |
| --- | --- | --- |
| `page_size` | `10` | Number of records per page, from 1 to 1000 |
| `page_number` | `0` | Zero-based page index |
| `sort_by` | `-maximum_acceleration` | Sort expression with a mandatory `+` or `-` prefix |
| `search_after` | `null` | Cursor returned by `/search` for the next page |

The supported sort fields are:

- `magnitude`
- `maximum_acceleration`
- `event_time`
- `depth`

A `+` prefix sorts ascending and a `-` prefix sorts descending.
The field name is case-insensitive and is normalized to lowercase.
A value without a prefix is rejected.

`search_after` is only used by `/search`.
When it is present, `/search` ignores `page_number` and continues from the cursor.
Pass the previous response's `search_after` unchanged.
Keep the same filters and the same `sort_by` while walking a cursor, because the cursor encodes the previous sort position.

## Basic Query

```bash
BASE=http://localhost:8000

curl -s -X POST "$BASE/query?count_total=true" \
  -H "Content-Type: application/json" \
  -d '{
    "region": "jp",
    "min_magnitude": 6.0,
    "min_pga": 200.0,
    "from_date": "2011-01-01T00:00:00Z",
    "to_date": "2011-12-31T23:59:59Z",
    "category": "knt",
    "pagination": {
      "page_size": 50,
      "page_number": 0,
      "sort_by": "-maximum_acceleration"
    }
  }'
```

The same body works with `/search`.

```bash
curl -s -X POST "$BASE/search" \
  -H "Content-Type: application/json" \
  -d '{
    "region": "nz",
    "min_pga": 100.0,
    "pagination": {
      "page_size": 100,
      "sort_by": "+event_time"
    }
  }'
```

An empty object returns the first page of all records.

```bash
curl -s -X POST "$BASE/query" \
  -H "Content-Type: application/json" \
  -d '{}'
```

## Geographic Search

Use `event_location` to find events near a point.

```json
{
  "event_location": [141.0, 38.0],
  "max_event_distance": 200000,
  "min_magnitude": 6.0
}
```

Use `station_location` to find stations near a point.

```json
{
  "station_location": [139.7, 35.7],
  "max_station_distance": 50000,
  "min_pga": 50.0
}
```

Both filters can be combined.
Each filter applies independently to its own location field.

## Regular Expression Search

```json
{
  "station_code": "^(MYG|WAK)",
  "direction": "^(EW|NS)$",
  "file_name": "2011"
}
```

All three patterns are matched case-insensitively.
`/query` uses MongoDB regular expressions and `/search` uses Elasticsearch regular expressions.
Elasticsearch text fields are analyzed, so `/search` patterns match indexed tokens rather than necessarily the full raw string.
Their syntax is similar but not identical.

## Response Shape

Both endpoints return a `records` list and a `pagination` object.

```json
{
  "records": [
    {
      "endpoint": "/search",
      "id": "d7348417-57b8-5f9f-bb88-aaf8f54c2ba4",
      "file_name": "20161113_110259_WTMC_20.V2A",
      "category": "processed",
      "region": "nz",
      "magnitude": 7.8,
      "maximum_acceleration": 123.4,
      "event_time": "2016-11-13T11:02:59",
      "event_location": [173.02, -42.69],
      "depth": 15.0,
      "station_code": "WTMC",
      "station_location": [172.62, -41.72],
      "direction": "NS",
      "sampling_frequency": 100.0,
      "duration": 120.0
    }
  ],
  "pagination": {
    "page_size": 10,
    "page_number": 0,
    "sort_by": "-maximum_acceleration",
    "search_after": [123.4],
    "total": 187846
  }
}
```

The `endpoint` field is set to `/search` for Elasticsearch results and is `null` for `/query` results.
The `search_after` value is opaque and should be treated as a cursor.
It is `null` when the current `/search` response contains no hits.

## Totals

`/query` sets `total` to zero unless `count_total=true`.
Counting is optional because geospatial counts can be expensive.
`/search` always returns an exact total through `track_total_hits`.

The total is useful for progress indicators and collection statistics.
Do not use the total to drive offset pagination without considering the offset limit.

## Deep Pagination

Use `/search` with `search_after` for results beyond the first 10,000 matches.

1. Send the first request without `search_after`.
2. Read `pagination.search_after` from the response.
3. Send the next request with the same query and `pagination.search_after` set to that value.
4. Repeat until the response contains no records or `search_after` is `null`.

Example first request:

```json
{
  "min_magnitude": 5.0,
  "pagination": {
    "page_size": 100,
    "sort_by": "-event_time"
  }
}
```

Example next request:

```json
{
  "min_magnitude": 5.0,
  "pagination": {
    "page_size": 100,
    "sort_by": "-event_time",
    "search_after": [1719273600000]
  }
}
```

The cursor values correspond to the sort fields.
Do not edit them or change the sort order between pages.
The cursor currently follows one selected sort field, so records with identical sort values may not have a stable order across pages.
Narrow the query or choose a field with fewer ties when exact traversal completeness matters.

`/query` has no cursor support and will accept larger offsets, but MongoDB must scan the skipped documents.
Prefer `/search` for collection-wide traversal.

`/search` without `search_after` clamps the offset below 10,000.
For the default page size of 10, the largest effective page number is 999.
With a page size of 100, the largest effective page number is 99.
Use `search_after` when a larger offset is required.

## Python Client

`MBClient.search()` uses `/query`.

```python
from mb.app.response import PaginationConfig, QueryConfig
from mb.client import MBClient


async with MBClient("https://tlcfem.top/mb/api") as client:
    records = (
        await client.search(
            QueryConfig(
                min_magnitude=6.0,
                min_pga=200.0,
                pagination=PaginationConfig(
                    page_size=20,
                    sort_by="-maximum_acceleration",
                ),
            )
        )
        or []
    )

    for record in records:
        print(record.id, record.file_name)
```

`MBClient.retrieve_all()` uses `/search` and handles the cursor automatically.

```python
query = QueryConfig(
    region="jp",
    min_magnitude=7.0,
    pagination=PaginationConfig(page_size=100, sort_by="-event_time"),
)

async for record in client.retrieve_all(query):
    print(record.id, record.event_time)
```

`retrieve_all()` is an async generator and fetches one page at a time.
It does not stop at the 10,000 offset limit because it uses `search_after`.

## Statistics

`GET /stats` returns Elasticsearch aggregations for magnitude, PGA, and event year.
Use it for dashboards and collection summaries rather than fetching every record.
See the [API Reference](API.md) for the response shape.

## Practical Notes

- Metadata records do not include waveform arrays, so searching is cheap.
- Download waveforms separately with `/waveform` or `MBClient.download()`.
- Use `min_pga` and `max_pga` in Gal, not in `g` or `m/s²`.
- Use meters for distance fields, even though metadata reports depth in kilometers.
- Use timezone-aware timestamps to avoid off-by-hours date filters.
- Keep regex filters anchored and specific when the collection is large.
- Use `/search` when a query must traverse the entire collection.
- Use `/query` when a simple exact count or MongoDB-specific behavior is needed.

For processing selected records, see [Processing](Processing.md).
For Python download and plotting examples, see the [Python Client](PythonClient.md).
