# Search For Records

## API

Two APIs are available for record filtering:

1. `POST /query`: MongoDB-backed query endpoint.
2. `POST /search`: Elasticsearch-backed query endpoint.

`/query` is suitable for normal filtering and simple pagination.
`/search` is recommended for large result sets and deep pagination (`search_after`).

Search criteria are provided as a JSON request body (`QueryConfig`).

## Query Fields

### `region`

Query a specific region (`jp` or `nz`).
If not specified, records from all regions are considered.

### `min_magnitude` and `max_magnitude`

Minimum and maximum event magnitude.

### `category`

Database/category label (for example, `knt` or `kik` for some JP records).

### `event_location` and `station_location`

Geographic location expressed as `[longitude, latitude]`.
When provided, location filtering is combined with maximum distance constraints.

### `max_event_distance` and `max_station_distance`

Maximum allowed distance (meters) from `event_location` or `station_location`.
If omitted while location is provided, each field defaults to `100000` meters (`max_event_distance` for event filtering, `max_station_distance` for station filtering).
This default is implemented in `QueryConfig.generate_query_string()` and `QueryConfig.generate_elastic_query()`.

### `from_date` and `to_date`

Start and end timestamps for event time filtering.

### `min_pga` and `max_pga`

Minimum and maximum PGA (`maximum_acceleration`).

### `file_name`

Case-insensitive pattern match on the original record file name from the source dataset/provider.

### `station_code`

Case-insensitive pattern match on station code.

### `direction`

Case-insensitive pattern match on record direction.

## Pagination

Pagination options are grouped under `pagination` in the request body.

### `pagination.page_size`

Number of records per page. Default: `10`.

### `pagination.page_number`

Zero-based page index. Default: `0`.

### `pagination.sort_by`

Sort expression with sign prefix (`+` ascending, `-` descending).
Supported fields:

- `magnitude`
- `maximum_acceleration`
- `event_time`
- `depth`

Default: `-maximum_acceleration`.

### `pagination.search_after`

Cursor-based pagination token used by `/search`.
When present, `/search` continues from that cursor instead of using `page_number`.

## Notes

- `/query` supports optional `count_total` (query parameter) to return exact total count, which may be expensive for some geo queries.
- `/search` always returns total hits from Elasticsearch together with `search_after` for the next page.
