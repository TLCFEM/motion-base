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

import os
import re
import tarfile
from datetime import datetime
from math import ceil
from typing import BinaryIO, IO
from uuid import UUID

import aiofiles
import pint
import structlog

from .record import NIED, NZSM
from ..app.utility import UploadTask

_logger = structlog.get_logger(__name__)


class ParserNIED:
    @staticmethod
    def validate_archive(archive_name: str):
        if not archive_name.endswith(".tar.gz"):
            raise ValueError("NIED archive file should be a .tar.gz file.")

        if "knt" not in archive_name and "kik" not in archive_name:
            raise ValueError("NIED archive file name should contain knt or kik.")

    @staticmethod
    async def parse_archive(
        archive_obj: str | BinaryIO, user_id: UUID, archive_name: str | None = None, task_id: UUID | None = None
    ) -> list[str]:
        if not isinstance(archive_obj, str) and archive_name is None:
            raise ValueError("Need archive name if archive is provided as a BinaryIO.")

        name_string = archive_name if archive_name is not None else archive_obj
        category = "knt" if "knt" in name_string else "kik"

        kwargs: dict = {"mode": "r:gz"}
        if isinstance(archive_obj, str):
            kwargs["name"] = archive_obj
        else:
            kwargs["fileobj"] = archive_obj

        task: UploadTask | None = None
        if task_id is not None:
            task = await UploadTask.find_one(UploadTask.id == task_id)

        records = []
        with tarfile.open(**kwargs) as archive:
            if task:
                task.pid = os.getpid()
                task.total_size = len(archive.getnames())
            for f in archive:
                if task:
                    task.current_size += 1
                    await task.save()
                if not f.isfile() or f.name.endswith(".ps.gz"):
                    continue
                target = archive.extractfile(f)
                if not target:
                    continue
                try:
                    record = await ParserNIED.parse_file(target)
                    record.uploaded_by = user_id
                    record.file_name = os.path.basename(f.name)
                    record.category = category
                    await record.save()
                    records.append(record.file_name)
                except Exception as e:
                    _logger.critical("Failed to parse.", file_name=f.name, exc_info=e)

        if task:
            await task.delete()

        return records

    @staticmethod
    async def parse_file(file_path: str | IO[bytes]) -> NIED:
        if isinstance(file_path, str):
            async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                lines = await f.readlines()

            lines = [line.strip() for line in lines]
        else:
            lines = [line.decode("utf-8").strip() for line in file_path.readlines()]

        record = NIED()
        record.event_time = datetime.strptime(lines[0][18:], "%Y/%m/%d %H:%M:%S")
        record.event_location = [float(lines[2][18:]), float(lines[1][18:])]
        record.depth = pint.Quantity(float(lines[3][18:]), ParserNIED._normalise_unit(lines[3])).to("km").magnitude
        record.magnitude = float(lines[4][18:])
        record.station_code = lines[5][18:]
        record.station_location = [float(lines[7][18:]), float(lines[6][18:])]
        record.station_elevation = float(lines[8][18:])
        record.station_elevation_unit = ParserNIED._normalise_unit(lines[8])
        record.record_time = datetime.strptime(lines[9][18:], "%Y/%m/%d %H:%M:%S")
        record.sampling_frequency = float(ParserNIED._parse_value(lines[10][18:]))
        record.sampling_frequency_unit = ParserNIED._normalise_unit(lines[10])
        record.duration = pint.Quantity(float(lines[11][18:]), ParserNIED._normalise_unit(lines[11])).to("s").magnitude
        record.direction = ParserNIED._parse_direction(lines[12][18:])
        record.scale_factor = float(ParserNIED._strip_unit(lines[13][18:]))
        record.maximum_acceleration = abs(float(lines[14][18:]))
        record.raw_data_unit = ParserNIED._normalise_unit(lines[14])

        record.raw_data = [int(value) for line in lines[17:] for value in line.split()]

        return record

    @staticmethod
    def _parse_unit(line: str) -> str:
        matches = re.findall(r"\(([^)]+)\)", line)
        if len(matches) == 0:
            raise ValueError(f"No unit found in line: {line}.")
        if len(matches) > 1:
            raise ValueError(f"Multiple units found in line: {line}.")

        return matches[0]

    @staticmethod
    def _normalise_unit(line: str) -> str:
        unit = ParserNIED._parse_unit(line)
        if unit == "gal":
            unit = unit.capitalize()
        return str(pint.Unit(unit))

    @staticmethod
    def _strip_unit(line: str) -> float:
        try:
            unit = ParserNIED._parse_unit(line)
            numerator, denominator = line.replace(f"({unit})", "").split("/")
        except ValueError:
            numerator, denominator = line.split("/")

        return float(numerator) / float(denominator)

    @staticmethod
    def _parse_direction(line: str) -> str:
        return line.replace("-", "").upper()

    @staticmethod
    def _parse_value(line: str) -> str:
        matches = re.findall(r"([0-9.]+)", line)
        if len(matches) == 0:
            raise ValueError(f"No value found in line: {line}.")
        if len(matches) > 1:
            raise ValueError(f"Multiple values found in line: {line}.")
        return matches[0]


class ParserNZSM:
    @staticmethod
    def validate_file(file_path: str):
        lower_path = file_path.lower()
        if lower_path.endswith((".v2a", ".v1a")):
            return

        raise ValueError("NZSM archive file should be a V2A/V1A file.")

    @staticmethod
    async def parse_archive(file_path: str | IO[bytes], user_id: UUID, file_name: str | None = None) -> list[str]:
        if isinstance(file_path, str):
            async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                lines = await f.readlines()
        else:
            if file_name is None:
                raise ValueError("File name is required when a stream is provided.")
            lines = [line.decode("utf-8") for line in file_path.readlines()]

        while True:
            if lines[-1].strip() != "":
                break
            lines.pop()

        num_lines = len(lines) // 3

        assert 3 * num_lines == len(lines), "Number of lines should be a multiple of 3."

        record_names: list[str] = []
        pattern = re.compile(r"(\d{8})_(\d{6})_([A-Za-z0-9]{3,4})_?")
        if matches := pattern.search(lines[0]):
            event_time: datetime = datetime.strptime(matches[1] + matches[2], "%Y%m%d%H%M%S")
            station_code: str = matches[3]
        else:
            event_time: datetime = datetime.strptime(
                "".join(x for x in lines[7].strip().split(" ") if x), "%Y%B%d%H%Mut"
            )
            station_code = [x for x in lines[1].split(" ") if x][1]

        async def _populate_common_fields(record: NZSM):
            record.event_time = event_time
            record.station_code = station_code
            record.uploaded_by = user_id
            record.file_name = os.path.basename(file_name if file_name else file_path).upper()
            record.category = "processed" if record.file_name.endswith(".V2A") else "unprocessed"
            await record.save()
            record_names.append(record.file_name)

        await _populate_common_fields(ParserNZSM.parse_file(lines[:num_lines]))
        await _populate_common_fields(ParserNZSM.parse_file(lines[num_lines : 2 * num_lines]))
        await _populate_common_fields(ParserNZSM.parse_file(lines[2 * num_lines :]))

        return record_names

    @staticmethod
    def parse_file(lines: list[str]) -> NZSM:
        record = NZSM()

        int_header, float_header = ParserNZSM._parse_header(lines)

        record.event_location = [float_header[13], -float_header[12]]
        record.depth = int_header[16]
        record.magnitude = float_header[14] if float_header[14] > 0 else float_header[16]
        record.station_location = [float_header[11], -float_header[10]]
        record.sampling_frequency = 1 / ParserNZSM._parse_interval(lines[10])
        record.duration = float_header[23]
        record.direction = lines[12].split()[1].upper()
        record.maximum_acceleration = abs(pint.Quantity(float_header[35], "mm/s/s").to("Gal").magnitude)

        offset: int = 26
        a_samples = int_header[33]
        a_lines = ceil(a_samples / 10)
        record.raw_data = [
            int(record.FTI * float(v)) for line in lines[offset : offset + a_lines] for v in ParserNZSM._split(line)
        ]

        return record

    @staticmethod
    def _parse_interval(line: str):
        pattern = re.compile(r"\s(\d+\.\d+)\s")
        matches = pattern.search(line)
        if matches:
            return float(matches[1])

        raise ValueError("Sampling frequency/interval not found.")

    @staticmethod
    def _split(line: str, size: int = 8) -> list[str]:
        line = line.replace("\n", "")
        for i in range(0, len(line), size):
            yield line[i : i + size]

    @staticmethod
    def _parse_header(lines: list[str]) -> tuple[list, list]:
        int_header = [int(v) for line in lines[16:20] for v in ParserNZSM._split(line)]
        float_header = [float(v) for line in lines[20:26] for v in ParserNZSM._split(line)]
        return int_header, float_header
