#  Copyright (C) 2022-2025 Theodore Chang
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
from datetime import datetime
from math import ceil
from typing import IO, BinaryIO
from zoneinfo import ZoneInfo  # noqa

import pint
import structlog
import tzdata  # noqa # pylint: disable=unused-import

from .base_parser import BaseParserNIED, BaseParserNZSM
from .sync_record import NIED, NZSM, UploadTask

_logger = structlog.get_logger(__name__)


def _wrap_longitude(_longitude: float) -> float:
    while _longitude > 180.0:
        _longitude -= 360.0
    while _longitude < -180.0:
        _longitude += 360.0
    return _longitude


class ParserNIED(BaseParserNIED):
    @staticmethod
    def parse_archive(
        *,
        archive_obj: str | BinaryIO,
        user_id: str,
        archive_name: str | None = None,
        task_id: str | None = None,
        overwrite_existing: bool = True,
    ) -> list[NIED]:
        if not isinstance(archive_obj, str) and archive_name is None:
            raise ValueError("Need archive name if archive is provided as a BinaryIO.")

        name_string: str = archive_obj if isinstance(archive_obj, str) else archive_name
        category: str = "knt" if "knt" in name_string else "kik"

        kwargs: dict = {"mode": "r:gz"}
        if isinstance(archive_obj, str):
            kwargs["name"] = archive_obj
        else:
            kwargs["fileobj"] = archive_obj

        task: UploadTask | None = None
        if task_id is not None:
            task = UploadTask.objects(id=task_id).first()
            task.pid = os.getpid()
            if isinstance(archive_obj, str):
                task.archive_path = archive_obj

        records = []
        try:
            with tarfile.open(**kwargs) as archive:
                if task:
                    task.total_size = len(archive.getnames())
                for f in archive:
                    if task:
                        task.current_size += 1
                        task.save()
                    if (
                        not f.isfile()
                        or not f.name.endswith(
                            ("EW1", "EW2", "NS1", "NS2", "UD1", "UD2", "EW", "NS", "UD")
                        )
                        or not (target := archive.extractfile(f))
                    ):
                        continue
                    try:
                        record = ParserNIED.parse_file(target, overwrite_existing)
                        record.uploaded_by = user_id
                        record.file_name = os.path.basename(f.name)
                        record.category = category
                        record.save()
                        records.append(record)
                    except Exception as e:
                        _logger.critical(
                            "Failed to parse.", file_name=f.name, exc_info=e
                        )
        except tarfile.ReadError as e:
            _logger.critical("Failed to open the archive.", exc_info=e)

        if task:
            task.delete()

        return records

    @staticmethod
    def parse_file(file_path: str | IO[bytes], overwrite_existing: bool = True) -> NIED:
        if isinstance(file_path, str):
            with open(file_path, encoding="utf-8") as f:
                lines = f.readlines()

            lines = [line.strip() for line in lines]
        else:
            lines = [line.decode("utf-8").strip() for line in file_path.readlines()]

        file_hash = hashlib.sha256("".join(lines).encode("utf-8")).hexdigest()
        if overwrite_existing and (record := NIED.objects(file_hash=file_hash).first()):
            record.delete()

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
    @staticmethod
    def parse_archive(
        *,
        archive_obj: str | BinaryIO,
        user_id: str,
        archive_name: str | None = None,
        task_id: str | None = None,
        overwrite_existing: bool = True,
    ) -> list[NZSM]:
        if not isinstance(archive_obj, str) and archive_name is None:
            raise ValueError("Need archive name if archive is provided as a BinaryIO.")

        name_string: str = archive_obj if isinstance(archive_obj, str) else archive_name

        kwargs: dict = {}
        if name_string.endswith(".tar.gz"):
            kwargs["mode"] = "r:gz"
            if isinstance(archive_obj, str):
                kwargs["name"] = archive_obj
            else:
                kwargs["fileobj"] = archive_obj
        elif name_string.endswith(".zip"):
            kwargs["mode"] = "r"
            kwargs["file"] = archive_obj

        task: UploadTask | None = None
        if task_id is not None:
            task = UploadTask.objects(id=task_id).first()
            if isinstance(archive_obj, str):
                task.archive_path = archive_obj
            task.pid = os.getpid()

        records: list = []

        if name_string.endswith(".tar.gz"):
            try:
                with tarfile.open(**kwargs) as archive:
                    if task:
                        task.total_size = len(archive.getnames())
                    for f in archive:
                        if task:
                            task.current_size += 1
                            task.save()
                        if not f.name.upper().endswith((".V2A", ".V1A")):
                            continue
                        if target := archive.extractfile(f):
                            try:
                                records.extend(
                                    ParserNZSM.parse_file(
                                        target,
                                        user_id,
                                        os.path.basename(f.name),
                                        overwrite_existing,
                                    )
                                )
                            except Exception as e:
                                _logger.critical(
                                    "Failed to parse.", file_name=f.name, exc_info=e
                                )
            except tarfile.ReadError as e:
                _logger.critical("Failed to open the archive.", exc_info=e)
        elif name_string.endswith(".zip"):
            try:
                with zipfile.ZipFile(**kwargs) as archive:
                    if task:
                        task.total_size = len(archive.namelist())
                    for f in archive.namelist():
                        if task:
                            task.current_size += 1
                            task.save()
                        if not f.upper().endswith((".V2A", ".V1A")):
                            continue
                        with archive.open(f) as target:
                            try:
                                records.extend(
                                    ParserNZSM.parse_file(
                                        target,
                                        user_id,
                                        os.path.basename(f),
                                        overwrite_existing,
                                    )
                                )
                            except Exception as e:
                                _logger.critical(
                                    "Failed to parse.", file_name=f, exc_info=e
                                )
            except zipfile.BadZipFile as e:
                _logger.critical("Failed to open the archive.", exc_info=e)

        if task:
            task.delete()

        return records

    @staticmethod
    def parse_file(
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

        def _populate_common_fields(record: NZSM):
            record.station_code = station_code
            record.uploaded_by = user_id
            record.file_name = os.path.basename(
                file_name if file_name else file_path
            ).upper()
            record.category = (
                "processed" if ".V2A" in record.file_name else "unprocessed"
            )
            if last_update_time is not None:
                record.last_update_time = last_update_time
            record.save()
            records.append(record)

        int_header = ParserNZSM._parse_header(lines)[0]
        a_lines = (int_header[33] + 9) // 10
        v_lines = (int_header[34] + 9) // 10
        d_lines = (int_header[35] + 9) // 10

        if (target_lines := a_lines + v_lines + d_lines + 26) == len(lines):
            _populate_common_fields(ParserNZSM.parse_lines(lines, overwrite_existing))
        else:
            assert 3 * target_lines == len(lines), (
                "Number of lines should be a multiple of 3."
            )

            _populate_common_fields(
                ParserNZSM.parse_lines(lines[:target_lines], overwrite_existing)
            )
            _populate_common_fields(
                ParserNZSM.parse_lines(
                    lines[target_lines : 2 * target_lines], overwrite_existing
                )
            )
            _populate_common_fields(
                ParserNZSM.parse_lines(lines[2 * target_lines :], overwrite_existing)
            )

        return records

    @staticmethod
    def parse_lines(lines: list[str], overwrite_existing: bool = True) -> NZSM:
        """
        Parse file according to the format shown in the following link.

        https://www.geonet.org.nz/data/supplementary/strong_motion_file_formats
        """
        file_hash = hashlib.sha256("".join(lines).encode("utf-8")).hexdigest()
        if overwrite_existing and (record := NZSM.objects(file_hash=file_hash).first()):
            record.delete()

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
        record.direction = lines[12].split()[1].upper()
        record.maximum_acceleration = abs(
            pint.Quantity(float_header[35], "mm/s/s").to("Gal").magnitude
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
