# Processing Waveforms

`motion-base` stores raw acceleration samples and exposes processing as a stateless operation.
`POST /process` loads one record, applies a `ProcessConfig`, and returns the transformed waveform without modifying the database.
The Python client exposes offline equivalents for normalization, filtering, spectra, and export.

## Requesting Processing

```bash
BASE=http://localhost:8000
RECORD_ID=d7348417-57b8-5f9f-bb88-aaf8f54c2ba4

curl -s -X POST "$BASE/process?record_id=$RECORD_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "up_ratio": 2,
    "down_ratio": 1,
    "filter_length": 32,
    "filter_type": "bandpass",
    "window_type": "nuttall",
    "low_cut": 0.1,
    "high_cut": 20.0,
    "remove_head": 1.0,
    "normalised": false,
    "with_filter": true,
    "with_spectrum": true,
    "with_response_spectrum": true,
    "damping_ratio": 0.05,
    "period_end": 5.0,
    "period_step": 0.01
  }'
```

`record_id` is a query parameter and the body is a `ProcessConfig`.
The endpoint is public and does not require authentication.
A missing record returns `404`.
A cutoff configuration with `low_cut >= high_cut` returns `400`, even when filtering is disabled.

## Configuration

| Field | Default | Range | Meaning |
| --- | --- | --- | --- |
| `up_ratio` | `1` | `>= 1` | Upsampling factor used by the FIR filter stage |
| `down_ratio` | `1` | `>= 1` | Decimation factor applied after filtering |
| `filter_length` | `32` | `>= 8` | Half-length of the FIR filter, producing `2 * filter_length + 1` taps |
| `filter_type` | `bandpass` | `lowpass`, `highpass`, `bandpass`, `bandstop` | FIR response type |
| `window_type` | `nuttall` | `flattop`, `blackmanharris`, `nuttall`, `hann`, `hamming`, `kaiser`, `chebwin` | Window passed to `scipy.signal.firwin` |
| `low_cut` | `0.01` | `> 0` | Lower cutoff frequency in hertz |
| `high_cut` | `50.0` | `> 0` | Upper cutoff frequency in hertz |
| `damping_ratio` | `0.05` | `0` to `1` | Damping ratio for response spectra |
| `period_end` | `10.0` | `>= 0` | Largest response-spectrum period in seconds |
| `period_step` | `0.01` | `>= 0` | Period increment in seconds |
| `normalised` | `false` | Boolean | Divide the waveform by its peak absolute value |
| `with_filter` | `false` | Boolean | Enable upsampling and FIR filtering |
| `with_spectrum` | `false` | Boolean | Compute a one-sided FFT amplitude spectrum |
| `with_response_spectrum` | `false` | Boolean | Compute displacement, velocity, and acceleration response spectra |
| `remove_head` | `0.0` | `>= 0` | Seconds to remove from the start of the waveform |

Use `period_step > 0` in practice because a zero step does not produce a useful period grid.
Use `low_cut < high_cut` and keep both below the effective Nyquist frequency.

## Pipeline Order

The server applies operations in a fixed order.

1. Convert raw integer samples to acceleration in `cm/s/s`.
2. Normalize the waveform when `normalised=true`.
3. Remove `remove_head` seconds from the beginning.
4. When `with_filter=true`, upsample by `up_ratio`, design an FIR filter, and convolve it with the signal.
5. When `down_ratio > 1`, decimate by taking every `down_ratio`-th sample.
6. When `with_spectrum=true`, compute a one-sided FFT amplitude spectrum.
7. When `with_response_spectrum=true`, compute response spectra on the final waveform.

Each stage feeds the next stage.
Filtering therefore sees the waveform after head removal, and spectra are computed after resampling.

## Resampling Semantics

`up_ratio` is only applied inside the filter stage.
If `with_filter=false`, `up_ratio` has no effect and the original sampling interval is retained.

With filtering enabled, the effective sampling interval is:

```text
dt_out = dt_in * down_ratio / up_ratio
```

The reported `time_interval` reflects the final sampling interval.
With filtering enabled, the output length is approximately `len(waveform) * up_ratio / down_ratio` because decimation keeps every `down_ratio`-th sample.
Without filtering, the upsampling factor is 1 and the length is approximately `len(waveform) / down_ratio`.
FIR edge transients affect both ends of the record rather than the output length.

Upsampling is implemented by inserting zeros between samples and applying a scaled FIR filter.
Downsampling is plain decimation.
When `with_filter=false` and `down_ratio > 1`, no anti-alias filter is applied, so high-frequency content can alias into the output.
Enable filtering when decimating real data.

## Filter Design

The filter is an FIR filter designed with `scipy.signal.firwin`.
`filter_length` is a half-length, so the actual number of taps is `2 * filter_length + 1`.
The requested half-length is capped at `up_ratio * len(waveform) // 2` so it does not exceed half of the upsampled record.

Cutoff frequencies are converted to normalized frequencies using the post-upsampling interval.
For `bandpass` and `bandstop`, both `low_cut` and `high_cut` are used.
For `lowpass`, only `high_cut` is used.
For `highpass`, only `low_cut` is used.

The filter is convolved with the zero-stuffed signal using `same` output length.
This preserves the upsampled length but introduces the usual FIR edge transients.
Trim the beginning of a record with `remove_head` before filtering when the initial transient matters.

## Waveform and Units

The stored raw samples are integers with a source unit, scale factor, and offset.
Conversion to physical acceleration is:

```text
acceleration = (raw_data + offset) * scale_factor
```

The process endpoint returns numeric acceleration in `cm/s/s` and reports the final `time_interval`.
The numeric waveform is in `cm/s/s`, while the `processed_data_unit` label can mirror the source record's raw unit.
`normalised=true` divides by the peak absolute value before filtering.
Normalized data is dimensionless, so avoid applying unit conversions to it.

`remove_head` trims samples only.
It does not shift `record_time` or other metadata.

## FFT Spectrum

When `with_spectrum=true`, the response includes:

- `frequency_interval` in hertz.
- `spectrum` as a one-sided amplitude spectrum.

The computation is:

```text
spectrum = 2 * abs(rfft(waveform)) / len(waveform)
frequency_interval = 1 / (time_interval * len(waveform))
```

The spectrum is computed from the final, possibly resampled waveform.
Frequencies run from zero to the effective Nyquist frequency.

## Response Spectra

When `with_response_spectrum=true`, the response includes:

- `period` in seconds.
- `displacement_spectrum` (`SD`).
- `velocity_spectrum` (`SV`).
- `acceleration_spectrum` (`SA`).

The period grid runs from `0` to `period_end` in steps of `period_step`.
The solver integrates a linear single-degree-of-freedom oscillator for each period with the requested damping ratio.
It uses a recursive recurrence implemented with numba, not a frequency-domain approximation.
The special period of zero returns zero displacement and velocity, and returns PGA as the acceleration response.

Response spectra are computed on the final waveform after filtering and decimation.
The current implementation does not apply baseline correction to the acceleration before computing spectra.

## Client-Side Processing

Downloaded `MBRecord` objects contain the waveform and can be processed without another server request.

```python
import numpy as np

from mb.app.response import PaginationConfig, QueryConfig
from mb.client import MBClient


async def main():
    async with MBClient("http://localhost:8000") as client:
        records = (
            await client.search(QueryConfig(pagination=PaginationConfig(page_size=5)))
            or []
        )

        await client.download(records)

        for record in client:
            record.normalise()
            record.to_spectrum()
            record.to_response_spectrum(0.05, np.arange(0, 5, 0.01))
            record.to_table_file(f"{record.id}.txt")
```

| Method | Effect |
| --- | --- |
| `normalise()` | Divides the waveform by its peak absolute value and marks it dimensionless |
| `filter(window, up_ratio=1)` | Applies a precomputed FIR window to the waveform |
| `to_spectrum()` | Populates `frequency_interval` and `spectrum` |
| `to_response_spectrum(damping, period)` | Populates response-spectrum arrays |
| `to_table(unit=None)` | Returns time and acceleration arrays, optionally converted with Pint |
| `to_table_file(path, unit=None)` | Writes a two-column text file |
| `plot_waveform()` | Returns a Matplotlib figure of the current waveform |
| `plot_spectrum()` | Computes and plots the FFT spectrum |
| `plot_response_spectrum()` | Computes and plots three response spectra |

Client-side processing mutates the `MBRecord` instance.
Plots are not shown automatically, so call `matplotlib.pyplot.show()` when running interactively.
The client's `filter()` helper accepts a window array rather than a `ProcessConfig`.
Use `mb.record.utility.get_window` when a custom FIR window is needed, and leave its `ratio` at the default because `filter()` applies `up_ratio` itself.

## Practical Guidance

- Filter before decimating whenever possible.
- Remove strong initial transients before response-spectrum analysis.
- Use a period step of `0.01` seconds for ordinary spectra and a finer step only when needed.
- Use `period_end` larger than the dominant period of the structure being studied.
- Keep `filter_length` well below the record length to avoid an over-constrained filter.
- Compare raw and processed waveforms before drawing conclusions from a spectrum.
- Store the `process_config` returned by `/process` with exported results for reproducibility.

See the [API Reference](API.md) for the endpoint contract and the [Python Client](PythonClient.md) guide for download and plotting examples.
