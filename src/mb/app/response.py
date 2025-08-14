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
from enum import Enum

import numpy as np
from pydantic import BaseModel, Field, field_validator, model_validator

from ..record.response_spectrum import response_spectrum
from ..record.utility import apply_filter, filter_regex, window_regex, zero_stuff


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
    file_name: str = Field(None)
    category: str = Field(None)
    region: str = Field(None)
    uploaded_by: str = Field(None)

    magnitude: float = Field(None)
    maximum_acceleration: float = Field(None)

    event_time: datetime = Field(None)
    event_location: list[float] = Field(None)
    depth: float = Field(None)

    station_code: str = Field(None)
    station_location: list[float] = Field(None)
    station_elevation: float = Field(None)
    station_elevation_unit: str = Field(None)
    record_time: datetime = Field(None)
    last_update_time: datetime = Field(None)

    sampling_frequency: float = Field(None)
    sampling_frequency_unit: str = Field(None)
    duration: float = Field(None)
    direction: str = Field(None)
    scale_factor: float = Field(None)


class RawRecordResponse(MetadataResponse):
    """
    Response represents a record which can be either waveform or spectrum.
    """

    raw_data: list[int] = Field(None)
    raw_data_unit: str = Field(None)
    offset: float = Field(None)


class RecordResponse(RawRecordResponse):
    """
    Response represents a record which can be either waveform or spectrum.
    """

    processed_data_unit: str = Field(None)

    time_interval: float = Field(None)
    waveform: list[float] = Field(None)

    frequency_interval: float = Field(None)
    spectrum: list[float] = Field(None)

    period: list[float] = Field(None)
    displacement_spectrum: list[float] = Field(None)
    velocity_spectrum: list[float] = Field(None)
    acceleration_spectrum: list[float] = Field(None)

    @model_validator(mode="before")
    @classmethod
    def default_unit(cls, values):
        if values.get("processed_data_unit", None):
            values["processed_data_unit"] = values["raw_data_unit"]

        return values

    def normalise(self):
        if self.waveform is None:
            raise RuntimeError("Cannot normalise the waveform.")

        wave_array = np.array(self.waveform)
        self.waveform = (wave_array / np.max(np.abs(wave_array))).tolist()

        self.processed_data_unit = "1"

        return self

    def filter(self, window, up_ratio: int = 1):
        self.time_interval /= up_ratio
        # noinspection PyTypeChecker
        self.waveform = apply_filter(
            window * up_ratio, zero_stuff(up_ratio, self.waveform)
        ).tolist()

        return self

    def to_spectrum(self):
        if self.time_interval is None or self.waveform is None:
            raise RuntimeError("Cannot convert to spectrum.")

        self.frequency_interval = 1 / (self.time_interval * len(self.waveform))
        self.spectrum = (
            2 * np.abs(np.fft.rfft(self.waveform)) / len(self.waveform)
        ).tolist()

    def to_response_spectrum(
        self, damping_ratio: float, period: list[float] | np.ndarray
    ):
        if isinstance(period, np.ndarray):
            # noinspection PyTypeChecker
            self.period = period.tolist()
            spectra = response_spectrum(
                damping_ratio, self.time_interval, np.array(self.waveform), period
            )
        else:
            self.period = period
            spectra = response_spectrum(
                damping_ratio,
                self.time_interval,
                np.array(self.waveform),
                np.array(self.period),
            )
        self.displacement_spectrum = spectra[:, 0].tolist()
        self.velocity_spectrum = spectra[:, 1].tolist()
        self.acceleration_spectrum = spectra[:, 2].tolist()


class ListRecordResponse(BaseModel):
    records: list[RecordResponse] = Field(None)


class SortBy(str, Enum):
    magnitude = "magnitude"
    maximum_acceleration = "maximum_acceleration"
    event_time = "event_time"
    depth = "depth"


class PaginationConfig(BaseModel):
    """
    Pagination response.
    """

    page_size: int = Field(10, ge=1, le=1000)
    page_number: int = Field(0, ge=0)
    sort_by: str = Field("-maximum_acceleration")
    search_after: list | None = Field(None)

    @field_validator("sort_by")
    @classmethod
    def validate_sort_by(cls, v: str) -> str:
        if v is None:
            return "-maximum_acceleration"

        if v.startswith(("+", "-")) and v[1:].lower() in SortBy.__members__:
            return v.lower()

        raise ValueError(f"Invalid sort_by value: {v}")


class PaginationResponse(PaginationConfig):
    """
    Pagination response.
    """

    total: int = Field(...)


class ListMetadataResponse(BaseModel):
    """
    Response represents a record which can be either waveform or spectrum.
    """

    records: list[MetadataResponse] = Field(None)
    pagination: PaginationResponse = Field(None)


class ProcessConfig(BaseModel):
    up_ratio: int = Field(
        1,
        ge=1,
        description="Upsampling ratio, should be greater than one. "
        "The effective resampling ratio should be `up_ratio/down_ratio`.",
    )
    down_ratio: int = Field(
        1,
        ge=1,
        description="Downsampling ratio, should be greater than one. "
        "The effective resampling ratio should be `up_ratio/down_ratio`.",
    )
    filter_length: int = Field(
        32, ge=8, description="Filter window length, at least eight, default is 32."
    )
    filter_type: str = Field(
        "bandpass",
        pattern=filter_regex,
        description="filter type, any of `lowpass`, `highpass`, `bandpass`, `bandstop`",
    )
    window_type: str = Field(
        "nuttall",
        pattern=window_regex,
        description="any window type of `flattop`, `blackmanharris`, `nuttall`, `hann`, `hamming`, `kaiser`, `chebwin`",
    )
    low_cut: float = Field(0.01, gt=0)
    high_cut: float = Field(50.0, gt=0)
    damping_ratio: float = Field(0.05, ge=0, le=1)
    period_end: float = Field(10.0, ge=0)
    period_step: float = Field(0.01, ge=0)
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
    region: str | None = Field(None, pattern="^(jp|nz)$")
    min_magnitude: float | None = Field(None, ge=0, le=10)
    max_magnitude: float | None = Field(None, ge=0, le=10)
    category: str | None = Field(None)
    event_location: list[float] | None = Field(
        None, min_length=2, max_length=2, description="[longitude, latitude]"
    )
    station_location: list[float] | None = Field(
        None, min_length=2, max_length=2, description="[longitude, latitude]"
    )
    max_event_distance: float | None = Field(
        None,
        ge=0,
        description="Maximum distance in meters from the event location to the desired location.",
    )
    max_station_distance: float | None = Field(
        None,
        ge=0,
        description="Maximum distance in meters from the station location to the desired location.",
    )
    from_date: datetime | None = Field(None)
    to_date: datetime | None = Field(None)
    min_pga: float | None = Field(None, ge=0)
    max_pga: float | None = Field(None, ge=0)
    file_name: str | None = Field(None)
    station_code: str | None = Field(None)
    direction: str | None = Field(None)
    pagination: PaginationConfig = Field(default_factory=PaginationConfig)

    def generate_query_string(self) -> dict:
        query_dict: dict = {}

        if self.region is not None:
            query_dict["region"] = self.region.lower()

        if self.category is not None:
            query_dict["category"] = self.category.lower()

        magnitude: dict = {}
        if self.min_magnitude is not None:
            magnitude["$gte"] = self.min_magnitude
        if self.max_magnitude is not None:
            magnitude["$lte"] = self.max_magnitude
        if magnitude:
            query_dict["magnitude"] = magnitude

        if self.event_location is not None:
            # geo_json = {"$nearSphere": self.event_location, "$maxDistance": 10 / 6371}
            # if self.max_event_distance is not None:
            #     geo_json["$maxDistance"] = self.max_event_distance / 6371 / 1000
            # geo_query["event_location"] = geo_json
            max_distance = (
                self.max_event_distance
                if self.max_event_distance is not None
                else 100000.0
            )
            query_dict["event_location"] = {
                "$geoWithin": {
                    "$centerSphere": [self.event_location, max_distance / 6378100.0]
                }
            }

        if self.station_location is not None:
            # geo_json = {"$nearSphere": self.station_location, "$maxDistance": 10 / 6371}
            # if self.max_station_distance is not None:
            #     geo_json["$maxDistance"] = self.max_station_distance / 6371 / 1000
            # geo_query["station_location"] = geo_json
            max_distance = (
                self.max_station_distance
                if self.max_station_distance is not None
                else 100000.0
            )
            query_dict["station_location"] = {
                "$geoWithin": {
                    "$centerSphere": [self.station_location, max_distance / 6378100.0]
                }
            }

        date_range: dict = {}
        if self.from_date is not None:
            date_range["$gte"] = self.from_date
        if self.to_date is not None:
            date_range["$lte"] = self.to_date
        if date_range:
            query_dict["event_time"] = date_range

        pga: dict = {}
        if self.min_pga is not None:
            pga["$gte"] = self.min_pga
        if self.max_pga is not None:
            pga["$lte"] = self.max_pga
        if pga:
            query_dict["maximum_acceleration"] = pga

        if self.direction is not None:
            query_dict["direction"] = {"$regex": self.direction, "$options": "i"}

        if self.file_name is not None:
            query_dict["file_name"] = {"$regex": self.file_name, "$options": "i"}

        if self.station_code is not None:
            query_dict["station_code"] = {"$regex": self.station_code, "$options": "i"}

        return query_dict

    def generate_elastic_query(self):
        # generate a query dict that can be used in elastic search

        query_dict: dict = {"bool": {"must": []}}

        query_must = query_dict["bool"]["must"]

        if self.region is not None:
            query_must.append({"match": {"region": self.region.lower()}})

        if self.category is not None:
            query_must.append({"match": {"category": self.category.lower()}})

        magnitude_range = {}
        if self.min_magnitude is not None:
            magnitude_range["gte"] = self.min_magnitude
        if self.max_magnitude is not None:
            magnitude_range["lte"] = self.max_magnitude
        if magnitude_range:
            query_must.append({"range": {"magnitude": magnitude_range}})

        date_range = {}
        if self.from_date is not None:
            date_range["gte"] = self.from_date
        if self.to_date is not None:
            date_range["lte"] = self.to_date
        if date_range:
            query_must.append({"range": {"event_time": date_range}})

        pga_range = {}
        if self.min_pga is not None:
            pga_range["gte"] = self.min_pga
        if self.max_pga is not None:
            pga_range["lte"] = self.max_pga
        if pga_range:
            query_must.append({"range": {"maximum_acceleration": pga_range}})

        if self.event_location is not None:
            max_distance = (
                self.max_event_distance
                if self.max_event_distance is not None
                else 100000.0
            )
            query_must.append(
                {
                    "geo_distance": {
                        "distance": f"{int(max_distance)}m",
                        "event_location": {
                            "lon": self.event_location[0],
                            "lat": self.event_location[1],
                        },
                    }
                }
            )

        if self.station_location is not None:
            max_distance = (
                self.max_station_distance
                if self.max_station_distance is not None
                else 100000.0
            )
            query_must.append(
                {
                    "geo_distance": {
                        "distance": f"{int(max_distance)}m",
                        "station_location": {
                            "lon": self.station_location[0],
                            "lat": self.station_location[1],
                        },
                    }
                }
            )

        if self.direction is not None:
            query_must.append({"regexp": {"direction": self.direction}})

        if self.file_name is not None:
            query_must.append({"regexp": {"file_name": self.file_name}})

        if self.station_code is not None:
            query_must.append({"regexp": {"station_code": self.station_code}})

        return query_dict


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


class TotalResponse(BaseModel):
    total: list[int]


class BulkRequest(BaseModel):
    records: list[dict]
