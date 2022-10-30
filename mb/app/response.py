#  Copyright (C) 2022 Theodore Chang
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
from typing import List
from uuid import UUID

from pydantic import BaseModel


class MetadataResponse(BaseModel):
    """
    The metadata of a record.

    Attributes:
        file_name: The original name of record file, often contains the station name and the event time.
        event_location: geographic location of the event. [longitude, latitude]
        station_location: geographic location of the station. [longitude, latitude]
        depth: depth of the event, in kilometer.
        maximum_acceleration: maximum acceleration (PGA) of the record, in cm/s/s.
    """
    id: UUID
    file_name: str
    sub_category: str
    magnitude: float
    origin_time: datetime
    event_location: list[float, float]
    depth: float  # km
    station_code: str
    station_location: list[float, float]
    sampling_frequency: float
    sampling_frequency_unit: str
    duration: float
    direction: str
    maximum_acceleration: float  # Gal


class SequenceResponse(MetadataResponse):
    """
    Response represents a record which can be either waveform or spectrum.
    """
    interval: float
    data: List[float]


class ResponseSpectrumResponse(MetadataResponse):
    """
    Response represents a record that is a response spectrum.
    """
    period: List[float]
    displacement_spectrum: List[float]
    velocity_spectrum: List[float]
    acceleration_spectrum: List[float]


class SequenceSpectrumResponse(MetadataResponse):
    """
    Response represents a record which contains both waveform and response spectrum.
    """
    time_interval: float | None
    waveform: List[float] | None

    frequency_interval: float | None
    spectrum: List[float] | None

    period: List[float] | None
    displacement_spectrum: List[float] | None
    velocity_spectrum: List[float] | None
    acceleration_spectrum: List[float] | None

    processing_parameters: dict | None


class MetadataListResponse(BaseModel):
    """
    A list of IDs of the target records.
    One can later use the ID to retrieve the record.
    """
    query: dict
    result: list[MetadataResponse]
