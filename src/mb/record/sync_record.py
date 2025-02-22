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
from datetime import datetime

import pint
import structlog
from mongoengine import (
    DateTimeField,
    Document,
    FloatField,
    IntField,
    ListField,
    StringField,
)

from .utility import str_factory, uuid5_str

_logger = structlog.get_logger(__name__)


class Record(Document):
    id = StringField(default=str_factory, primary_key=True)

    file_name = StringField(
        default=None, description="The original file name of the record."
    )
    file_hash = StringField(default=None, description="The hash of the record.")
    category = StringField(default=None, description="The category of the record.")
    region = StringField(default=None, description="The region of the record.")
    uploaded_by = StringField(
        default=None, description="The user who uploaded the record."
    )

    magnitude = FloatField(default=None, description="The magnitude of the record.")
    maximum_acceleration = FloatField(default=None, description="PGA in Gal.")

    event_time = DateTimeField(
        default=None, description="The origin time of the record."
    )
    event_location = ListField(
        default=None, description="The geolocation of the earthquake event."
    )
    depth = FloatField(
        default=None, description="The depth of the earthquake event in kilometer."
    )

    station_code = StringField(
        default=None, description="The code of the station recording the record."
    )
    station_location = ListField(
        default=None, description="The geolocation of the station recording the record."
    )
    station_elevation = FloatField(
        default=None, description="The elevation of the station recording the record."
    )
    station_elevation_unit = StringField(
        default=None,
        description="The unit of the elevation of the station recording the record.",
    )
    record_time = DateTimeField(
        default=None, description="The time the record was recorded."
    )
    last_update_time = DateTimeField(
        default=None, description="The time the record was last updated."
    )

    sampling_frequency = FloatField(
        default=None, description="The sampling frequency of the record."
    )
    sampling_frequency_unit = StringField(
        default=None, description="The unit of the sampling frequency of the record."
    )
    duration = FloatField(
        default=None, description="The duration of the record in seconds."
    )
    direction = StringField(default=None, description="The direction of the record.")
    scale_factor = FloatField(
        default=None, description="The scale factor of the record."
    )

    raw_data = ListField(
        default=None, description="The raw acceleration data of the record."
    )
    raw_data_unit = StringField(
        default=None, description="The unit of the raw acceleration data of the record."
    )
    offset = FloatField(default=0, description="The offset of the record.")

    meta = {
        "collection": "Record",
        "allow_inheritance": True,
        "indexes": [
            [("file_name", "text")],
            "file_hash",
            "category",
            "region",
            "-magnitude",
            "-maximum_acceleration",
            "-event_time",
            [("event_location", "2dsphere")],
            "depth",
            "station_code",
            [("station_location", "2dsphere")],
            "direction",
            (
                "-magnitude",
                "-maximum_acceleration",
                "-event_time",
                "direction",
                "event_location",
            ),
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
        self.id = uuid5_str(token)

        return super().save(*args, **kwargs)


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
    id = StringField(default=str_factory, primary_key=True)
    create_time = DateTimeField(default=datetime.now)
    pid = IntField(default=0)
    total_size = IntField(default=0)
    current_size = IntField(default=0)
    archive_path = StringField(default=None)

    meta = {
        "collection": "UploadTask",
    }

    @property
    def progress(self) -> float:
        return self.current_size / max(1, self.total_size)


def create_task(task_id=None):
    task = UploadTask() if task_id is None else UploadTask(id=task_id)
    task.save()
    return task.id


def delete_task(task_id: str):
    if (task := UploadTask.objects(id=task_id).first()) is not None:
        task.delete()
