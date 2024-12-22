#  Copyright (C) 2022-2025 Theodore Chang
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

from __future__ import annotations

from datetime import datetime

import numpy as np
import pint
from beanie import Document, Indexed
from pydantic import Field

from .utility import normalise, convert_to, perform_fft, str_factory

ASCENDING = 1
DESCENDING = -1
GEOSPHERE = "2dsphere"


class MetadataRecord(Document):
    id: str = Field(default_factory=str_factory)

    file_name: Indexed(str, "text") = Field(
        None, description="The original file name of the record."
    )
    file_hash: Indexed(str) = Field(None, description="The hash of the record.")
    category: Indexed(str) = Field(None, description="The category of the record.")
    region: Indexed(str) = Field(None, description="The region of the record.")
    uploaded_by: str = Field(None, description="The user who uploaded the record.")

    magnitude: Indexed(float, DESCENDING) = Field(
        None, description="The magnitude of the record."
    )
    maximum_acceleration: Indexed(float, DESCENDING) = Field(
        None, description="PGA in Gal."
    )

    event_time: Indexed(datetime, DESCENDING) = Field(
        None, description="The origin time of the record."
    )
    event_location: Indexed(list[float], GEOSPHERE) = Field(
        None, description="The geolocation of the earthquake event."
    )
    depth: Indexed(float) = Field(
        None, description="The depth of the earthquake event in kilometer."
    )

    station_code: Indexed(str) = Field(
        None, description="The code of the station recording the record."
    )
    station_location: Indexed(list[float], GEOSPHERE) = Field(
        None, description="The geolocation of the station recording the record."
    )
    station_elevation: float = Field(
        None, description="The elevation of the station recording the record."
    )
    station_elevation_unit: str = Field(
        None,
        description="The unit of the elevation of the station recording the record.",
    )
    record_time: datetime = Field(None, description="The time the record was recorded.")
    last_update_time: datetime = Field(
        None, description="The time the record was last updated."
    )

    sampling_frequency: float = Field(
        None, description="The sampling frequency of the record."
    )
    sampling_frequency_unit: str = Field(
        None, description="The unit of the sampling frequency of the record."
    )
    duration: float = Field(None, description="The duration of the record in seconds.")
    direction: Indexed(str) = Field(None, description="The direction of the record.")
    scale_factor: float = Field(None, description="The scale factor of the record.")

    class Settings:
        indexes = [
            [
                ("magnitude", DESCENDING),
                ("maximum_acceleration", DESCENDING),
                ("event_time", DESCENDING),
                ("direction", ASCENDING),
                ("event_location", DESCENDING),
            ],
        ]


class Record(MetadataRecord):
    raw_data: list[int] = Field(
        None, description="The raw acceleration data of the record."
    )
    raw_data_unit: str = Field(
        None, description="The unit of the raw acceleration data of the record."
    )
    offset: float = Field(0, description="The offset of the record.")

    def to_raw_waveform(self) -> tuple[float, list]:
        return 1 / self.sampling_frequency, self.raw_data

    def to_waveform(self, **kwargs) -> tuple[float, np.ndarray]:
        sampling_interval: float = 1 / self.sampling_frequency

        numpy_array: np.ndarray = np.array(self.raw_data, dtype=float) + self.offset
        if kwargs.get("normalised", False):
            numpy_array = normalise(numpy_array)
            unit = None
        else:
            numpy_array *= self.scale_factor
            unit = kwargs.get("unit", None)

        return sampling_interval, convert_to(
            pint.Quantity(numpy_array, self.raw_data_unit), unit
        )

    def to_spectrum(self, **kwargs) -> tuple[float, np.ndarray]:
        _, waveform = self.to_waveform(**kwargs)
        return perform_fft(self.sampling_frequency, waveform)


class NIED(Record):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.region = "jp"

    async def save(self, *args, **kwargs):
        self.offset = -sum(self.raw_data) / len(self.raw_data)
        return await super().save(*args, **kwargs)


class NZSM(Record):
    FTI: float = 100000

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.region = "nz"
        self.scale_factor = 1 / self.FTI
        self.sampling_frequency_unit = str(pint.Unit("Hz"))
        self.raw_data_unit = str(pint.Unit("mm/s/s"))


class UploadTask(Document):
    id: str = Field(default_factory=str_factory)
    create_time: datetime = Field(default_factory=datetime.now)
    pid: int = Field(default=0)
    total_size: int = Field(default=0)
    current_size: int = Field(default=0)
    archive_path: str = Field(default=None)

    @property
    def progress(self) -> float:
        return self.current_size / max(1, self.total_size)


async def create_task():
    task = UploadTask()
    await task.save()
    return task.id
