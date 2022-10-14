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
from typing import List, Tuple
from uuid import NAMESPACE_OID, UUID, uuid4, uuid5

import numpy as np
import pint
import pymongo
from beanie import Document, Indexed
from pydantic import Field


class Record(Document):
    id: UUID = Field(default_factory=uuid4)
    uploaded_by: UUID = Field(default_factory=uuid4)
    file_name: Indexed(str) = None
    sub_category: Indexed(str) = None
    magnitude: Indexed(float, pymongo.DESCENDING) = None
    origin_time: datetime = None
    latitude: float = None
    longitude: float = None
    depth: float = None
    depth_unit: str = None
    station_code: str = None
    station_latitude: float = None
    station_longitude: float = None
    sampling_frequency: float = None
    sampling_frequency_unit: str = None
    duration: float = None
    duration_unit: str = None
    direction: str = None
    raw_data: List[int] = None
    raw_data_unit: str = None

    def set_id(self, id_seed: str | None = None):
        if id_seed is None:
            id_seed = self.file_name

        self.id = uuid5(NAMESPACE_OID, id_seed)

    @property
    def collection_name(self):
        return self.__class__.__name__.upper()

    def to_raw_waveform(self, **kwargs) -> Tuple[float, list]:
        raise NotImplementedError()

    def to_waveform(self, normalised: bool = False, **kwargs) -> Tuple[float, np.ndarray]:
        raise NotImplementedError()

    def to_spectrum(self, **kwargs) -> Tuple[float, np.ndarray]:
        raise NotImplementedError()

    @staticmethod
    def _perform_fft(sampling_frequency: float, magnitude: np.ndarray) -> Tuple[float, np.ndarray]:
        fft_magnitude: np.ndarray = 2 * np.abs(np.fft.rfft(magnitude)) / len(magnitude)
        return 1 / sampling_frequency, fft_magnitude

    @staticmethod
    def _normalise(magnitude: np.ndarray) -> np.ndarray:
        max_value: float = abs(np.max(magnitude))
        min_value: float = abs(np.min(magnitude))
        magnitude /= max_value if max_value > min_value else min_value
        return magnitude


def to_unit(quantity: pint.Quantity, unit: pint.Unit):
    if unit:
        return quantity.to(unit).magnitude

    return quantity.magnitude
