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


import numpy as np
import pint
import pytest

from mb.record.response_spectrum import Newmark, sdof_response
from mb.record.utility import (
    apply_filter,
    convert_to,
    get_window,
    normalise,
    perform_fft,
    zero_stuff,
)


def test_integrate_newmark():
    Newmark().integrate(0.05, np.random.rand(10))


def test_sdof():
    sdof_response(0.05, 0.01, 12.0, np.random.rand(1000))


def test_perform_fft():
    magnitude = np.array([1.0, 0.0, -1.0, 0.0, 1.0, 0.0, -1.0, 0.0])
    interval, spectrum = perform_fft(100.0, magnitude)

    assert interval == pytest.approx(12.5)
    assert spectrum.shape == (5,)


@pytest.mark.parametrize(
    "motion,expected",
    [
        ([1.0, -2.0, 3.0], [1 / 3, -2 / 3, 1.0]),
        ([-1.0, 0.5], [-1.0, 0.5]),
    ],
)
def test_normalise(motion, expected):
    result = normalise(np.array(motion, dtype=float))

    assert result == pytest.approx(expected)


def test_convert_to():
    quantity = pint.Quantity(np.array([1.0, 2.0]), "m/s**2")

    assert convert_to(quantity, None) == pytest.approx([1.0, 2.0])
    assert convert_to(quantity, "Gal") == pytest.approx([100.0, 200.0])


def test_apply_filter():
    waveform = np.array([1.0, 2.0, 3.0])

    assert apply_filter(np.array([1.0]), waveform) == pytest.approx(waveform)


def test_zero_stuff():
    assert zero_stuff(1, [1.0, 2.0]) == pytest.approx([1.0, 2.0])
    assert zero_stuff(1, np.array([1.0, 2.0])) == pytest.approx([1.0, 2.0])
    assert zero_stuff(2, np.array([1.0, 2.0])) == pytest.approx(
        [1.0, 0.0, 2.0, 0.0]
    )


@pytest.mark.parametrize(
    "window_type,kwargs",
    [
        ("flattop", {}),
        ("blackmanharris", {}),
        ("nuttall", {}),
        ("hann", {}),
        ("hamming", {}),
        ("kaiser", {"beta": 4}),
        ("chebwin", {"at": 60}),
    ],
)
def test_get_window(window_type, kwargs):
    window = get_window("lowpass", window_type, 4, 0.1, ratio=2, **kwargs)

    assert window.shape == (9,)
    assert np.all(np.isfinite(window))


def test_get_window_bandpass_and_bad_type():
    window = get_window("bandpass", "hann", 4, [0.1, 0.2])
    assert window.shape == (9,)

    with pytest.raises(ValueError, match="Unknown window type"):
        get_window("lowpass", "unknown", 4, 0.1)
