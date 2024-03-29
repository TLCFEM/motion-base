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
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from ..record.utility import filter_regex, window_regex


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

    endpoint: str = Field(None)

    id: str = Field(...)
    file_name: str | None = Field(...)
    category: str | None = Field(...)
    region: str | None = Field(...)
    uploaded_by: str | None = Field(...)

    magnitude: float | None = Field(...)
    maximum_acceleration: float | None = Field(...)

    event_time: datetime | None = Field(...)
    event_location: list[float, float] | None = Field(...)
    depth: float | None = Field(...)

    station_code: str | None = Field(...)
    station_location: list[float, float] | None = Field(...)
    station_elevation: float | None = Field(...)
    station_elevation_unit: str | None = Field(...)
    record_time: datetime | None = Field(...)
    last_update_time: datetime | None = Field(...)

    sampling_frequency: float | None = Field(...)
    sampling_frequency_unit: str | None = Field(...)
    duration: float | None = Field(...)
    direction: str | None = Field(...)
    scale_factor: float | None = Field(...)


class RawRecordResponse(MetadataResponse):
    """
    Response represents a record which can be either waveform or spectrum.
    """

    raw_data: list[int] | None = Field(None)
    raw_data_unit: str | None = Field(None)
    offset: float | None = Field(None)


class RecordResponse(MetadataResponse):
    """
    Response represents a record which can be either waveform or spectrum.
    """

    time_interval: float | None = Field(None)
    waveform: list[float] | None = Field(None)

    frequency_interval: float | None = Field(None)
    spectrum: list[float] | None = Field(None)

    period: list[float] | None = Field(None)
    displacement_spectrum: list[float] | None = Field(None)
    velocity_spectrum: list[float] | None = Field(None)
    acceleration_spectrum: list[float] | None = Field(None)


class PaginationResponse(BaseModel):
    """
    Pagination response.
    """

    total: int = Field(...)
    page_size: int = Field(...)
    page_number: int = Field(...)


class ListMetadataResponse(BaseModel):
    """
    Response represents a record which can be either waveform or spectrum.
    """

    records: list[MetadataResponse] = Field(None)
    pagination: PaginationResponse = Field(None)


class ProcessConfig(BaseModel):
    ratio: int = Field(1, ge=1)
    filter_length: int = Field(16, ge=8)
    filter_type: str = Field(
        "bandpass", regex=filter_regex, description="filter type, any of `lowpass`, `highpass`, `bandpass`, `bandstop`"
    )
    window_type: str = Field(
        "nuttall",
        regex=window_regex,
        description="any window type of `flattop`, `blackmanharris`, `nuttall`, `hann`, `hamming`, `kaiser`, `chebwin`",
    )
    low_cut: float = Field(0.05, ge=0)
    high_cut: float = Field(40.0, ge=0)
    damping_ratio: float = Field(0.05, ge=0, le=1)
    period_end: float = Field(20.0, ge=0)
    period_step: float = Field(0.05, ge=0)
    normalised: bool = Field(False)
    with_filter: bool = Field(False)
    with_spectrum: bool = Field(False)
    with_response_spectrum: bool = Field(False)
    remove_head: float = Field(0.0, ge=0)


class ProcessedResponse(RecordResponse):
    process_config: ProcessConfig


class UploadResponse(BaseModel):
    message: str
    task_ids: list | None = Field(None)
    records: list | None = Field(None)


class QueryConfig(BaseModel):
    region: str = Field(None, regex="^(jp|nz)$")
    min_magnitude: float = Field(None, ge=0, le=10)
    max_magnitude: float = Field(None, ge=0, le=10)
    category: str = Field(None)
    event_location: list[float, float] = Field(None, min_items=2, max_items=2)
    station_location: list[float, float] = Field(None, min_items=2, max_items=2)
    max_event_distance: float = Field(None, ge=0)
    max_station_distance: float = Field(None, ge=0)
    from_date: datetime = Field(None)
    to_date: datetime = Field(None)
    min_pga: float = Field(None)
    max_pga: float = Field(None)
    file_name: str = Field(None)
    station_code: str = Field(None)
    direction: str = Field(None)
    page_size: int = Field(10, ge=1, le=1000)
    page_number: int = Field(0, ge=0)

    def generate_query_string(self) -> tuple[dict, dict]:
        geo_query: dict = {}
        other_query: dict = {}

        if self.region is not None:
            other_query["region"] = self.region

        magnitude: dict = {}
        if self.min_magnitude is not None:
            magnitude["$gte"] = self.min_magnitude
        if self.max_magnitude is not None:
            magnitude["$lte"] = self.max_magnitude
        if magnitude:
            other_query["magnitude"] = magnitude

        if self.category is not None:
            other_query["category"] = self.category.lower()

        if self.event_location is not None:
            geo_json = {"$nearSphere": self.event_location, "$maxDistance": 10 / 6371}
            if self.max_event_distance is not None:
                geo_json["$maxDistance"] = self.max_event_distance / 6371 / 1000
            geo_query["event_location"] = geo_json

        if self.station_location is not None:
            geo_json = {"$nearSphere": self.station_location, "$maxDistance": 10 / 6371}
            if self.max_station_distance is not None:
                geo_json["$maxDistance"] = self.max_station_distance / 6371 / 1000
            geo_query["station_location"] = geo_json

        date_range: dict = {}
        if self.from_date is not None:
            date_range["$gte"] = self.from_date
        if self.to_date is not None:
            date_range["$lte"] = self.to_date
        if date_range:
            other_query["event_time"] = date_range

        pga: dict = {}
        if self.min_pga is not None:
            pga["$gte"] = self.min_pga
        if self.max_pga is not None:
            pga["$lte"] = self.max_pga
        if pga:
            other_query["maximum_acceleration"] = pga

        if self.direction is not None:
            other_query["direction"] = {"$regex": self.direction, "$options": "i"}

        if self.file_name is not None:
            other_query["file_name"] = {"$regex": self.file_name, "$options": "i"}

        if self.station_code is not None:
            other_query["station_code"] = {"$regex": self.station_code, "$options": "i"}

        return geo_query, other_query


class UploadTaskResponse(BaseModel):
    id: str
    create_time: datetime
    total_size: int
    current_size: int


class UploadTasksResponse(BaseModel):
    tasks: list[UploadTaskResponse | None]


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    last_name: str
    first_name: str


class Token(BaseModel):
    access_token: str
    token_type: str
