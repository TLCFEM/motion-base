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

import os
import re
import tarfile
from datetime import datetime
from typing import BinaryIO, IO, List, Tuple

import aiofiles
import numpy as np
import pint
import pymongo
from beanie import Indexed

from mb.app.utility import UploadTask
from mb.record.record import Record


class NIED(Record):
    station_elevation: float = None
    station_elevation_unit: str = None
    record_time: datetime = None
    scale_factor: float = None
    maximum_acceleration: Indexed(float, pymongo.DESCENDING) = None
    maximum_acceleration_unit: str = None
    raw_data: List[int] = None

    class Config:
        arbitrary_types_allowed = False

    @property
    def offset(self) -> float:
        return -sum(self.raw_data) / len(self.raw_data)

    @property
    def extrema(self) -> Tuple[float, float]:
        max_value = (max(self.raw_data) + self.offset) * self.scale_factor
        min_value = (min(self.raw_data) + self.offset) * self.scale_factor
        return min_value, max_value

    def to_raw_waveform(self, **kwargs) -> Tuple[float, list]:
        return 1 / self.sampling_frequency, self.raw_data

    def to_waveform(self, normalised: bool = False, **kwargs) -> Tuple[float, np.ndarray]:
        sampling_interval: float = 1 / self.sampling_frequency

        numpy_array: np.ndarray = np.array(self.raw_data, dtype=float) + self.offset
        if normalised:
            max_value: float = abs(np.max(numpy_array))
            min_value: float = abs(np.min(numpy_array))
            numpy_array /= max_value if max_value > min_value else min_value
        else:
            numpy_array *= self.scale_factor

        return sampling_interval, numpy_array

    def to_spectrum(self, **kwargs) -> Tuple[float, np.ndarray]:
        _, waveform = self.to_waveform(normalised=False)
        return self._perform_fft(self.sampling_frequency, waveform)


class ParserNIED:
    @staticmethod
    def validate_archive(archive_name: str):
        if not archive_name.endswith('.tar.gz'):
            raise ValueError('NIED archive file should be a tar.gz file.')

        if 'knt' not in archive_name and 'kik' not in archive_name:
            raise ValueError('NIED archive file name should contain knt or kik.')

    @staticmethod
    async def parse_archive(
            archive_obj: str | BinaryIO,
            archive_name: str | None = None,
            task: UploadTask | None = None
    ) -> list[str]:
        if not isinstance(archive_obj, str) and archive_name is None:
            raise ValueError('Need archive name if archive is provided as a BinaryIO.')

        name_string = archive_name if archive_name is not None else archive_obj
        sub_category = 'knt' if 'knt' in name_string else 'kik'

        records = []
        if isinstance(archive_obj, str):
            kwargs = dict(name=archive_obj, mode='r:gz')
        else:
            kwargs = dict(mode='r:gz', fileobj=archive_obj)

        if task is None:
            task = UploadTask()

        with tarfile.open(**kwargs) as archive:
            task.total_size = len(archive.getnames())
            for f in archive:
                task.current_size += 1
                if not f.isfile() or f.name.endswith('.ps.gz'):
                    continue
                target = archive.extractfile(f)
                if not target:
                    continue
                record = await ParserNIED.parse_file(target)
                record.file_name = os.path.basename(f.name)
                record.sub_category = sub_category
                record.set_id()
                await record.save()
                records.append(record.file_name)

        return records

    @staticmethod
    async def parse_file(file_path: str | IO[bytes]) -> NIED:
        if isinstance(file_path, str):
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                lines = await f.readlines()

            lines = [line.strip() for line in lines]
        else:
            lines = [line.decode('utf-8').strip() for line in file_path.readlines()]

        record = NIED()
        record.origin_time = datetime.strptime(lines[0][18:], '%Y/%m/%d %H:%M:%S')
        record.latitude = float(lines[1][18:])
        record.longitude = float(lines[2][18:])
        record.depth = float(lines[3][18:])
        record.depth_unit = _normalised_unit(lines[3])
        record.magnitude = float(lines[4][18:])
        record.station_code = lines[5][18:]
        record.station_latitude = float(lines[6][18:])
        record.station_longitude = float(lines[7][18:])
        record.station_elevation = float(lines[8][18:])
        record.station_elevation_unit = _normalised_unit(lines[8])
        record.record_time = datetime.strptime(lines[9][18:], '%Y/%m/%d %H:%M:%S')
        record.sampling_frequency = float(_parse_value(lines[10][18:]))
        record.sampling_frequency_unit = _normalised_unit(lines[10])
        record.duration = float(lines[11][18:])
        record.duration_unit = _normalised_unit(lines[11])
        record.direction = _parse_direction(lines[12][18:])
        record.scale_factor = float(_strip_unit(lines[13][18:]))
        record.maximum_acceleration = float(lines[14][18:])
        record.maximum_acceleration_unit = _normalised_unit(lines[14])

        record.raw_data = [int(value) for line in lines[17:] for value in line.split()]

        return record


def _normalised_unit(line: str) -> str:
    unit = _parse_unit(line)
    if unit == 'gal':
        unit = unit.capitalize()
    return str(pint.Unit(unit))


def _strip_unit(line: str) -> float:
    try:
        unit = _parse_unit(line)
        numerator, denominator = line.replace(f'({unit})', '').split('/')
    except ValueError:
        numerator, denominator = line.split('/')

    return float(numerator) / float(denominator)


def _parse_direction(line: str) -> str:
    return line.replace('-', '').upper()


def _parse_value(line: str) -> str:
    regex = r'([0-9.]+)'
    matches = re.findall(regex, line)
    if len(matches) == 0:
        raise ValueError(f'No value found in line: {line}')
    if len(matches) > 1:
        raise ValueError(f'Multiple values found in line: {line}')
    return matches[0]


def _parse_unit(line: str) -> str:
    regex = r'\(([^)]+)\)'
    matches = re.findall(regex, line)
    if len(matches) == 0:
        raise ValueError(f'No unit found in line: {line}')
    if len(matches) > 1:
        raise ValueError(f'Multiple units found in line: {line}')

    return matches[0]


async def retrieve_single_record(sub_category: str, file_name: str) -> Record:
    result: Record = await NIED.find_one(
        NIED.sub_category == sub_category,
        NIED.file_name == file_name)
    return result


if __name__ == '__main__':
    pass
