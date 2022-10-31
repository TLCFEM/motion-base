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
from http import HTTPStatus

import numpy as np
from fastapi import HTTPException

from mb.app.response import SequenceSpectrumResponse
from mb.record.jp import NIED
from mb.record.record import Record, apply_filter, get_window, zero_stuff
from mb.record.response_spectrum import response_spectrum


def processing_record(
        result: Record,
        upsampling_rate: int | None,
        filter_length: int | None,
        filter_type: str | None,
        window_type: str | None,
        low_cut: float | None,
        high_cut: float | None,
        damping_ratio: float | None,
        period_end: float | None,
        period_step: float | None,
        normalised: bool | None,
        with_filter: bool | None,
        with_spectrum: bool | None,
        with_response_spectrum: bool | None
) -> SequenceSpectrumResponse:
    if with_filter is None:
        with_filter = False
    if with_spectrum is None:
        with_spectrum = False
    if with_response_spectrum is None:
        with_response_spectrum = False

    if upsampling_rate is None:
        upsampling_rate = 1
    if filter_length is None:
        filter_length = 8
    if filter_type is None:
        filter_type = 'bandpass'
    if window_type is None:
        window_type = 'nuttall'
    if low_cut is None:
        low_cut = .05
    if high_cut is None:
        high_cut = 40.

    if low_cut >= high_cut:
        raise HTTPException(
            HTTPStatus.BAD_REQUEST,
            detail='Low cut frequency should be smaller than high cut frequency.')

    if damping_ratio is None:
        damping_ratio = 0.05
    if period_end is None:
        period_end = 20.
    if period_step is None:
        period_step = 0.05
    if normalised is None:
        normalised = False

    record = SequenceSpectrumResponse(**result.dict(), processing_parameters={
        'upsampling_rate': upsampling_rate,
        'filter_length': filter_length,
        'filter_type': filter_type,
        'window_type': window_type,
        'low_cut': low_cut,
        'high_cut': high_cut,
        'damping_ratio': damping_ratio,
        'period_end': period_end,
        'period_step': period_step,
        'normalised': normalised,
        'with_filter': with_filter,
        'with_spectrum': with_spectrum,
        'with_response_spectrum': with_response_spectrum
    })

    time_interval, waveform = result.to_waveform(normalised=normalised, unit='cm/s/s')

    if with_filter:
        upsampled_interval = time_interval / upsampling_rate

        f0 = min(max(2 * low_cut * upsampled_interval, np.finfo(np.float32).eps), 1 - np.finfo(np.float32).eps)
        f1 = min(max(2 * high_cut * upsampled_interval, f0 + np.finfo(np.float32).eps), 1 - np.finfo(np.float32).eps)

        freq_list: float | list[float]
        if filter_type in ('bandpass', 'bandstop'):
            freq_list = [f0, f1]
        elif filter_type == 'lowpass':
            freq_list = f1
        elif filter_type == 'highpass':
            freq_list = f0
        else:
            raise HTTPException(
                HTTPStatus.BAD_REQUEST,
                detail='Filter type should be one of bandpass, bandstop, lowpass and highpass.')
        new_waveform: np.ndarray = apply_filter(
            get_window(filter_type, window_type, filter_length, freq_list, ratio=upsampling_rate),
            zero_stuff(upsampling_rate, waveform))
    else:
        upsampled_interval = time_interval
        new_waveform = waveform

    record.time_interval = upsampled_interval
    record.waveform = new_waveform.tolist()

    if with_spectrum:
        frequency_interval, spectrum = NIED.perform_fft(1 / upsampled_interval, new_waveform)
        record.frequency_interval = frequency_interval
        record.spectrum = spectrum.tolist()

    if with_response_spectrum:
        period = np.arange(0, period_end + period_step, period_step)
        spectrum = response_spectrum(damping_ratio, upsampled_interval, new_waveform, period)
        record.period = period.tolist()
        record.displacement_spectrum = spectrum[:, 0].tolist()
        record.velocity_spectrum = spectrum[:, 1].tolist()
        record.acceleration_spectrum = spectrum[:, 2].tolist()

    return record
