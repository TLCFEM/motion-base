#  Copyright (C) 2022-2024 Theodore Chang
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
import os
from datetime import datetime
from uuid import NAMESPACE_OID, uuid5, uuid4

import numpy as np
import pint
import structlog
from mongoengine import Document, UUIDField, StringField, FloatField, DateTimeField, ListField, IntField

from .utility import normalise, convert_to, perform_fft

_logger = structlog.get_logger(__name__)


class Record(Document):
    id = UUIDField(False, primary_key=True)

    file_name = StringField(default=None, description="The original file name of the record.")
    category = StringField(default=None, description="The category of the record.")
    region = StringField(default=None, description="The region of the record.")
    uploaded_by = UUIDField(default=None, description="The user who uploaded the record.")

    magnitude = FloatField(default=None, description="The magnitude of the record.")
    maximum_acceleration = FloatField(default=None, description="PGA in Gal.")

    event_time = DateTimeField(default=None, description="The origin time of the record.")
    event_location = ListField(default=None, description="The geolocation of the earthquake event.")
    depth = FloatField(default=None, description="The depth of the earthquake event in kilometer.")

    station_code = StringField(default=None, description="The code of the station recording the record.")
    station_location = ListField(default=None, description="The geolocation of the station recording the record.")
    station_elevation = FloatField(default=None, description="The elevation of the station recording the record.")
    station_elevation_unit = StringField(
        default=None, description="The unit of the elevation of the station recording the record."
    )
    record_time = DateTimeField(default=None, description="The time the record was recorded.")
    last_update_time = DateTimeField(default=None, description="The time the record was last updated.")

    sampling_frequency = FloatField(default=None, description="The sampling frequency of the record.")
    sampling_frequency_unit = StringField(default=None, description="The unit of the sampling frequency of the record.")
    duration = FloatField(default=None, description="The duration of the record in seconds.")
    direction = StringField(default=None, description="The direction of the record.")
    scale_factor = FloatField(default=None, description="The scale factor of the record.")

    raw_data = ListField(default=None, description="The raw acceleration data of the record.")
    raw_data_unit = StringField(default=None, description="The unit of the raw acceleration data of the record.")
    offset = FloatField(default=0, description="The offset of the record.")

    meta = {
        "collection": "Record",
        "allow_inheritance": True,
        "indexes": [
            "file_name",
            "category",
            "region",
            "-magnitude",
            "-maximum_acceleration",
            "-event_time",
            [("event_location", "2dsphere")],
            "depth",
            [("station_location", "2dsphere")],
            "direction",
        ],
    }

    def save(self, *args, **kwargs):
        token: str = self.file_name
        if self.region is not None:
            token += self.region
        if self.category is not None:
            token += self.category
        if self.last_update_time is not None:
            token += self.last_update_time.isoformat()
        if self.direction is not None:
            token += self.direction
        self.id = uuid5(NAMESPACE_OID, token)
        return super().save(*args, **kwargs)

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

        return sampling_interval, convert_to(pint.Quantity(numpy_array, self.raw_data_unit), unit)

    def to_spectrum(self, **kwargs) -> tuple[float, np.ndarray]:
        _, waveform = self.to_waveform(**kwargs)
        return perform_fft(self.sampling_frequency, waveform)


class NIED(Record):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.region = "jp"

    def save(self, *args, **kwargs):
        self.offset = -sum(self.raw_data) / len(self.raw_data)
        return super().save(*args, **kwargs)


class NZSM(Record):
    FTI: float = 100000

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.region = "nz"
        self.scale_factor = 1 / self.FTI
        self.sampling_frequency_unit = str(pint.Unit("Hz"))
        self.raw_data_unit = str(pint.Unit("mm/s/s"))


class UploadTask(Document):
    id = UUIDField(False, default=uuid4)
    create_time = DateTimeField(default=datetime.now)
    pid = IntField(default=0)
    total_size = IntField(default=0)
    current_size = IntField(default=0)
    archive_path = StringField(default=None)

    @property
    def progress(self) -> float:
        return self.current_size / max(1, self.total_size)

    def delete(self, *args, **kwargs):
        if self.archive_path and os.path.exists(self.archive_path):
            try:
                os.remove(self.archive_path)
            except Exception as e:
                _logger.error("Failed to delete the archive.", exc_info=e, archive_path=self.archive_path)
        return super().delete(*args, **kwargs)
