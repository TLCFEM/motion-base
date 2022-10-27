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
    id: UUID
    file_name: str
    sub_category: str
    magnitude: float
    origin_time: datetime
    latitude: float
    longitude: float
    depth: float
    depth_unit: str
    station_code: str
    station_latitude: float
    station_longitude: float
    sampling_frequency: float
    sampling_frequency_unit: str
    duration: float
    duration_unit: str
    direction: str


class SequenceResponse(MetadataResponse):
    """
    Response represents a record which can be either waveform or spectrum.
    """
    interval: float
    data: List[float]


class ResponseSpectrumResponse(MetadataResponse):
    """
    Response represents a record which can be either waveform or spectrum.
    """
    data: List[List[float]]


class MetadataListResponse(BaseModel):
    """
    A list of IDs of the target records.
    One can later use the ID to retrieve the record.
    """
    query: dict
    result: list[MetadataResponse]
