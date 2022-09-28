import os
import re
from datetime import datetime
from math import ceil
from typing import IO, List, Tuple

import aiofiles
import numpy as np
import pint
import pymongo
import structlog
from beanie import Indexed

from mb.record.record import Record, to_unit

_FTI_ = 10000

_logger = structlog.get_logger(__name__)


class NZSM(Record):
    record_time: datetime = None
    scale_factor: float = 1 / _FTI_
    maximum_acceleration: Indexed(float, pymongo.DESCENDING) = None
    maximum_acceleration_unit: str = None
    raw_data: List[int] = None

    def to_raw_waveform(self, **kwargs) -> Tuple[float, list]:
        return 1 / self.sampling_frequency, self.raw_data

    def to_waveform(self, normalised: bool = False, **kwargs) -> Tuple[float, np.ndarray]:
        sampling_interval: float = 1 / self.sampling_frequency

        numpy_array: np.ndarray = np.array(self.to_raw_waveform(**kwargs)[1], dtype=float)
        if normalised:
            max_value: float = abs(np.max(numpy_array))
            min_value: float = abs(np.min(numpy_array))
            numpy_array /= max_value if max_value > min_value else min_value
            unit = None
        else:
            numpy_array *= self.scale_factor
            unit = kwargs.get('unit', None)

        return sampling_interval, to_unit(pint.Quantity(numpy_array, self.maximum_acceleration_unit), unit)

    def to_spectrum(self, **kwargs) -> Tuple[float, np.ndarray]:
        _, waveform = self.to_waveform(**kwargs)
        return self._perform_fft(self.sampling_frequency, waveform)


class ParserNZSM:
    @staticmethod
    def validate_file(file_path: str):
        if file_path.lower().endswith('.v2a'):
            return
        if file_path.lower().endswith('.v1a'):
            return

        raise ValueError('NZSM archive file should be a V2A/V1A file.')

    @staticmethod
    async def parse_archive(file_path: str | IO[bytes], file_name: str | None = None) -> List[str]:
        if isinstance(file_path, str):
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                lines = await f.readlines()
        else:
            if file_name is None:
                raise ValueError('File name is required when a stream is provided.')
            lines = [line.decode('utf-8') for line in file_path.readlines()]

        while True:
            if lines[-1].strip() != '':
                break
            lines.pop()

        num_lines = len(lines) // 3

        assert 3 * num_lines == len(lines), 'Number of lines should be a multiple of 3.'

        record_names: List[str] = []
        pattern = re.compile(r'(\d{8})_(\d{6})_(\w{3,4})_?')
        matches = pattern.search(lines[0])

        async def _populate_common_fields(record: NZSM):
            record.origin_time = datetime.strptime(matches[1] + matches[2], '%Y%m%d%H%M%S')
            record.station_code = matches[3]
            record.depth_unit = str(pint.Unit('km'))
            record.sampling_frequency_unit = str(pint.Unit('Hz'))
            record.maximum_acceleration_unit = str(pint.Unit('mm/s/s'))
            record.duration_unit = str(pint.Unit('s'))
            record.file_name = os.path.basename(file_name if file_name else file_path)
            record.sub_category = 'processed' if record.file_name.endswith('.V2A') else 'unprocessed'
            record.set_id(record.file_name + record.direction)
            await record.save()
            record_names.append(record.file_name)

        await _populate_common_fields(ParserNZSM.parse_file(lines[:num_lines]))
        await _populate_common_fields(ParserNZSM.parse_file(lines[num_lines:2 * num_lines]))
        await _populate_common_fields(ParserNZSM.parse_file(lines[2 * num_lines:]))

        return record_names

    @staticmethod
    def parse_file(lines: List[str]) -> NZSM:
        record = NZSM()

        int_header, float_header = _parse_header(lines)

        record.latitude = -float_header[12]
        record.longitude = float_header[13]
        record.depth = int_header[16]
        record.magnitude = float_header[16]
        record.station_latitude = -float_header[10]
        record.station_longitude = float_header[11]
        record.sampling_frequency = 1 / _parse_interval(lines[10])

        record.duration = float_header[23]
        record.direction = lines[12].split()[1]
        record.maximum_acceleration = float_header[35]

        offset: int = 26
        a_samples = int_header[33]
        a_lines = ceil(a_samples / 10)
        record.raw_data = [
            int(_FTI_ * float(v)) for line in lines[offset:offset + a_lines] for v in _fixed_size_split(line, 8)
        ]

        return record


def _parse_interval(line: str):
    pattern = re.compile(r'\s(\d+\.\d+)\s')
    matches = pattern.search(line)
    if matches:
        return float(matches[1])

    raise ValueError('Sampling frequency/interval not found.')


def _fixed_size_split(line: str, size: int = 8) -> List[str]:
    line = line.replace('\n', '')
    return [line[i:i + size] for i in range(0, len(line), size)]


def _parse_header(lines: List[str]) -> (list, list):
    int_header = [int(v) for line in lines[16:  20] for v in _fixed_size_split(line)]
    float_header = [float(v) for line in lines[20: 26] for v in _fixed_size_split(line)]
    return int_header, float_header


async def retrieve_single_record(file_name: str) -> NZSM:
    return await NZSM.find_one(NZSM.file_name == file_name)
