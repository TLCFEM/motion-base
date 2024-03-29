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

from uuid import uuid4, NAMESPACE_OID, uuid5

import numpy as np
import pint
from numba import njit
from scipy import signal


def perform_fft(sampling_frequency: float, magnitude: np.ndarray) -> (float, np.ndarray):
    fft_magnitude: np.ndarray = 2 * np.abs(np.fft.rfft(magnitude)) / len(magnitude)
    return sampling_frequency / magnitude.size, fft_magnitude


@njit
def normalise(magnitude: np.ndarray) -> np.ndarray:
    max_value: float = abs(np.max(magnitude))
    min_value: float = abs(np.min(magnitude))
    magnitude /= max_value if max_value > min_value else min_value
    return magnitude


def convert_to(quantity: pint.Quantity, unit: pint.Unit | None):
    return quantity.to(unit).magnitude if unit else quantity.magnitude


@njit
def apply_filter(window, waveform: np.ndarray) -> np.ndarray:
    return np.convolve(waveform, window, mode="same")


@njit
def zero_stuff(ratio: int, waveform: np.ndarray | list[float]) -> np.ndarray:
    if ratio == 1:
        return np.array(waveform) if isinstance(waveform, list) else waveform
    output: np.ndarray = np.zeros(len(waveform) * ratio)
    output[::ratio] = waveform
    return output


filter_regex = "^(lowpass|highpass|bandpass|bandstop)$"
window_regex = "^(flattop|blackmanharris|nuttall|hann|hamming|kaiser|chebwin)$"


def get_window(filter_type: str, window_type: str, length: int, cutoff: float | list[float], **kwargs) -> np.ndarray:
    if window_type == "flattop":
        window = ("flattop",)
    elif window_type == "blackmanharris":
        window = ("blackmanharris",)
    elif window_type == "nuttall":
        window = ("nuttall",)
    elif window_type == "hann":
        window = ("hann",)
    elif window_type == "hamming":
        window = ("hamming",)
    elif window_type == "kaiser":
        window = ("kaiser", kwargs.get("beta", 9))
    elif window_type == "chebwin":
        window = ("chebwin", kwargs.get("at", 80))
    else:
        raise ValueError(f"Unknown window type: {window_type}.")

    return signal.firwin(2 * length + 1, cutoff, window=window, pass_zero=filter_type) * kwargs.get("ratio", 1)


def str_factory():
    return str(uuid4())


def uuid5_str(token: str) -> str:
    return str(uuid5(NAMESPACE_OID, token))
