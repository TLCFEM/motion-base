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
from beanie import Document, Indexed
from numba import njit
from pydantic import Field
from scipy import signal

DESCENDING = -1
GEOSPHERE = '2dsphere'


class Record(Document):
    id: UUID = Field(default_factory=uuid4)
    uploaded_by: UUID = Field(default_factory=uuid4)
    file_name: Indexed(str) = None
    sub_category: Indexed(str) = None
    magnitude: Indexed(float, DESCENDING) = None
    origin_time: Indexed(datetime, DESCENDING) = None
    event_location: Indexed(list[float, float], GEOSPHERE) = None
    depth: Indexed(float) = None  # in kilometer
    station_code: str = None
    station_location: Indexed(list[float, float], GEOSPHERE) = None
    sampling_frequency: float = None
    sampling_frequency_unit: str = None
    duration: float = None  # in seconds
    direction: Indexed(str) = None
    maximum_acceleration: Indexed(float, DESCENDING) = None  # PGA in Gal
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
    def perform_fft(sampling_frequency: float, magnitude: np.ndarray) -> Tuple[float, np.ndarray]:
        fft_magnitude: np.ndarray = 2 * np.abs(np.fft.rfft(magnitude)) / len(magnitude)
        return sampling_frequency / magnitude.size, fft_magnitude

    @staticmethod
    @njit
    def _normalise(magnitude: np.ndarray) -> np.ndarray:
        max_value: float = abs(np.max(magnitude))
        min_value: float = abs(np.min(magnitude))
        magnitude /= max_value if max_value > min_value else min_value
        return magnitude


def to_unit(quantity: pint.Quantity, unit: pint.Unit):
    if unit:
        return quantity.to(unit).magnitude

    return quantity.magnitude


def apply_filter(window, waveform: np.ndarray) -> np.ndarray:
    return np.convolve(waveform, window, mode='same')


@njit
def zero_stuff(ratio: int, waveform: np.ndarray) -> np.ndarray:
    if ratio == 1:
        return waveform
    output: np.ndarray = np.zeros(len(waveform) * ratio)
    output[::ratio] = waveform
    return output


filter_regex = '^(lowpass|highpass|bandpass|bandstop)$'
window_regex = '^(flattop|blackmanharris|nuttall|hann|hamming|kaiser|chebwin)$'


def get_window(filter_type: str, window_type: str, length: int, cutoff: float | list[float], **kwargs) -> np.ndarray:
    if window_type == 'flattop':
        window = ('flattop',)
    elif window_type == 'blackmanharris':
        window = ('blackmanharris',)
    elif window_type == 'nuttall':
        window = ('nuttall',)
    elif window_type == 'hann':
        window = ('hann',)
    elif window_type == 'hamming':
        window = ('hamming',)
    elif window_type == 'kaiser':
        beta = kwargs.get('beta', 9)
        window = ('kaiser', beta)
    elif window_type == 'chebwin':
        at = kwargs.get('at', 80)
        window = ('chebwin', at)
    else:
        raise ValueError(f'Unknown window type: {window_type}')

    bin_num = 2 * length + 1

    return signal.firwin(bin_num, cutoff, window=window, pass_zero=filter_type) * kwargs.get('ratio', 1)
