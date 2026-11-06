#  Copyright (C) 2022-2026 Theodore Chang
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.

from http import HTTPStatus

import numpy as np
import pytest
from fastapi import HTTPException

from mb.app.process import process_record_local
from mb.app.response import ProcessConfig
from mb.record.async_record import Record


@pytest.fixture
async def sample_record(mongo_connection):
    return Record(
        raw_data=[int(1000 * np.sin(0.1 * i)) for i in range(200)],
        raw_data_unit="cm/s/s",
        sampling_frequency=50.0,
        scale_factor=1e-5,
    )


async def test_process_defaults(sample_record):
    response = process_record_local(sample_record, ProcessConfig())

    assert response.endpoint == "/process"
    assert response.processed_data_unit == "cm/s/s"
    assert response.time_interval == pytest.approx(0.02)
    assert len(response.waveform) == len(sample_record.raw_data)
    assert response.spectrum is None
    assert response.period is None


@pytest.mark.parametrize(
    "filter_type", ["bandpass", "bandstop", "lowpass", "highpass"]
)
async def test_process_filter_types(sample_record, filter_type):
    response = process_record_local(
        sample_record,
        ProcessConfig(
            with_filter=True,
            filter_type=filter_type,
            up_ratio=2,
            down_ratio=2,
            filter_length=8,
        ),
    )

    assert response.time_interval == pytest.approx(0.02)
    assert len(response.waveform) == len(sample_record.raw_data)


async def test_process_all_processing_steps(sample_record):
    response = process_record_local(
        sample_record,
        ProcessConfig(
            with_filter=True,
            filter_type="bandpass",
            window_type="hann",
            up_ratio=2,
            down_ratio=2,
            normalised=True,
            remove_head=0.2,
            with_spectrum=True,
            with_response_spectrum=True,
            period_end=0.2,
            period_step=0.1,
        ),
    )

    assert len(response.waveform) < len(sample_record.raw_data)
    assert response.frequency_interval > 0
    assert response.spectrum
    assert response.period == pytest.approx(np.arange(0, 0.2 + 0.1, 0.1))
    assert response.displacement_spectrum
    assert response.velocity_spectrum
    assert response.acceleration_spectrum


async def test_process_invalid_filter_type(sample_record):
    config = ProcessConfig(with_filter=True)
    config.filter_type = "invalid"

    with pytest.raises(HTTPException) as exc_info:
        process_record_local(sample_record, config)

    assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST


async def test_process_invalid_cutoffs(sample_record):
    with pytest.raises(HTTPException) as exc_info:
        process_record_local(sample_record, ProcessConfig(low_cut=50.0, high_cut=10.0))

    assert exc_info.value.status_code == HTTPStatus.BAD_REQUEST
