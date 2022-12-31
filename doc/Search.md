# Search For Records

## API

The search functionality fully relies on the MongoDB query. An API named as `/query` is provided.

Search criteria can be provided as either query parameters or as a JSON object in the request body. An example will
be provided in the following section.

## Query Parameters

### `region`

Query a specific region, e.g., `region=jp`. If not specified, all regions will be queried, and results will be merged.

### `min_magnitude` and `max_magnitude`

The minimum and maximum magnitude of the records of interest.

### `category`

The category of the records of interest. Some databases have categories. The Japanese database NIED, for
example, has two categories: `knt` and `kik`. In this case, `category=knt` will query the records of the KNT
network.

### `event_location` and `station_location`

The geographic locations of the event and the station. The location needs to be specified in the form of a list of
two floats, e.g., `event_location=-122.0&event_location=38.0`. The first float is the longitude, and the second
float is the latitude.

The records returned will be the ones that are closer to the specified location, ordered by the distance.

### `max_event_distance` and `max_station_distance`

If one wants to find all the records that are within a certain distance from the event, this parameter can be used.

### `from_date` and `to_date`

The start and end time of the records of interest. These can be used to find a specific earthquake event.

### `min_pga` and `max_pga`

The minimum and maximum magnitude of the records of interest.

### `event_name`

### `direction`

### `page_size`

Use for pagination. The default value is 10.

### `page_number`

Use for pagination. The default value is 0.
