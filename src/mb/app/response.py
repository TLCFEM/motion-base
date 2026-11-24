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

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Literal

import numpy as np
from pydantic import BaseModel, Field, field_validator, model_validator

from ..record.integrator import IntegrationType


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

    @model_validator(mode="before")
    @classmethod
    def allow_default_none(cls, data):
        if not isinstance(data, dict):
            return data
        return {k: v for k, v in data.items() if v is not None}


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

    displacement_unit: str = Field(None)
    velocity_unit: str = Field(None)
    displacement: list[float] = Field(None)
    velocity: list[float] = Field(None)

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
        from ..record.utility import apply_filter

        self.time_interval /= up_ratio
        self.waveform = apply_filter(
            np.asarray(window) * up_ratio, self.waveform, up_ratio
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
        from ..record.response_spectrum import response_spectrum

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


class SortBy(StrEnum):
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


# noinspection SpellCheckingInspection
class IntegrationConfig(BaseModel):
    """Parameters of the time integration scheme.

    The scheme is selected with ``integration_type``.  Only the parameters
    used by the selected scheme are read; the remaining ones are ignored.  A
    missing parameter keeps the default of the corresponding integrator.
    """

    integration_type: IntegrationType = Field(
        IntegrationType.Newmark,
        description="The time integration scheme, for example `Newmark` or `BatheTwoStep`.",
    )
    gamma: float | None = Field(
        None, description="Velocity weighting factor of the Newmark-like schemes."
    )
    beta: float | None = Field(
        None, description="Displacement weighting factor of the Newmark-like schemes."
    )
    spectral_radius: float | None = Field(
        None, description="Spectral radius at infinity of the single-parameter schemes."
    )
    alpha_f: float | None = Field(
        None, description="Stiffness-weighted alpha parameter of GeneralizedAlpha."
    )
    alpha_m: float | None = Field(
        None, description="Mass-weighted alpha parameter of GeneralizedAlpha."
    )
    r1: float | None = Field(
        None, description="First spectral radius of the GSSSS U0/V0 schemes."
    )
    r2: float | None = Field(
        None, description="Second spectral radius of the GSSSS U0/V0 schemes."
    )
    r3: float | None = Field(
        None, description="Third spectral radius of the GSSSS U0/V0 schemes."
    )
    rs: float | None = Field(
        None, description="Spectral radius of the explicit stage of GSSE."
    )
    rb: float | None = Field(
        None, description="Spectral radius of the final stage of GSSE."
    )
    parameter: float | None = Field(None, description="Scheme parameter of WAT2.")

    @model_validator(mode="before")
    @classmethod
    def normalise_parameters(cls, data):
        if data is None:
            return {}
        if isinstance(data, (str, IntegrationType)):
            return {"integration_type": data}
        if not isinstance(data, dict):
            return data

        data = dict(data)

        for container in (
            "parameters",
            "params",
            "integration_parameters",
            "integration_params",
        ):
            extra = data.pop(container, None)
            if isinstance(extra, dict):
                for key, value in extra.items():
                    data.setdefault(key, value)

        type_value = None
        for key in ("integration_type", "type", "method", "name", "integration_method"):
            if key in data:
                value = data.pop(key)
                if type_value is None:
                    type_value = value
        if type_value is not None:
            data["integration_type"] = type_value

        for alias in ("rho_inf", "rho", "rho_infinity", "spectral_radius_inf"):
            if alias in data:
                data.setdefault("spectral_radius", data.pop(alias))

        for alias in ("radii", "spectral_radii", "r"):
            if alias in data:
                radii = data.pop(alias)
                if np.ndim(radii) == 0:
                    for key in ("r1", "r2", "r3"):
                        data.setdefault(key, radii)
                elif len(radii) == 3:
                    for key, value in zip(("r1", "r2", "r3"), radii, strict=True):
                        data.setdefault(key, value)
                else:
                    raise ValueError("Exactly three spectral radii are required.")

        if "wat2_parameter" in data:
            data.setdefault("parameter", data.pop("wat2_parameter"))

        return data

    def create_integrator(self):
        """Create the configured time integrator."""
        from ..record.integrator import create_integrator

        return create_integrator(
            self.integration_type,
            **self.model_dump(exclude={"integration_type"}, exclude_none=True),
        )


# noinspection SpellCheckingInspection
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
    filter_type: Literal["lowpass", "highpass", "bandpass", "bandstop"] = Field(
        "bandpass",
        description="filter type, any of `lowpass`, `highpass`, `bandpass`, `bandstop`",
    )
    window_type: Literal[
        "flattop", "blackmanharris", "nuttall", "hann", "hamming", "kaiser", "chebwin"
    ] = Field(
        "nuttall",
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
    with_integration: bool = Field(
        False,
        description="Integrate the processed acceleration to obtain velocity and displacement.",
    )
    integration: IntegrationConfig = Field(
        default_factory=IntegrationConfig,
        description="Time integration scheme and its parameters.",
    )
    remove_head: float = Field(0.0, ge=0)

    @model_validator(mode="before")
    @classmethod
    def collect_integration(cls, data):
        """Accept the integration settings nested or as flat convenience fields."""
        if not isinstance(data, dict):
            return data

        data = dict(data)

        for alias in ("with_time_integration", "integrate"):
            if alias in data:
                data.setdefault("with_integration", data.pop(alias))

        nested = None
        for key in ("integration", "time_integration", "integration_config"):
            if key in data:
                value = data.pop(key)
                if isinstance(value, bool):
                    data.setdefault("with_integration", value)
                else:
                    nested = value
                break

        known = {
            "integration_type",
            "type",
            "method",
            "name",
            "integration_method",
            "gamma",
            "beta",
            "spectral_radius",
            "rho_inf",
            "rho",
            "rho_infinity",
            "spectral_radius_inf",
            "alpha_f",
            "alpha_m",
            "r1",
            "r2",
            "r3",
            "radii",
            "spectral_radii",
            "r",
            "rs",
            "rb",
            "parameter",
            "parameters",
            "params",
            "integration_parameters",
            "integration_params",
        }

        flat: dict = {}
        for key in list(data):
            if key.startswith("integration_"):
                target = key[len("integration_") :]
                if target in ("type", "method", "name"):
                    target = "integration_type"
                elif target in ("parameters", "params"):
                    target = "parameters"
                if target in known:
                    flat[target] = data.pop(key)

        for key in list(data):
            if key in known:
                flat[key] = data.pop(key)

        if nested is not None or flat:
            if isinstance(nested, IntegrationConfig):
                nested_values = nested.model_dump(exclude_none=True)
            elif isinstance(nested, dict):
                nested_values = dict(nested)
            elif nested is not None:
                nested_values = {"integration_type": nested}
            else:
                nested_values = {}

            data["integration"] = {**flat, **nested_values}
            data.setdefault("with_integration", True)

        return data

    @property
    def integration_config(self) -> IntegrationConfig:
        """Alias of :attr:`integration`."""
        return self.integration

    @property
    def integration_type(self) -> IntegrationType:
        """The configured time integration scheme."""
        return self.integration.integration_type

    @integration_type.setter
    def integration_type(self, value: IntegrationType | str):
        self.integration.integration_type = IntegrationType(value)

    @property
    def integration_method(self) -> IntegrationType:
        """Alias of :attr:`integration_type`."""
        return self.integration.integration_type

    @property
    def integration_parameters(self) -> dict[str, float]:
        """The explicitly configured scheme parameters."""
        return self.integration.model_dump(
            exclude={"integration_type"}, exclude_none=True
        )

    @property
    def time_integration(self) -> IntegrationConfig:
        """Alias of :attr:`integration`."""
        return self.integration


class ProcessedResponse(RecordResponse):
    process_config: ProcessConfig


class UploadResponse(BaseModel):
    message: str
    task_ids: list | None = Field(None)
    records: list | None = Field(None)


class QueryConfig(BaseModel):
    region: Literal["jp", "nz"] | None = Field(None)
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

        def _regex(key, value):
            return {"regexp": {key: {"value": value, "case_insensitive": True}}}

        if self.direction is not None:
            query_must.append(_regex("direction", self.direction))

        if self.file_name is not None:
            query_must.append(_regex("file_name", self.file_name))

        if self.station_code is not None:
            query_must.append(_regex("station_code", self.station_code))

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
