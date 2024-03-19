#  Copyright (C) 2022-2023 Theodore Chang
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
from uuid import UUID

from pydantic import BaseModel, Field

from mb.record.utility import filter_regex, window_regex


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

    id: UUID = Field(...)
    file_name: str | None = Field(...)
    category: str | None = Field(...)
    region: str | None = Field(...)
    uploaded_by: UUID | None = Field(...)

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

    sampling_frequency: float | None = Field(...)
    sampling_frequency_unit: str | None = Field(...)
    duration: float | None = Field(...)
    direction: str | None = Field(...)
    scale_factor: float | None = Field(...)


class ListMetadataResponse(BaseModel):
    """
    Response represents a record which can be either waveform or spectrum.
    """

    records: list[MetadataResponse] = Field(None)


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


class ListRecordResponse(BaseModel):
    """
    Response represents a record which can be either waveform or spectrum.
    """

    records: list[RecordResponse]


class ProcessConfig(BaseModel):
    ratio: int = Field(None, ge=1)
    filter_length: int = Field(None, ge=8)
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


class ProcessedResponse(RecordResponse):
    process_config: ProcessConfig


class QueryConfig(BaseModel):
    region: str = Field(None)
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
    event_name: str = Field(None)
    direction: str = Field(None)
    page_size: int = Field(10, ge=1, le=1000)
    page_number: int = Field(0, ge=0)

    def generate_query_string(self) -> dict:
        query_dict: dict = {"$and": []}

        if self.region is not None:
            query_dict["$and"].append({"region": self.region})

        magnitude: dict = {}
        if self.min_magnitude is not None:
            magnitude["$gte"] = self.min_magnitude
        if self.max_magnitude is not None:
            magnitude["$lte"] = self.max_magnitude
        if magnitude:
            query_dict["$and"].append({"magnitude": magnitude})

        if self.category is not None:
            query_dict["$and"].append({"category": self.category.lower()})

        if self.event_location is not None:
            query_dict["event_location"] = {"$nearSphere": self.event_location}
            if self.max_event_distance is not None:
                query_dict["event_location"]["$maxDistance"] = self.max_event_distance / 6371

        if self.station_location is not None:
            query_dict["station_location"] = {"$nearSphere": self.station_location}
            if self.max_station_distance is not None:
                query_dict["station_location"]["$maxDistance"] = self.max_station_distance / 6371

        date_range: dict = {}
        if self.from_date is not None:
            date_range["$gte"] = self.from_date
        if self.to_date is not None:
            date_range["$lte"] = self.to_date
        if date_range:
            query_dict["$and"].append({"event_time": date_range})

        pga: dict = {}
        if self.min_pga is not None:
            pga["$gte"] = self.min_pga
        if self.max_pga is not None:
            pga["$lte"] = self.max_pga
        if pga:
            query_dict["$and"].append({"maximum_acceleration": pga})

        if self.direction is not None:
            query_dict["$and"].append({"direction": {"$regex": self.direction, "$options": "i"}})

        if self.event_name is not None:
            query_dict["$and"].append({"file_name": {"$regex": self.event_name, "$options": "i"}})

        if not query_dict["$and"]:
            del query_dict["$and"]

        return query_dict
