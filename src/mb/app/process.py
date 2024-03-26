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

from http import HTTPStatus

import numpy as np
from fastapi import HTTPException

from .response import ProcessConfig, ProcessedResponse
from ..record.async_record import Record
from ..record.response_spectrum import response_spectrum
from ..record.utility import apply_filter, get_window, zero_stuff, perform_fft


def processing_record(result: Record, process_config: ProcessConfig):
    if process_config.low_cut >= process_config.high_cut:
        raise HTTPException(
            HTTPStatus.BAD_REQUEST, detail="Low cut frequency should be smaller than high cut frequency."
        )

    record = ProcessedResponse(**result.dict(), endpoint="/process", process_config=process_config)

    time_interval, waveform = result.to_waveform(normalised=process_config.normalised, unit="cm/s/s")

    if process_config.with_filter:
        new_interval = time_interval / process_config.ratio

        float_eps = float(np.finfo(np.float32).eps)

        f0 = min(max(2 * process_config.low_cut * new_interval, float_eps), 1 - float_eps)
        f1 = min(max(2 * process_config.high_cut * new_interval, f0 + float_eps), 1 - float_eps)

        freq_list: float | list[float]
        if process_config.filter_type in ("bandpass", "bandstop"):
            freq_list = [f0, f1]
        elif process_config.filter_type == "lowpass":
            freq_list = f1
        elif process_config.filter_type == "highpass":
            freq_list = f0
        else:
            raise HTTPException(
                HTTPStatus.BAD_REQUEST, detail="Filter type should be one of bandpass, bandstop, lowpass and highpass."
            )
        new_waveform: np.ndarray = apply_filter(
            get_window(
                process_config.filter_type,
                process_config.window_type,
                process_config.filter_length,
                freq_list,
                ratio=process_config.ratio,
            ),
            zero_stuff(process_config.ratio, waveform),
        )
    else:
        new_interval = time_interval
        new_waveform = waveform

    record.time_interval = new_interval
    record.waveform = new_waveform.tolist()

    if process_config.with_spectrum:
        frequency_interval, spectrum = perform_fft(1 / new_interval, new_waveform)
        record.frequency_interval = frequency_interval
        record.spectrum = spectrum.tolist()

    if process_config.with_response_spectrum:
        period = np.arange(0, process_config.period_end + process_config.period_step, process_config.period_step)
        spectrum = response_spectrum(process_config.damping_ratio, new_interval, new_waveform, period)
        record.period = period.tolist()
        record.displacement_spectrum = spectrum[:, 0].tolist()
        record.velocity_spectrum = spectrum[:, 1].tolist()
        record.acceleration_spectrum = spectrum[:, 2].tolist()

    return record
