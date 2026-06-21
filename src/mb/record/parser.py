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

from __future__ import annotations

import hashlib
import os
import tarfile
import zipfile
from asyncio import gather
from contextlib import nullcontext
from datetime import datetime
from math import ceil
from typing import IO, BinaryIO, Literal
from zoneinfo import ZoneInfo

import pint
import structlog
import tzdata  # noqa

from ..utility import UPath
from .async_record import NIED, NZSM, UploadTask
from .base_parser import BaseParserNIED, BaseParserNZSM

_logger = structlog.get_logger(__name__)


def _wrap_longitude(_longitude: float) -> float:
    while _longitude > 180.0:
        _longitude -= 360.0
    while _longitude < -180.0:
        _longitude += 360.0
    return _longitude


def _proxy(target: UPath | BinaryIO):
    return target.open("rb") if isinstance(target, UPath) else nullcontext(target)


class ParserNIED(BaseParserNIED):
    MAX_DEPTH: int = 10
    ALLOWED_SUFFIX: tuple = (
        "TAR.GZ",
        "EW1",
        "EW2",
        "NS1",
        "NS2",
        "UD1",
        "UD2",
        "EW",
        "NS",
        "UD",
    )

    @staticmethod
    async def _parse_tar(
        archive: tarfile.TarFile,
        task: UploadTask | None,
        category: str,
        user_id: str,
        overwrite_existing: bool,
        current_depth: int,
    ):
        if task:
            task.total_size += len(archive.getnames())

        records: list[NIED] = []

        for f in archive:
            if task:
                task.current_size += 1
                await task.save()

            if (
                not f.isfile()
                or not f.name.upper().endswith(ParserNIED.ALLOWED_SUFFIX)
                or not (target := archive.extractfile(f))
            ):
                continue

            if f.name.upper().endswith("TAR.GZ"):
                records.extend(
                    await ParserNIED._parse_archive(
                        target,
                        task,
                        category,
                        user_id,
                        overwrite_existing,
                        current_depth + 1,
                    )
                )
                continue

            try:
                record = await ParserNIED.parse_file(target, overwrite_existing)
                record.uploaded_by = user_id
                record.file_name = os.path.basename(f.name)
                record.category = category
                await record.save()
                records.append(record)
            except Exception as e:
                _logger.critical("Failed to parse.", file_name=f.name, exc_info=e)

        return records

    @staticmethod
    async def _parse_archive(
        fo: IO[bytes],
        task: UploadTask | None,
        category: str,
        user_id: str,
        overwrite_existing: bool,
        current_depth: int = 0,
    ):
        records: list[NIED] = []

        if current_depth >= ParserNIED.MAX_DEPTH:
            return records

        try:
            with tarfile.open(None, "r:gz", fo) as archive:
                records = await ParserNIED._parse_tar(
                    archive, task, category, user_id, overwrite_existing, current_depth
                )
        except tarfile.ReadError as e:
            _logger.critical("Failed to open the archive.", exc_info=e)

        return records

    @staticmethod
    async def parse_archive(
        *,
        archive_obj: UPath | BinaryIO,
        user_id: str,
        archive_name: str | None = None,
        task_id: str | None = None,
        overwrite_existing: bool = True,
    ) -> list[NIED]:
        if not isinstance(archive_obj, UPath) and archive_name is None:
            raise ValueError("Need archive name if archive is provided as a BinaryIO.")

        # noinspection PyTypeChecker
        name_string: str = (
            archive_obj.as_posix() if isinstance(archive_obj, UPath) else archive_name
        )
        if "knt" in name_string:
            category = "knt"
        elif "kik" in name_string:
            category = "kik"
        else:
            category = "unknown"

        task: UploadTask | None = None
        if task_id is not None:
            task = await UploadTask.get(task_id)
            task.pid = os.getpid()
            if isinstance(archive_obj, UPath):
                task.archive_path = archive_obj.as_posix()

        with _proxy(archive_obj) as fo:
            records = await ParserNIED._parse_archive(
                fo, task, category, user_id, overwrite_existing
            )

        if task:
            await task.delete()

        return records

    @staticmethod
    async def parse_file(
        file_path: str | IO[bytes], overwrite_existing: bool = True
    ) -> NIED:
        if isinstance(file_path, str):
            with open(file_path, encoding="utf-8") as f:
                lines = f.readlines()

            lines = [line.strip() for line in lines]
        else:
            lines = [line.decode("utf-8").strip() for line in file_path.readlines()]

        file_hash = hashlib.sha256("".join(lines).encode("utf-8")).hexdigest()
        if overwrite_existing and (
            record := await NIED.find_one(NIED.file_hash == file_hash)
        ):
            await record.delete()

        def _parse_date(string: str) -> datetime:
            return datetime.strptime(string, "%Y/%m/%d %H:%M:%S").replace(
                tzinfo=ZoneInfo("Asia/Tokyo")
            )

        record = NIED()
        record.file_hash = file_hash
        record.event_time = _parse_date(lines[0][18:])
        record.event_location = [
            _wrap_longitude(float(lines[2][18:])),
            float(lines[1][18:]),
        ]
        record.depth = (
            pint.Quantity(float(lines[3][18:]), ParserNIED._normalise_unit(lines[3]))
            .to("km")
            .magnitude
        )
        record.magnitude = float(lines[4][18:])
        record.station_code = lines[5][18:]
        record.station_location = [
            _wrap_longitude(float(lines[7][18:])),
            float(lines[6][18:]),
        ]
        record.station_elevation = float(lines[8][18:])
        record.station_elevation_unit = ParserNIED._normalise_unit(lines[8])
        record.record_time = _parse_date(lines[9][18:])
        record.sampling_frequency = float(ParserNIED._parse_value(lines[10][18:]))
        record.sampling_frequency_unit = ParserNIED._normalise_unit(lines[10])
        record.duration = (
            pint.Quantity(float(lines[11][18:]), ParserNIED._normalise_unit(lines[11]))
            .to("s")
            .magnitude
        )
        record.direction = ParserNIED._parse_direction(lines[12][18:])
        record.scale_factor = float(ParserNIED._strip_unit(lines[13][18:]))
        record.maximum_acceleration = abs(float(lines[14][18:]))
        record.raw_data_unit = ParserNIED._normalise_unit(lines[14])
        record.last_update_time = _parse_date(lines[15][18:])

        record.raw_data = [int(value) for line in lines[17:] for value in line.split()]

        return record


class ParserNZSM(BaseParserNZSM):
    MAX_DEPTH: int = 10

    @staticmethod
    def _flags(_fn: str):
        _is_zip = _fn.lower().endswith(".zip")
        _is_tar = _fn.lower().endswith(".tar.gz")
        return _is_zip, _is_tar, _is_zip or _is_tar

    @staticmethod
    async def _parse_zip(
        archive: zipfile.ZipFile,
        task: UploadTask | None,
        user_id: str,
        overwrite_existing: bool,
        current_depth: int,
    ):
        if task:
            task.total_size += len(archive.namelist())

        records: list[NZSM] = []

        for f in archive.namelist():
            if task:
                task.current_size += 1
                await task.save()

            is_zip, is_tar, is_archive = ParserNZSM._flags(f)

            if not ParserNZSM.validate_file(f) and not is_archive:
                continue

            with archive.open(f) as target:
                if is_archive:
                    records.extend(
                        await ParserNZSM._parse_archive(
                            "zip" if is_zip else "tar",
                            target,
                            task,
                            user_id,
                            overwrite_existing,
                            current_depth + 1,
                        )
                    )
                else:
                    try:
                        records.extend(
                            await ParserNZSM.parse_file(
                                target, user_id, os.path.basename(f), overwrite_existing
                            )
                        )
                    except Exception as e:
                        _logger.critical("Failed to parse.", file_name=f, exc_info=e)

        return records

    @staticmethod
    async def _parse_tar(
        archive: tarfile.TarFile,
        task: UploadTask | None,
        user_id: str,
        overwrite_existing: bool,
        current_depth: int,
    ):
        if task:
            task.total_size += len(archive.getnames())

        records: list[NZSM] = []

        for f in archive:
            if task:
                task.current_size += 1
                await task.save()

            is_zip, is_tar, is_archive = ParserNZSM._flags(f.name)

            if (
                not f.isfile()
                or (not ParserNZSM.validate_file(f.name) and not is_archive)
                or not (target := archive.extractfile(f))
            ):
                continue

            if is_archive:
                records.extend(
                    await ParserNZSM._parse_archive(
                        "zip" if is_zip else "tar",
                        target,
                        task,
                        user_id,
                        overwrite_existing,
                        current_depth + 1,
                    )
                )
                continue

            try:
                records.extend(
                    await ParserNZSM.parse_file(
                        target, user_id, os.path.basename(f.name), overwrite_existing
                    )
                )
            except Exception as e:
                _logger.critical("Failed to parse.", file_name=f.name, exc_info=e)

        return records

    @staticmethod
    async def _parse_archive(
        mode: Literal["zip", "tar"],
        fo: IO[bytes],
        task: UploadTask | None,
        user_id: str,
        overwrite_existing: bool,
        current_depth: int = 0,
    ):
        records: list[NZSM] = []

        if current_depth >= ParserNZSM.MAX_DEPTH:
            return records

        if mode == "tar":
            try:
                with tarfile.open(None, "r:gz", fo) as archive:
                    records = await ParserNZSM._parse_tar(
                        archive, task, user_id, overwrite_existing, current_depth
                    )
            except tarfile.ReadError as e:
                _logger.critical("Failed to open the archive.", exc_info=e)
        elif mode == "zip":
            try:
                with zipfile.ZipFile(fo) as archive:
                    records = await ParserNZSM._parse_zip(
                        archive, task, user_id, overwrite_existing, current_depth
                    )
            except zipfile.BadZipFile as e:
                _logger.critical("Failed to open the archive.", exc_info=e)

        return records

    @staticmethod
    async def parse_archive(
        *,
        archive_obj: UPath | BinaryIO,
        user_id: str,
        archive_name: str | None = None,
        task_id: str | None = None,
        overwrite_existing: bool = True,
    ) -> list[NZSM]:
        if not isinstance(archive_obj, UPath) and archive_name is None:
            raise ValueError("Need archive name if archive is provided as a BinaryIO.")

        # noinspection PyTypeChecker
        name_string: str = (
            archive_obj.as_posix() if isinstance(archive_obj, UPath) else archive_name
        )

        task: UploadTask | None = None
        if task_id is not None:
            task = await UploadTask.get(task_id)
            if isinstance(archive_obj, UPath):
                task.archive_path = archive_obj.as_posix()
            task.pid = os.getpid()

        with _proxy(archive_obj) as fo:
            records: list[NZSM] = await ParserNZSM._parse_archive(
                "tar" if name_string.endswith(".tar.gz") else "zip",
                fo,
                task,
                user_id,
                overwrite_existing,
            )

        if task:
            await task.delete()

        return records

    @staticmethod
    async def parse_file(
        file_path: str | IO[bytes],
        user_id: str,
        file_name: str | None = None,
        overwrite_existing: bool = True,
    ) -> list[NZSM]:
        if isinstance(file_path, str):
            with open(file_path, encoding="utf-8") as f:
                lines = f.readlines()
        else:
            if file_name is None:
                raise ValueError("File name is required when a stream is provided.")
            lines = [line.decode("utf-8") for line in file_path.readlines()]

        while True:
            if lines[-1].strip() != "":
                break
            lines.pop()

        records: list[NZSM] = []
        station_code = [x for x in lines[1].split(" ") if x][1]

        last_update_time: datetime | None = None
        if len(last_processed := lines[5].upper().split("PROCESSED")) == 2:
            last_update_time = datetime.strptime(
                last_processed[1].strip(), "%Y %B %d"
            ).replace(tzinfo=ZoneInfo("Pacific/Auckland"))

        async def _populate_common_fields(record: NZSM):
            record.station_code = station_code
            record.uploaded_by = user_id
            # noinspection PyTypeChecker
            record.file_name = os.path.basename(file_name or file_path).upper()
            record.category = (
                "processed" if ".V2A" in record.file_name else "unprocessed"
            )
            if last_update_time is not None:
                record.last_update_time = last_update_time
            await record.save()
            return record

        int_header = ParserNZSM._parse_header(lines)[0]
        a_lines = (int_header[33] + 9) // 10
        v_lines = (int_header[34] + 9) // 10
        d_lines = (int_header[35] + 9) // 10

        if (target_lines := a_lines + v_lines + d_lines + 26) == len(lines):
            tasks = [ParserNZSM.parse_lines(lines, overwrite_existing)]
        else:
            assert 3 * target_lines == len(lines), (
                "Number of lines should be a multiple of 3."
            )

            tasks = [
                ParserNZSM.parse_lines(lines[:target_lines], overwrite_existing),
                ParserNZSM.parse_lines(
                    lines[target_lines : 2 * target_lines], overwrite_existing
                ),
                ParserNZSM.parse_lines(lines[2 * target_lines :], overwrite_existing),
            ]

        records.extend(
            await gather(*[_populate_common_fields(x) for x in await gather(*tasks)])
        )

        return records

    @staticmethod
    async def parse_lines(lines: list[str], overwrite_existing: bool = True) -> NZSM:
        """
        Parse file according to the format shown in the following link.

        https://www.geonet.org.nz/data/supplementary/strong_motion_file_formats
        """
        file_hash = hashlib.sha256("".join(lines).encode("utf-8")).hexdigest()
        if overwrite_existing and (
            record := await NZSM.find_one(NZSM.file_hash == file_hash)
        ):
            await record.delete()

        record = NZSM()

        record.file_hash = file_hash

        int_header, float_header = ParserNZSM._parse_header(lines)

        record.event_time = datetime(
            int_header[0],
            int_header[1],
            int_header[2],
            int_header[3],
            int_header[4],
            int(int_header[5] / 10),
        )
        record.event_location = [_wrap_longitude(float_header[13]), -float_header[12]]
        record.depth = int_header[16]
        record.magnitude = (
            float_header[14] if float_header[14] > 0 else float_header[16]
        )

        date_tuple: tuple = (
            int_header[8],
            int_header[9],
            int_header[18],
            int_header[19],
            int_header[38],
            int(int_header[39] / 1000),
        )
        if date_tuple not in ((1970, 1, 1, 0, 0, -1), (0, 0, 0, 0, 0, 0)):
            record.record_time = datetime(*date_tuple)
        record.station_location = [_wrap_longitude(float_header[11]), -float_header[10]]
        record.sampling_frequency = 1 / ParserNZSM._parse_interval(lines[10])
        record.duration = float_header[23]
        if segment := lines[12].split():
            record.direction = segment[1].upper()
        record.maximum_acceleration = abs(
            pint.Quantity(float_header[35] or float_header[30], "mm/s/s")
            .to("Gal")
            .magnitude
        )

        offset: int = 26
        a_samples = int_header[33]
        a_lines = ceil(a_samples / 10)
        record.raw_data = [
            int(record.FTI * float(v) * float_header[7])
            for line in lines[offset : offset + a_lines]
            for v in ParserNZSM._split(line)
        ]

        return record
