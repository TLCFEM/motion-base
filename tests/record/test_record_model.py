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

from datetime import datetime

import numpy as np
import pytest

from mb.record.async_record import (
    MetadataRecord,
    Record,
    UploadTask,
    create_task,
    delete_task,
)


def _make_record() -> Record:
    return Record(
        file_name="test.V1A",
        raw_data=[0, 100, -100, 50],
        raw_data_unit="mm/s/s",
        sampling_frequency=100.0,
        scale_factor=1e-5,
        offset=10.0,
    )


async def test_metadata_record_accepts_instance(mongo_connection):
    record = MetadataRecord(file_name="test")
    assert MetadataRecord.model_validate(record) is not None


async def test_record_waveform_and_spectrum(mongo_connection):
    record = _make_record()

    interval, raw = record.to_raw_waveform()
    assert interval == pytest.approx(0.01)
    assert raw == record.raw_data

    interval, waveform = record.to_waveform()
    assert interval == pytest.approx(0.01)
    assert waveform == pytest.approx((np.array(record.raw_data) + 10.0) * 1e-5)

    _, waveform = record.to_waveform(unit="cm/s/s")
    assert waveform == pytest.approx(
        (np.array(record.raw_data) + 10.0) * 1e-5 * 0.1
    )

    _, waveform = record.to_waveform(normalised=True)
    expected = np.array(record.raw_data, dtype=float) + 10.0
    assert waveform == pytest.approx(expected / np.max(np.abs(expected)))

    frequency_interval, spectrum = record.to_spectrum()
    assert frequency_interval == pytest.approx(25.0)
    assert spectrum.shape == (3,)


async def test_metadata_record_save_id(mongo_connection):
    record = MetadataRecord(
        file_name="test.V1A",
        region="nz",
        category="processed",
        last_update_time=datetime(2020, 1, 1),
        direction="N",
    )

    await record.save()

    assert record.id
    assert await MetadataRecord.find_one(MetadataRecord.id == record.id)


async def test_upload_task_lifecycle(mongo_connection):
    task_id = await create_task()

    task = await UploadTask.get(task_id)
    assert task.progress == 0.0

    task.total_size = 4
    task.current_size = 2
    await task.save()
    assert task.progress == 0.5

    await delete_task(task_id)
    assert await UploadTask.find_one(UploadTask.id == task_id) is None

    # Deleting a missing task is a no-op.
    await delete_task(task_id)
