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
from http import HTTPStatus
from typing import BinaryIO, IO, Tuple
from uuid import UUID

import aiofiles
import numpy as np
import pint
import structlog
from fastapi import HTTPException
from numba import jit
from pint import Quantity

from mb.app.utility import UploadTask, match_uuid
from mb.record.record import Record, to_unit

_logger = structlog.get_logger(__name__)


class NIED(Record):
    station_elevation: float = None
    station_elevation_unit: str = None
    record_time: datetime = None
    scale_factor: float = None

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
            numpy_array = self._normalise(numpy_array)
            unit = None
        else:
            numpy_array *= self.scale_factor
            unit = kwargs.get('unit', None)

        return sampling_interval, to_unit(pint.Quantity(numpy_array, self.raw_data_unit), unit)

    def to_spectrum(self, **kwargs) -> Tuple[float, np.ndarray]:
        _, waveform = self.to_waveform(normalised=False, unit=kwargs.get('unit', None))
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
            user_id: UUID,
            archive_name: str | None = None,
            task_id: UUID | None = None
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

        task: UploadTask | None = None
        if task_id is not None:
            task = await UploadTask.find_one(UploadTask.id == task_id)

        with tarfile.open(**kwargs) as archive:
            if task:
                task.total_size = len(archive.getnames())
            for f in archive:
                if task:
                    task.current_size += 1
                    await task.save()
                if not f.isfile() or f.name.endswith('.ps.gz'):
                    continue
                target = archive.extractfile(f)
                if not target:
                    continue
                try:
                    record = await ParserNIED.parse_file(target)
                    record.uploaded_by = user_id
                    record.file_name = os.path.basename(f.name)
                    record.sub_category = sub_category
                    record.set_id()
                    await record.save()
                    records.append(record.file_name)
                except Exception as e:
                    _logger.critical('Failed to parse.', file_name=f.name, exe_info=e)

        if task:
            await task.delete()

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
        record.event_location = [float(lines[2][18:]), float(lines[1][18:])]
        record.depth = Quantity(float(lines[3][18:]), _normalised_unit(lines[3])).to('km').magnitude
        record.magnitude = float(lines[4][18:])
        record.station_code = lines[5][18:]
        record.station_location = [float(lines[7][18:]), float(lines[6][18:])]
        record.station_elevation = float(lines[8][18:])
        record.station_elevation_unit = _normalised_unit(lines[8])
        record.record_time = datetime.strptime(lines[9][18:], '%Y/%m/%d %H:%M:%S')
        record.sampling_frequency = float(_parse_value(lines[10][18:]))
        record.sampling_frequency_unit = _normalised_unit(lines[10])
        record.duration = Quantity(float(lines[11][18:]), _normalised_unit(lines[11])).to('s').magnitude
        record.direction = _parse_direction(lines[12][18:])
        record.scale_factor = float(_strip_unit(lines[13][18:]))
        record.maximum_acceleration = float(lines[14][18:])
        record.raw_data_unit = _normalised_unit(lines[14])

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


@jit
def _parse_direction(line: str) -> str:
    return line.replace('-', '').upper()


def _parse_value(line: str) -> str:
    matches = re.findall(r'([0-9.]+)', line)
    if len(matches) == 0:
        raise ValueError(f'No value found in line: {line}')
    if len(matches) > 1:
        raise ValueError(f'Multiple values found in line: {line}')
    return matches[0]


def _parse_unit(line: str) -> str:
    matches = re.findall(r'\(([^)]+)\)', line)
    if len(matches) == 0:
        raise ValueError(f'No unit found in line: {line}')
    if len(matches) > 1:
        raise ValueError(f'Multiple units found in line: {line}')

    return matches[0]


async def retrieve_single_record(file_id_or_name: str | UUID, sub_category: str | None = None) -> NIED:
    if isinstance(file_id_or_name, UUID):
        return await NIED.find_one(NIED.id == file_id_or_name)

    if sub_category is None:
        if not match_uuid(file_id_or_name):
            raise HTTPException(HTTPStatus.BAD_REQUEST, detail='Invalid file ID.')

        return await NIED.find_one(NIED.id == UUID(file_id_or_name.lower()))

    return await NIED.find_one(
        NIED.file_name == file_id_or_name.upper(),
        NIED.sub_category == sub_category.lower()
    )


class MetadataNIED(NIED):
    class Settings:
        projection = {'raw_data': False}
