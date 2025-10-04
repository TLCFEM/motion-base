# The Client

The web interface presents a nice and simple way to browse records.
But it is not convenient for programmatic usage.

A Python client is also provided to interact with the server.

Currently, the package is not published to PyPI.
To use the client, one shall clone the repository and install the package locally.

```bash
git clone https://github.com/TLCFEM/motion-base.git
cd motion-base
pip install .[client]
```

Then one can import the client and start using it.

## Creation

The client is designed in an asynchronous way, using the `aiohttp` library.
One shall use the context manager to create a client.

Additional parameters may include:

1. `timeout(float)` - request timeout
2. `semaphore(int)` - number of concurrent requests

```python
async with MBClient('http://localhost:8000', timeout=20, semaphore=10) as client:
    # do something with the client
    ...
```

Here we use the [demo](https://tlcfem.top/mb/) server for demonstration.
Please note that this server is only for demonstration purposes and the performance is expected to be poor.
Thus, it is not recommended to use it for massive data processing.


```python
from rich.pretty import pprint

from mb.client import MBClient

server_url = "https://tlcfem.top:8443"
```


## Query

To query the server, one shall use the `search` method.
The method accepts a query configuration object.
The configuration(s) are `pydantic` models.
For example, to search for 100 records with PGA no less than 200 Gal, one can do the following.


```python
from mb.app.response import PaginationConfig, QueryConfig

async with MBClient(server_url, timeout=20, semaphore=10) as client:
    results = await client.search(
        QueryConfig(min_pga=200, pagination=PaginationConfig(page_size=100))
    )
    pprint(f"Find {len(results)} records. The first one contains looks like this.")
    pprint(results[0])
```


<pre style="white-space:pre;overflow-x:auto;line-height:normal;font-family:Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace"><span style="color: #008000; text-decoration-color: #008000">'Find 100 records. The first one contains looks like this.'</span>
</pre>




<pre style="white-space:pre;overflow-x:auto;line-height:normal;font-family:Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace"><span style="color: #800080; text-decoration-color: #800080; font-weight: bold">MBRecord</span><span style="font-weight: bold">(</span>
<span style="color: #7fbf7f; text-decoration-color: #7fbf7f">│   </span><span style="color: #808000; text-decoration-color: #808000">endpoint</span>=<span style="color: #008000; text-decoration-color: #008000">'/query'</span>,
<span style="color: #7fbf7f; text-decoration-color: #7fbf7f">│   </span><span style="color: #808000; text-decoration-color: #808000">id</span>=<span style="color: #008000; text-decoration-color: #008000">'d7348417-57b8-5f9f-bb88-aaf8f54c2ba4'</span>,
<span style="color: #7fbf7f; text-decoration-color: #7fbf7f">│   </span><span style="color: #808000; text-decoration-color: #808000">file_name</span>=<span style="color: #008000; text-decoration-color: #008000">'20161113_110259_WTMC_20.V2A'</span>,
<span style="color: #7fbf7f; text-decoration-color: #7fbf7f">│   </span><span style="color: #808000; text-decoration-color: #808000">category</span>=<span style="color: #008000; text-decoration-color: #008000">'processed'</span>,
<span style="color: #7fbf7f; text-decoration-color: #7fbf7f">│   </span><span style="color: #808000; text-decoration-color: #808000">region</span>=<span style="color: #008000; text-decoration-color: #008000">'nz'</span>,
<span style="color: #7fbf7f; text-decoration-color: #7fbf7f">│   </span><span style="color: #808000; text-decoration-color: #808000">uploaded_by</span>=<span style="color: #008000; text-decoration-color: #008000">'d41eadf4-5770-5e2f-874f-0f18f543fd73'</span>,
<span style="color: #7fbf7f; text-decoration-color: #7fbf7f">│   </span><span style="color: #808000; text-decoration-color: #808000">magnitude</span>=<span style="color: #008080; text-decoration-color: #008080; font-weight: bold">7.53</span>,
<span style="color: #7fbf7f; text-decoration-color: #7fbf7f">│   </span><span style="color: #808000; text-decoration-color: #808000">maximum_acceleration</span>=<span style="color: #008080; text-decoration-color: #008080; font-weight: bold">2969.75</span>,
<span style="color: #7fbf7f; text-decoration-color: #7fbf7f">│   </span><span style="color: #808000; text-decoration-color: #808000">event_time</span>=<span style="color: #800080; text-decoration-color: #800080; font-weight: bold">datetime</span><span style="color: #800080; text-decoration-color: #800080; font-weight: bold">.datetime</span><span style="font-weight: bold">(</span><span style="color: #008080; text-decoration-color: #008080; font-weight: bold">2016</span>, <span style="color: #008080; text-decoration-color: #008080; font-weight: bold">11</span>, <span style="color: #008080; text-decoration-color: #008080; font-weight: bold">13</span>, <span style="color: #008080; text-decoration-color: #008080; font-weight: bold">11</span>, <span style="color: #008080; text-decoration-color: #008080; font-weight: bold">2</span>, <span style="color: #008080; text-decoration-color: #008080; font-weight: bold">56</span><span style="font-weight: bold">)</span>,
<span style="color: #7fbf7f; text-decoration-color: #7fbf7f">│   </span><span style="color: #808000; text-decoration-color: #808000">event_location</span>=<span style="font-weight: bold">[</span><span style="color: #008080; text-decoration-color: #008080; font-weight: bold">173.02</span>, <span style="color: #008080; text-decoration-color: #008080; font-weight: bold">-42.69</span><span style="font-weight: bold">]</span>,
<span style="color: #7fbf7f; text-decoration-color: #7fbf7f">│   </span><span style="color: #808000; text-decoration-color: #808000">depth</span>=<span style="color: #008080; text-decoration-color: #008080; font-weight: bold">15.0</span>,
<span style="color: #7fbf7f; text-decoration-color: #7fbf7f">│   </span><span style="color: #808000; text-decoration-color: #808000">station_code</span>=<span style="color: #008000; text-decoration-color: #008000">'WTMC'</span>,
<span style="color: #7fbf7f; text-decoration-color: #7fbf7f">│   </span><span style="color: #808000; text-decoration-color: #808000">station_location</span>=<span style="font-weight: bold">[</span><span style="color: #008080; text-decoration-color: #008080; font-weight: bold">173.054</span>, <span style="color: #008080; text-decoration-color: #008080; font-weight: bold">-42.619</span><span style="font-weight: bold">]</span>,
<span style="color: #7fbf7f; text-decoration-color: #7fbf7f">│   </span><span style="color: #808000; text-decoration-color: #808000">station_elevation</span>=<span style="color: #800080; text-decoration-color: #800080; font-style: italic">None</span>,
<span style="color: #7fbf7f; text-decoration-color: #7fbf7f">│   </span><span style="color: #808000; text-decoration-color: #808000">station_elevation_unit</span>=<span style="color: #800080; text-decoration-color: #800080; font-style: italic">None</span>,
<span style="color: #7fbf7f; text-decoration-color: #7fbf7f">│   </span><span style="color: #808000; text-decoration-color: #808000">record_time</span>=<span style="color: #800080; text-decoration-color: #800080; font-weight: bold">datetime</span><span style="color: #800080; text-decoration-color: #800080; font-weight: bold">.datetime</span><span style="font-weight: bold">(</span><span style="color: #008080; text-decoration-color: #008080; font-weight: bold">2016</span>, <span style="color: #008080; text-decoration-color: #008080; font-weight: bold">11</span>, <span style="color: #008080; text-decoration-color: #008080; font-weight: bold">13</span>, <span style="color: #008080; text-decoration-color: #008080; font-weight: bold">11</span>, <span style="color: #008080; text-decoration-color: #008080; font-weight: bold">2</span>, <span style="color: #008080; text-decoration-color: #008080; font-weight: bold">19</span><span style="font-weight: bold">)</span>,
<span style="color: #7fbf7f; text-decoration-color: #7fbf7f">│   </span><span style="color: #808000; text-decoration-color: #808000">last_update_time</span>=<span style="color: #800080; text-decoration-color: #800080; font-weight: bold">datetime</span><span style="color: #800080; text-decoration-color: #800080; font-weight: bold">.datetime</span><span style="font-weight: bold">(</span><span style="color: #008080; text-decoration-color: #008080; font-weight: bold">2017</span>, <span style="color: #008080; text-decoration-color: #008080; font-weight: bold">1</span>, <span style="color: #008080; text-decoration-color: #008080; font-weight: bold">20</span>, <span style="color: #008080; text-decoration-color: #008080; font-weight: bold">11</span>, <span style="color: #008080; text-decoration-color: #008080; font-weight: bold">0</span><span style="font-weight: bold">)</span>,
<span style="color: #7fbf7f; text-decoration-color: #7fbf7f">│   </span><span style="color: #808000; text-decoration-color: #808000">sampling_frequency</span>=<span style="color: #008080; text-decoration-color: #008080; font-weight: bold">200.0</span>,
<span style="color: #7fbf7f; text-decoration-color: #7fbf7f">│   </span><span style="color: #808000; text-decoration-color: #808000">sampling_frequency_unit</span>=<span style="color: #008000; text-decoration-color: #008000">'hertz'</span>,
<span style="color: #7fbf7f; text-decoration-color: #7fbf7f">│   </span><span style="color: #808000; text-decoration-color: #808000">duration</span>=<span style="color: #008080; text-decoration-color: #008080; font-weight: bold">209.99</span>,
<span style="color: #7fbf7f; text-decoration-color: #7fbf7f">│   </span><span style="color: #808000; text-decoration-color: #808000">direction</span>=<span style="color: #008000; text-decoration-color: #008000">'UP'</span>,
<span style="color: #7fbf7f; text-decoration-color: #7fbf7f">│   </span><span style="color: #808000; text-decoration-color: #808000">scale_factor</span>=<span style="color: #008080; text-decoration-color: #008080; font-weight: bold">1e-05</span>,
<span style="color: #7fbf7f; text-decoration-color: #7fbf7f">│   </span><span style="color: #808000; text-decoration-color: #808000">raw_data</span>=<span style="color: #800080; text-decoration-color: #800080; font-style: italic">None</span>,
<span style="color: #7fbf7f; text-decoration-color: #7fbf7f">│   </span><span style="color: #808000; text-decoration-color: #808000">raw_data_unit</span>=<span style="color: #800080; text-decoration-color: #800080; font-style: italic">None</span>,
<span style="color: #7fbf7f; text-decoration-color: #7fbf7f">│   </span><span style="color: #808000; text-decoration-color: #808000">offset</span>=<span style="color: #800080; text-decoration-color: #800080; font-style: italic">None</span>,
<span style="color: #7fbf7f; text-decoration-color: #7fbf7f">│   </span><span style="color: #808000; text-decoration-color: #808000">processed_data_unit</span>=<span style="color: #800080; text-decoration-color: #800080; font-style: italic">None</span>,
<span style="color: #7fbf7f; text-decoration-color: #7fbf7f">│   </span><span style="color: #808000; text-decoration-color: #808000">time_interval</span>=<span style="color: #800080; text-decoration-color: #800080; font-style: italic">None</span>,
<span style="color: #7fbf7f; text-decoration-color: #7fbf7f">│   </span><span style="color: #808000; text-decoration-color: #808000">waveform</span>=<span style="color: #800080; text-decoration-color: #800080; font-style: italic">None</span>,
<span style="color: #7fbf7f; text-decoration-color: #7fbf7f">│   </span><span style="color: #808000; text-decoration-color: #808000">frequency_interval</span>=<span style="color: #800080; text-decoration-color: #800080; font-style: italic">None</span>,
<span style="color: #7fbf7f; text-decoration-color: #7fbf7f">│   </span><span style="color: #808000; text-decoration-color: #808000">spectrum</span>=<span style="color: #800080; text-decoration-color: #800080; font-style: italic">None</span>,
<span style="color: #7fbf7f; text-decoration-color: #7fbf7f">│   </span><span style="color: #808000; text-decoration-color: #808000">period</span>=<span style="color: #800080; text-decoration-color: #800080; font-style: italic">None</span>,
<span style="color: #7fbf7f; text-decoration-color: #7fbf7f">│   </span><span style="color: #808000; text-decoration-color: #808000">displacement_spectrum</span>=<span style="color: #800080; text-decoration-color: #800080; font-style: italic">None</span>,
<span style="color: #7fbf7f; text-decoration-color: #7fbf7f">│   </span><span style="color: #808000; text-decoration-color: #808000">velocity_spectrum</span>=<span style="color: #800080; text-decoration-color: #800080; font-style: italic">None</span>,
<span style="color: #7fbf7f; text-decoration-color: #7fbf7f">│   </span><span style="color: #808000; text-decoration-color: #808000">acceleration_spectrum</span>=<span style="color: #800080; text-decoration-color: #800080; font-style: italic">None</span>
<span style="font-weight: bold">)</span>
</pre>



A list of `MBRecord` objects will be returned.
The search method only returns the metadata of the records.
As one may have observed, the `MBRecord` object does not contain the actual data.

More query parameters can be applied.
The actual amount of records returned may be less than the specified amount, if there are not enough records to return.


```python
async with MBClient(server_url, timeout=20, semaphore=10) as client:
    results = await client.search(
        QueryConfig(
            min_pga=300, min_magnitude=7, pagination=PaginationConfig(page_size=800)
        )
    )
    pprint(f"Find {len(results)} records.")
```


<pre style="white-space:pre;overflow-x:auto;line-height:normal;font-family:Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace"><span style="color: #008000; text-decoration-color: #008000">'Find 530 records.'</span>
</pre>



## Download

The download method accepts a record ID as found in the metadata.


```python
from mb.client import MBRecord


example_record: MBRecord
async with MBClient(server_url, timeout=20, semaphore=10) as client:
    await client.download(results[0].id)
    for r in client:
        example_record = r
        pprint(r, max_length=10)
```


<pre style="white-space:pre;overflow-x:auto;line-height:normal;font-family:Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace">Successfully downloaded file <span style="color: #008000; text-decoration-color: #008000">d7348417-57b8-5f9f-bb88-aaf8f54c2ba4</span>. <span style="font-weight: bold">[</span><span style="color: #800000; text-decoration-color: #800000; font-weight: bold">1</span><span style="color: #800000; text-decoration-color: #800000">/</span><span style="color: #800000; text-decoration-color: #800000; font-weight: bold">0</span><span style="font-weight: bold">]</span>.
</pre>




<pre style="white-space:pre;overflow-x:auto;line-height:normal;font-family:Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace"><span style="color: #800080; text-decoration-color: #800080; font-weight: bold">MBRecord</span><span style="font-weight: bold">(</span>
<span style="color: #7fbf7f; text-decoration-color: #7fbf7f">│   </span><span style="color: #808000; text-decoration-color: #808000">endpoint</span>=<span style="color: #008000; text-decoration-color: #008000">'/waveform'</span>,
<span style="color: #7fbf7f; text-decoration-color: #7fbf7f">│   </span><span style="color: #808000; text-decoration-color: #808000">id</span>=<span style="color: #008000; text-decoration-color: #008000">'d7348417-57b8-5f9f-bb88-aaf8f54c2ba4'</span>,
<span style="color: #7fbf7f; text-decoration-color: #7fbf7f">│   </span><span style="color: #808000; text-decoration-color: #808000">file_name</span>=<span style="color: #008000; text-decoration-color: #008000">'20161113_110259_WTMC_20.V2A'</span>,
<span style="color: #7fbf7f; text-decoration-color: #7fbf7f">│   </span><span style="color: #808000; text-decoration-color: #808000">category</span>=<span style="color: #008000; text-decoration-color: #008000">'processed'</span>,
<span style="color: #7fbf7f; text-decoration-color: #7fbf7f">│   </span><span style="color: #808000; text-decoration-color: #808000">region</span>=<span style="color: #008000; text-decoration-color: #008000">'nz'</span>,
<span style="color: #7fbf7f; text-decoration-color: #7fbf7f">│   </span><span style="color: #808000; text-decoration-color: #808000">uploaded_by</span>=<span style="color: #008000; text-decoration-color: #008000">'d41eadf4-5770-5e2f-874f-0f18f543fd73'</span>,
<span style="color: #7fbf7f; text-decoration-color: #7fbf7f">│   </span><span style="color: #808000; text-decoration-color: #808000">magnitude</span>=<span style="color: #008080; text-decoration-color: #008080; font-weight: bold">7.53</span>,
<span style="color: #7fbf7f; text-decoration-color: #7fbf7f">│   </span><span style="color: #808000; text-decoration-color: #808000">maximum_acceleration</span>=<span style="color: #008080; text-decoration-color: #008080; font-weight: bold">2969.75</span>,
<span style="color: #7fbf7f; text-decoration-color: #7fbf7f">│   </span><span style="color: #808000; text-decoration-color: #808000">event_time</span>=<span style="color: #800080; text-decoration-color: #800080; font-weight: bold">datetime</span><span style="color: #800080; text-decoration-color: #800080; font-weight: bold">.datetime</span><span style="font-weight: bold">(</span><span style="color: #008080; text-decoration-color: #008080; font-weight: bold">2016</span>, <span style="color: #008080; text-decoration-color: #008080; font-weight: bold">11</span>, <span style="color: #008080; text-decoration-color: #008080; font-weight: bold">13</span>, <span style="color: #008080; text-decoration-color: #008080; font-weight: bold">11</span>, <span style="color: #008080; text-decoration-color: #008080; font-weight: bold">2</span>, <span style="color: #008080; text-decoration-color: #008080; font-weight: bold">56</span><span style="font-weight: bold">)</span>,
<span style="color: #7fbf7f; text-decoration-color: #7fbf7f">│   </span><span style="color: #808000; text-decoration-color: #808000">event_location</span>=<span style="font-weight: bold">[</span><span style="color: #008080; text-decoration-color: #008080; font-weight: bold">173.02</span>, <span style="color: #008080; text-decoration-color: #008080; font-weight: bold">-42.69</span><span style="font-weight: bold">]</span>,
<span style="color: #7fbf7f; text-decoration-color: #7fbf7f">│   </span><span style="color: #808000; text-decoration-color: #808000">depth</span>=<span style="color: #008080; text-decoration-color: #008080; font-weight: bold">15.0</span>,
<span style="color: #7fbf7f; text-decoration-color: #7fbf7f">│   </span><span style="color: #808000; text-decoration-color: #808000">station_code</span>=<span style="color: #008000; text-decoration-color: #008000">'WTMC'</span>,
<span style="color: #7fbf7f; text-decoration-color: #7fbf7f">│   </span><span style="color: #808000; text-decoration-color: #808000">station_location</span>=<span style="font-weight: bold">[</span><span style="color: #008080; text-decoration-color: #008080; font-weight: bold">173.054</span>, <span style="color: #008080; text-decoration-color: #008080; font-weight: bold">-42.619</span><span style="font-weight: bold">]</span>,
<span style="color: #7fbf7f; text-decoration-color: #7fbf7f">│   </span><span style="color: #808000; text-decoration-color: #808000">station_elevation</span>=<span style="color: #800080; text-decoration-color: #800080; font-style: italic">None</span>,
<span style="color: #7fbf7f; text-decoration-color: #7fbf7f">│   </span><span style="color: #808000; text-decoration-color: #808000">station_elevation_unit</span>=<span style="color: #800080; text-decoration-color: #800080; font-style: italic">None</span>,
<span style="color: #7fbf7f; text-decoration-color: #7fbf7f">│   </span><span style="color: #808000; text-decoration-color: #808000">record_time</span>=<span style="color: #800080; text-decoration-color: #800080; font-weight: bold">datetime</span><span style="color: #800080; text-decoration-color: #800080; font-weight: bold">.datetime</span><span style="font-weight: bold">(</span><span style="color: #008080; text-decoration-color: #008080; font-weight: bold">2016</span>, <span style="color: #008080; text-decoration-color: #008080; font-weight: bold">11</span>, <span style="color: #008080; text-decoration-color: #008080; font-weight: bold">13</span>, <span style="color: #008080; text-decoration-color: #008080; font-weight: bold">11</span>, <span style="color: #008080; text-decoration-color: #008080; font-weight: bold">2</span>, <span style="color: #008080; text-decoration-color: #008080; font-weight: bold">19</span><span style="font-weight: bold">)</span>,
<span style="color: #7fbf7f; text-decoration-color: #7fbf7f">│   </span><span style="color: #808000; text-decoration-color: #808000">last_update_time</span>=<span style="color: #800080; text-decoration-color: #800080; font-weight: bold">datetime</span><span style="color: #800080; text-decoration-color: #800080; font-weight: bold">.datetime</span><span style="font-weight: bold">(</span><span style="color: #008080; text-decoration-color: #008080; font-weight: bold">2017</span>, <span style="color: #008080; text-decoration-color: #008080; font-weight: bold">1</span>, <span style="color: #008080; text-decoration-color: #008080; font-weight: bold">20</span>, <span style="color: #008080; text-decoration-color: #008080; font-weight: bold">11</span>, <span style="color: #008080; text-decoration-color: #008080; font-weight: bold">0</span><span style="font-weight: bold">)</span>,
<span style="color: #7fbf7f; text-decoration-color: #7fbf7f">│   </span><span style="color: #808000; text-decoration-color: #808000">sampling_frequency</span>=<span style="color: #008080; text-decoration-color: #008080; font-weight: bold">200.0</span>,
<span style="color: #7fbf7f; text-decoration-color: #7fbf7f">│   </span><span style="color: #808000; text-decoration-color: #808000">sampling_frequency_unit</span>=<span style="color: #008000; text-decoration-color: #008000">'hertz'</span>,
<span style="color: #7fbf7f; text-decoration-color: #7fbf7f">│   </span><span style="color: #808000; text-decoration-color: #808000">duration</span>=<span style="color: #008080; text-decoration-color: #008080; font-weight: bold">209.99</span>,
<span style="color: #7fbf7f; text-decoration-color: #7fbf7f">│   </span><span style="color: #808000; text-decoration-color: #808000">direction</span>=<span style="color: #008000; text-decoration-color: #008000">'UP'</span>,
<span style="color: #7fbf7f; text-decoration-color: #7fbf7f">│   </span><span style="color: #808000; text-decoration-color: #808000">scale_factor</span>=<span style="color: #008080; text-decoration-color: #008080; font-weight: bold">1e-05</span>,
<span style="color: #7fbf7f; text-decoration-color: #7fbf7f">│   </span><span style="color: #808000; text-decoration-color: #808000">raw_data</span>=<span style="font-weight: bold">[</span><span style="color: #008080; text-decoration-color: #008080; font-weight: bold">0</span>, <span style="color: #008080; text-decoration-color: #008080; font-weight: bold">0</span>, <span style="color: #008080; text-decoration-color: #008080; font-weight: bold">0</span>, <span style="color: #008080; text-decoration-color: #008080; font-weight: bold">0</span>, <span style="color: #008080; text-decoration-color: #008080; font-weight: bold">0</span>, <span style="color: #008080; text-decoration-color: #008080; font-weight: bold">0</span>, <span style="color: #008080; text-decoration-color: #008080; font-weight: bold">0</span>, <span style="color: #008080; text-decoration-color: #008080; font-weight: bold">0</span>, <span style="color: #008080; text-decoration-color: #008080; font-weight: bold">0</span>, <span style="color: #008080; text-decoration-color: #008080; font-weight: bold">0</span>, <span style="color: #808000; text-decoration-color: #808000">...</span> +<span style="color: #008080; text-decoration-color: #008080; font-weight: bold">41990</span><span style="font-weight: bold">]</span>,
<span style="color: #7fbf7f; text-decoration-color: #7fbf7f">│   </span><span style="color: #808000; text-decoration-color: #808000">raw_data_unit</span>=<span style="color: #008000; text-decoration-color: #008000">'millimeter / second ** 2'</span>,
<span style="color: #7fbf7f; text-decoration-color: #7fbf7f">│   </span><span style="color: #808000; text-decoration-color: #808000">offset</span>=<span style="color: #008080; text-decoration-color: #008080; font-weight: bold">0.0</span>,
<span style="color: #7fbf7f; text-decoration-color: #7fbf7f">│   </span><span style="color: #808000; text-decoration-color: #808000">processed_data_unit</span>=<span style="color: #008000; text-decoration-color: #008000">'millimeter / second ** 2'</span>,
<span style="color: #7fbf7f; text-decoration-color: #7fbf7f">│   </span><span style="color: #808000; text-decoration-color: #808000">time_interval</span>=<span style="color: #008080; text-decoration-color: #008080; font-weight: bold">0.005</span>,
<span style="color: #7fbf7f; text-decoration-color: #7fbf7f">│   </span><span style="color: #808000; text-decoration-color: #808000">waveform</span>=<span style="font-weight: bold">[</span><span style="color: #008080; text-decoration-color: #008080; font-weight: bold">0.0</span>, <span style="color: #008080; text-decoration-color: #008080; font-weight: bold">0.0</span>, <span style="color: #008080; text-decoration-color: #008080; font-weight: bold">0.0</span>, <span style="color: #008080; text-decoration-color: #008080; font-weight: bold">0.0</span>, <span style="color: #008080; text-decoration-color: #008080; font-weight: bold">0.0</span>, <span style="color: #008080; text-decoration-color: #008080; font-weight: bold">0.0</span>, <span style="color: #008080; text-decoration-color: #008080; font-weight: bold">0.0</span>, <span style="color: #008080; text-decoration-color: #008080; font-weight: bold">0.0</span>, <span style="color: #008080; text-decoration-color: #008080; font-weight: bold">0.0</span>, <span style="color: #008080; text-decoration-color: #008080; font-weight: bold">0.0</span>, <span style="color: #808000; text-decoration-color: #808000">...</span> +<span style="color: #008080; text-decoration-color: #008080; font-weight: bold">41990</span><span style="font-weight: bold">]</span>,
<span style="color: #7fbf7f; text-decoration-color: #7fbf7f">│   </span><span style="color: #808000; text-decoration-color: #808000">frequency_interval</span>=<span style="color: #800080; text-decoration-color: #800080; font-style: italic">None</span>,
<span style="color: #7fbf7f; text-decoration-color: #7fbf7f">│   </span><span style="color: #808000; text-decoration-color: #808000">spectrum</span>=<span style="color: #800080; text-decoration-color: #800080; font-style: italic">None</span>,
<span style="color: #7fbf7f; text-decoration-color: #7fbf7f">│   </span><span style="color: #808000; text-decoration-color: #808000">period</span>=<span style="color: #800080; text-decoration-color: #800080; font-style: italic">None</span>,
<span style="color: #7fbf7f; text-decoration-color: #7fbf7f">│   </span><span style="color: #808000; text-decoration-color: #808000">displacement_spectrum</span>=<span style="color: #800080; text-decoration-color: #800080; font-style: italic">None</span>,
<span style="color: #7fbf7f; text-decoration-color: #7fbf7f">│   </span><span style="color: #808000; text-decoration-color: #808000">velocity_spectrum</span>=<span style="color: #800080; text-decoration-color: #800080; font-style: italic">None</span>,
<span style="color: #7fbf7f; text-decoration-color: #7fbf7f">│   </span><span style="color: #808000; text-decoration-color: #808000">acceleration_spectrum</span>=<span style="color: #800080; text-decoration-color: #800080; font-style: italic">None</span>
<span style="font-weight: bold">)</span>
</pre>



The downloaded records are internally stored.
After the call to the download method, the records can be accessed by iterating over the client object.
One can observe that now the `MBRecord` object contains the actual data, both the raw data (typically integer) and the floating point data.

One can combine the search and download methods to download multiple records.
The downloaded records are stored in the client object.


```python
async with MBClient(server_url, timeout=20, semaphore=2) as client:
    page: int = 0
    while results := await client.search(
        QueryConfig(
            min_pga=1000,
            min_magnitude=7,
            pagination=PaginationConfig(page_size=20, page_number=page),
        )
    ):
        await client.download(results)
        page += 1

pprint(f"Downloaded {len(client)} records with {page} pages.")
```


<pre style="white-space:pre;overflow-x:auto;line-height:normal;font-family:Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace">Successfully downloaded file <span style="color: #008000; text-decoration-color: #008000">d7348417-57b8-5f9f-bb88-aaf8f54c2ba4</span>. <span style="font-weight: bold">[</span><span style="color: #800000; text-decoration-color: #800000; font-weight: bold">1</span><span style="color: #800000; text-decoration-color: #800000">/</span><span style="color: #800000; text-decoration-color: #800000; font-weight: bold">20</span><span style="font-weight: bold">]</span>.
</pre>




<pre style="white-space:pre;overflow-x:auto;line-height:normal;font-family:Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace">Successfully downloaded file <span style="color: #008000; text-decoration-color: #008000">37c59a4f-26b2-5ac0-b831-fe89d0d7d1f3</span>. <span style="font-weight: bold">[</span><span style="color: #800000; text-decoration-color: #800000; font-weight: bold">2</span><span style="color: #800000; text-decoration-color: #800000">/</span><span style="color: #800000; text-decoration-color: #800000; font-weight: bold">20</span><span style="font-weight: bold">]</span>.
</pre>




<pre style="white-space:pre;overflow-x:auto;line-height:normal;font-family:Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace">Successfully downloaded file <span style="color: #008000; text-decoration-color: #008000">768ee435-fccc-55ae-877e-36adbba217a6</span>. <span style="font-weight: bold">[</span><span style="color: #800000; text-decoration-color: #800000; font-weight: bold">3</span><span style="color: #800000; text-decoration-color: #800000">/</span><span style="color: #800000; text-decoration-color: #800000; font-weight: bold">20</span><span style="font-weight: bold">]</span>.
</pre>




<pre style="white-space:pre;overflow-x:auto;line-height:normal;font-family:Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace">Successfully downloaded file <span style="color: #008000; text-decoration-color: #008000">36811a3f-4510-5417-9b28-ea056e55e7aa</span>. <span style="font-weight: bold">[</span><span style="color: #800000; text-decoration-color: #800000; font-weight: bold">4</span><span style="color: #800000; text-decoration-color: #800000">/</span><span style="color: #800000; text-decoration-color: #800000; font-weight: bold">20</span><span style="font-weight: bold">]</span>.
</pre>




<pre style="white-space:pre;overflow-x:auto;line-height:normal;font-family:Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace">Successfully downloaded file <span style="color: #008000; text-decoration-color: #008000">510f53a7-f643-584d-9209-3af93244c001</span>. <span style="font-weight: bold">[</span><span style="color: #800000; text-decoration-color: #800000; font-weight: bold">5</span><span style="color: #800000; text-decoration-color: #800000">/</span><span style="color: #800000; text-decoration-color: #800000; font-weight: bold">20</span><span style="font-weight: bold">]</span>.
</pre>




<pre style="white-space:pre;overflow-x:auto;line-height:normal;font-family:Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace">Successfully downloaded file <span style="color: #008000; text-decoration-color: #008000">119ccd74-d185-515d-b9d9-92eae86e6d2c</span>. <span style="font-weight: bold">[</span><span style="color: #800000; text-decoration-color: #800000; font-weight: bold">6</span><span style="color: #800000; text-decoration-color: #800000">/</span><span style="color: #800000; text-decoration-color: #800000; font-weight: bold">20</span><span style="font-weight: bold">]</span>.
</pre>




<pre style="white-space:pre;overflow-x:auto;line-height:normal;font-family:Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace">Successfully downloaded file <span style="color: #008000; text-decoration-color: #008000">b851c73f-3124-5df7-ae25-e23b17b7defa</span>. <span style="font-weight: bold">[</span><span style="color: #800000; text-decoration-color: #800000; font-weight: bold">7</span><span style="color: #800000; text-decoration-color: #800000">/</span><span style="color: #800000; text-decoration-color: #800000; font-weight: bold">20</span><span style="font-weight: bold">]</span>.
</pre>




<pre style="white-space:pre;overflow-x:auto;line-height:normal;font-family:Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace">Successfully downloaded file <span style="color: #008000; text-decoration-color: #008000">fb5444ff-4db1-50e3-9d67-2dbb51e8ff55</span>. <span style="font-weight: bold">[</span><span style="color: #800000; text-decoration-color: #800000; font-weight: bold">8</span><span style="color: #800000; text-decoration-color: #800000">/</span><span style="color: #800000; text-decoration-color: #800000; font-weight: bold">20</span><span style="font-weight: bold">]</span>.
</pre>




<pre style="white-space:pre;overflow-x:auto;line-height:normal;font-family:Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace">Successfully downloaded file <span style="color: #008000; text-decoration-color: #008000">b27d7ed6-47ee-52d4-83c6-a2f0651b8d37</span>. <span style="font-weight: bold">[</span><span style="color: #800000; text-decoration-color: #800000; font-weight: bold">9</span><span style="color: #800000; text-decoration-color: #800000">/</span><span style="color: #800000; text-decoration-color: #800000; font-weight: bold">20</span><span style="font-weight: bold">]</span>.
</pre>




<pre style="white-space:pre;overflow-x:auto;line-height:normal;font-family:Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace">Successfully downloaded file <span style="color: #008000; text-decoration-color: #008000">5280dad2-b80e-57de-a0e9-2243209fbf2d</span>. <span style="font-weight: bold">[</span><span style="color: #800000; text-decoration-color: #800000; font-weight: bold">10</span><span style="color: #800000; text-decoration-color: #800000">/</span><span style="color: #800000; text-decoration-color: #800000; font-weight: bold">20</span><span style="font-weight: bold">]</span>.
</pre>




<pre style="white-space:pre;overflow-x:auto;line-height:normal;font-family:Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace">Successfully downloaded file <span style="color: #008000; text-decoration-color: #008000">586d0e40-a09a-5852-b5ab-49e0ef28bfee</span>. <span style="font-weight: bold">[</span><span style="color: #800000; text-decoration-color: #800000; font-weight: bold">11</span><span style="color: #800000; text-decoration-color: #800000">/</span><span style="color: #800000; text-decoration-color: #800000; font-weight: bold">20</span><span style="font-weight: bold">]</span>.
</pre>




<pre style="white-space:pre;overflow-x:auto;line-height:normal;font-family:Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace">Successfully downloaded file <span style="color: #008000; text-decoration-color: #008000">14d0f56d-8ab1-5176-9d9c-37a2fe65c561</span>. <span style="font-weight: bold">[</span><span style="color: #800000; text-decoration-color: #800000; font-weight: bold">12</span><span style="color: #800000; text-decoration-color: #800000">/</span><span style="color: #800000; text-decoration-color: #800000; font-weight: bold">20</span><span style="font-weight: bold">]</span>.
</pre>




<pre style="white-space:pre;overflow-x:auto;line-height:normal;font-family:Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace">Successfully downloaded file <span style="color: #008000; text-decoration-color: #008000">3f432486-bd9f-5e8c-84e5-1a3703cc595c</span>. <span style="font-weight: bold">[</span><span style="color: #800000; text-decoration-color: #800000; font-weight: bold">13</span><span style="color: #800000; text-decoration-color: #800000">/</span><span style="color: #800000; text-decoration-color: #800000; font-weight: bold">20</span><span style="font-weight: bold">]</span>.
</pre>




<pre style="white-space:pre;overflow-x:auto;line-height:normal;font-family:Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace">Successfully downloaded file <span style="color: #008000; text-decoration-color: #008000">60a15fc4-ec1e-5ee3-8145-ebe04fc5b683</span>. <span style="font-weight: bold">[</span><span style="color: #800000; text-decoration-color: #800000; font-weight: bold">14</span><span style="color: #800000; text-decoration-color: #800000">/</span><span style="color: #800000; text-decoration-color: #800000; font-weight: bold">20</span><span style="font-weight: bold">]</span>.
</pre>




<pre style="white-space:pre;overflow-x:auto;line-height:normal;font-family:Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace">Successfully downloaded file <span style="color: #008000; text-decoration-color: #008000">5d10d4b0-3ace-5e6c-8ac4-7450dc070ab1</span>. <span style="font-weight: bold">[</span><span style="color: #800000; text-decoration-color: #800000; font-weight: bold">15</span><span style="color: #800000; text-decoration-color: #800000">/</span><span style="color: #800000; text-decoration-color: #800000; font-weight: bold">20</span><span style="font-weight: bold">]</span>.
</pre>




<pre style="white-space:pre;overflow-x:auto;line-height:normal;font-family:Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace">Successfully downloaded file <span style="color: #008000; text-decoration-color: #008000">0e4a3d18-5210-5523-b864-9e069f3b7c62</span>. <span style="font-weight: bold">[</span><span style="color: #800000; text-decoration-color: #800000; font-weight: bold">16</span><span style="color: #800000; text-decoration-color: #800000">/</span><span style="color: #800000; text-decoration-color: #800000; font-weight: bold">20</span><span style="font-weight: bold">]</span>.
</pre>




<pre style="white-space:pre;overflow-x:auto;line-height:normal;font-family:Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace">Successfully downloaded file <span style="color: #008000; text-decoration-color: #008000">9e65e730-93d8-5419-b4c5-b1dcda9bfc59</span>. <span style="font-weight: bold">[</span><span style="color: #800000; text-decoration-color: #800000; font-weight: bold">17</span><span style="color: #800000; text-decoration-color: #800000">/</span><span style="color: #800000; text-decoration-color: #800000; font-weight: bold">20</span><span style="font-weight: bold">]</span>.
</pre>




<pre style="white-space:pre;overflow-x:auto;line-height:normal;font-family:Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace">Successfully downloaded file <span style="color: #008000; text-decoration-color: #008000">b6a20df6-7735-5db4-b004-d61835c07d23</span>. <span style="font-weight: bold">[</span><span style="color: #800000; text-decoration-color: #800000; font-weight: bold">18</span><span style="color: #800000; text-decoration-color: #800000">/</span><span style="color: #800000; text-decoration-color: #800000; font-weight: bold">20</span><span style="font-weight: bold">]</span>.
</pre>




<pre style="white-space:pre;overflow-x:auto;line-height:normal;font-family:Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace">Successfully downloaded file <span style="color: #008000; text-decoration-color: #008000">8e5df753-ffa2-52cd-9be0-243717168ff3</span>. <span style="font-weight: bold">[</span><span style="color: #800000; text-decoration-color: #800000; font-weight: bold">19</span><span style="color: #800000; text-decoration-color: #800000">/</span><span style="color: #800000; text-decoration-color: #800000; font-weight: bold">20</span><span style="font-weight: bold">]</span>.
</pre>




<pre style="white-space:pre;overflow-x:auto;line-height:normal;font-family:Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace">Successfully downloaded file <span style="color: #008000; text-decoration-color: #008000">094b6d9f-9cd3-57c1-aa32-5139da2405c5</span>. <span style="font-weight: bold">[</span><span style="color: #800000; text-decoration-color: #800000; font-weight: bold">20</span><span style="color: #800000; text-decoration-color: #800000">/</span><span style="color: #800000; text-decoration-color: #800000; font-weight: bold">20</span><span style="font-weight: bold">]</span>.
</pre>




<pre style="white-space:pre;overflow-x:auto;line-height:normal;font-family:Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace">Successfully downloaded file <span style="color: #008000; text-decoration-color: #008000">7c94b073-6201-59fb-a891-a7b6b49edbad</span>. <span style="font-weight: bold">[</span><span style="color: #800000; text-decoration-color: #800000; font-weight: bold">21</span><span style="color: #800000; text-decoration-color: #800000">/</span><span style="color: #800000; text-decoration-color: #800000; font-weight: bold">36</span><span style="font-weight: bold">]</span>.
</pre>




<pre style="white-space:pre;overflow-x:auto;line-height:normal;font-family:Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace">Successfully downloaded file <span style="color: #008000; text-decoration-color: #008000">489ca841-af34-54f5-ab9a-4d470e0defd0</span>. <span style="font-weight: bold">[</span><span style="color: #800000; text-decoration-color: #800000; font-weight: bold">22</span><span style="color: #800000; text-decoration-color: #800000">/</span><span style="color: #800000; text-decoration-color: #800000; font-weight: bold">36</span><span style="font-weight: bold">]</span>.
</pre>




<pre style="white-space:pre;overflow-x:auto;line-height:normal;font-family:Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace">Successfully downloaded file <span style="color: #008000; text-decoration-color: #008000">aa5a878e-3336-56ad-8510-2a0af8235c22</span>. <span style="font-weight: bold">[</span><span style="color: #800000; text-decoration-color: #800000; font-weight: bold">23</span><span style="color: #800000; text-decoration-color: #800000">/</span><span style="color: #800000; text-decoration-color: #800000; font-weight: bold">36</span><span style="font-weight: bold">]</span>.
</pre>




<pre style="white-space:pre;overflow-x:auto;line-height:normal;font-family:Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace">Successfully downloaded file <span style="color: #008000; text-decoration-color: #008000">d23e52ec-1a04-53ab-b65b-c8b5b5d742c5</span>. <span style="font-weight: bold">[</span><span style="color: #800000; text-decoration-color: #800000; font-weight: bold">24</span><span style="color: #800000; text-decoration-color: #800000">/</span><span style="color: #800000; text-decoration-color: #800000; font-weight: bold">36</span><span style="font-weight: bold">]</span>.
</pre>




<pre style="white-space:pre;overflow-x:auto;line-height:normal;font-family:Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace">Successfully downloaded file <span style="color: #008000; text-decoration-color: #008000">547d9cb5-4a0c-5390-888d-a5047d281144</span>. <span style="font-weight: bold">[</span><span style="color: #800000; text-decoration-color: #800000; font-weight: bold">25</span><span style="color: #800000; text-decoration-color: #800000">/</span><span style="color: #800000; text-decoration-color: #800000; font-weight: bold">36</span><span style="font-weight: bold">]</span>.
</pre>




<pre style="white-space:pre;overflow-x:auto;line-height:normal;font-family:Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace">Successfully downloaded file <span style="color: #008000; text-decoration-color: #008000">6065733f-7114-5ff1-941c-0ef645d4250a</span>. <span style="font-weight: bold">[</span><span style="color: #800000; text-decoration-color: #800000; font-weight: bold">26</span><span style="color: #800000; text-decoration-color: #800000">/</span><span style="color: #800000; text-decoration-color: #800000; font-weight: bold">36</span><span style="font-weight: bold">]</span>.
</pre>




<pre style="white-space:pre;overflow-x:auto;line-height:normal;font-family:Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace">Successfully downloaded file <span style="color: #008000; text-decoration-color: #008000">3056fdfe-d7c8-54f0-8208-db32e7f3e81e</span>. <span style="font-weight: bold">[</span><span style="color: #800000; text-decoration-color: #800000; font-weight: bold">27</span><span style="color: #800000; text-decoration-color: #800000">/</span><span style="color: #800000; text-decoration-color: #800000; font-weight: bold">36</span><span style="font-weight: bold">]</span>.
</pre>




<pre style="white-space:pre;overflow-x:auto;line-height:normal;font-family:Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace">Successfully downloaded file <span style="color: #008000; text-decoration-color: #008000">c7d56f87-ae81-5902-b4f7-c7cb87deb2bf</span>. <span style="font-weight: bold">[</span><span style="color: #800000; text-decoration-color: #800000; font-weight: bold">28</span><span style="color: #800000; text-decoration-color: #800000">/</span><span style="color: #800000; text-decoration-color: #800000; font-weight: bold">36</span><span style="font-weight: bold">]</span>.
</pre>




<pre style="white-space:pre;overflow-x:auto;line-height:normal;font-family:Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace">Successfully downloaded file <span style="color: #008000; text-decoration-color: #008000">1ad305d8-a2b6-5249-8ed0-864eaf1480f3</span>. <span style="font-weight: bold">[</span><span style="color: #800000; text-decoration-color: #800000; font-weight: bold">29</span><span style="color: #800000; text-decoration-color: #800000">/</span><span style="color: #800000; text-decoration-color: #800000; font-weight: bold">36</span><span style="font-weight: bold">]</span>.
</pre>




<pre style="white-space:pre;overflow-x:auto;line-height:normal;font-family:Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace">Successfully downloaded file <span style="color: #008000; text-decoration-color: #008000">511c9843-071f-50f9-85d1-029dfb62699a</span>. <span style="font-weight: bold">[</span><span style="color: #800000; text-decoration-color: #800000; font-weight: bold">30</span><span style="color: #800000; text-decoration-color: #800000">/</span><span style="color: #800000; text-decoration-color: #800000; font-weight: bold">36</span><span style="font-weight: bold">]</span>.
</pre>




<pre style="white-space:pre;overflow-x:auto;line-height:normal;font-family:Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace">Successfully downloaded file <span style="color: #008000; text-decoration-color: #008000">82b387bc-c547-5baa-9e5d-6d31322d7cc2</span>. <span style="font-weight: bold">[</span><span style="color: #800000; text-decoration-color: #800000; font-weight: bold">31</span><span style="color: #800000; text-decoration-color: #800000">/</span><span style="color: #800000; text-decoration-color: #800000; font-weight: bold">36</span><span style="font-weight: bold">]</span>.
</pre>




<pre style="white-space:pre;overflow-x:auto;line-height:normal;font-family:Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace">Successfully downloaded file <span style="color: #008000; text-decoration-color: #008000">4f782305-92f7-52e6-9e45-0e5aa9e6497e</span>. <span style="font-weight: bold">[</span><span style="color: #800000; text-decoration-color: #800000; font-weight: bold">32</span><span style="color: #800000; text-decoration-color: #800000">/</span><span style="color: #800000; text-decoration-color: #800000; font-weight: bold">36</span><span style="font-weight: bold">]</span>.
</pre>




<pre style="white-space:pre;overflow-x:auto;line-height:normal;font-family:Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace">Successfully downloaded file <span style="color: #008000; text-decoration-color: #008000">ed3f1965-4d6e-53dc-89a6-8bb7f92fa190</span>. <span style="font-weight: bold">[</span><span style="color: #800000; text-decoration-color: #800000; font-weight: bold">33</span><span style="color: #800000; text-decoration-color: #800000">/</span><span style="color: #800000; text-decoration-color: #800000; font-weight: bold">36</span><span style="font-weight: bold">]</span>.
</pre>




<pre style="white-space:pre;overflow-x:auto;line-height:normal;font-family:Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace">Successfully downloaded file <span style="color: #008000; text-decoration-color: #008000">96de92bf-2f2c-5ea1-8625-237182abe000</span>. <span style="font-weight: bold">[</span><span style="color: #800000; text-decoration-color: #800000; font-weight: bold">34</span><span style="color: #800000; text-decoration-color: #800000">/</span><span style="color: #800000; text-decoration-color: #800000; font-weight: bold">36</span><span style="font-weight: bold">]</span>.
</pre>




<pre style="white-space:pre;overflow-x:auto;line-height:normal;font-family:Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace">Successfully downloaded file <span style="color: #008000; text-decoration-color: #008000">3f953202-0acc-5577-b272-5eb41be6760c</span>. <span style="font-weight: bold">[</span><span style="color: #800000; text-decoration-color: #800000; font-weight: bold">35</span><span style="color: #800000; text-decoration-color: #800000">/</span><span style="color: #800000; text-decoration-color: #800000; font-weight: bold">36</span><span style="font-weight: bold">]</span>.
</pre>




<pre style="white-space:pre;overflow-x:auto;line-height:normal;font-family:Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace">Successfully downloaded file <span style="color: #008000; text-decoration-color: #008000">5dcde0dc-3b81-5543-8dbb-7b7c29ffda01</span>. <span style="font-weight: bold">[</span><span style="color: #800000; text-decoration-color: #800000; font-weight: bold">36</span><span style="color: #800000; text-decoration-color: #800000">/</span><span style="color: #800000; text-decoration-color: #800000; font-weight: bold">36</span><span style="font-weight: bold">]</span>.
</pre>




<pre style="white-space:pre;overflow-x:auto;line-height:normal;font-family:Menlo,'DejaVu Sans Mono',consolas,'Courier New',monospace"><span style="color: #008000; text-decoration-color: #008000">'Downloaded 36 records with 2 pages.'</span>
</pre>



## Plot

One can now plot the waveform by calling the `plot_waveform` method.
It returns a `matplotlib` figure object.


```python
example_record.plot_waveform()
pass
```


    
![png](client_files/client_12_0.png)
    


To plot frequency spectrum, one can call the `plot_spectrum` method.


```python
example_record.plot_spectrum()
pass
```


    
![png](client_files/client_14_0.png)
    


To plot response spectra, one can call the `plot_response_spectrum` method.


```python
example_record.plot_response_spectrum()
pass

```


    
![png](client_files/client_16_0.png)
    


Since only waveform is retrieved from the server, all necessary processing is done locally on the client side.
It means one can also apply custom processing to the waveform data.

For example, one can customise the computation of response spectra by providing a damping ratio and a list of periods.


```python
import numpy as np


example_record.plot_response_spectrum(0.1, np.arange(0, 2, 0.01))
pass
```


    
![png](client_files/client_18_0.png)
    


It shall be pointed out that, the frequency spectrum and response spectra are computed from the current waveform data.
The waveform data can be modified by applying filters or other processing.

For example, one can normalise the record to have a unit amplitude.


```python
example_record.normalise()
example_record.plot_waveform()
example_record.plot_spectrum()
example_record.plot_response_spectrum(0.1, np.arange(0, 2, 0.01))
pass
```


    
![png](client_files/client_20_0.png)
    



    
![png](client_files/client_20_1.png)
    



    
![png](client_files/client_20_2.png)
    

