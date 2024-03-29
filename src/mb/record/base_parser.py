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

import re

import pint
import structlog

_logger = structlog.get_logger(__name__)


class BaseParserNIED:
    @staticmethod
    def validate_archive(archive_name: str):
        if not archive_name.endswith(".tar.gz"):
            raise ValueError("NIED archive file should be a .tar.gz file.")

        if "knt" not in archive_name and "kik" not in archive_name:
            raise ValueError("NIED archive file name should contain knt or kik.")

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
        unit = BaseParserNIED._parse_unit(line)
        if unit == "gal":
            unit = unit.capitalize()
        return str(pint.Unit(unit))

    @staticmethod
    def _strip_unit(line: str) -> float:
        try:
            unit = BaseParserNIED._parse_unit(line)
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


class BaseParserNZSM:
    @staticmethod
    def validate_file(file_path: str):
        if file_path.upper().endswith((".V2A", ".V1A", ".V2A.BIN", ".V1A.BIN")):
            return

        raise ValueError("NZSM archive file should be a V2A/V1A file.")

    @staticmethod
    def _parse_interval(line: str):
        pattern = re.compile(r"\s(\d+\.\d+)\s")
        if matches := pattern.search(line):
            return float(matches[1])

        raise ValueError("Sampling frequency/interval not found.")

    @staticmethod
    def _split(line: str, size: int = 8) -> list[str]:
        line = line.replace("\n", "")
        for i in range(0, len(line), size):
            yield line[i : i + size]

    @staticmethod
    def _parse_header(lines: list[str]) -> tuple[list, list]:
        int_header = [int(v) for line in lines[16:20] for v in BaseParserNZSM._split(line)]
        float_header = [float(v) for line in lines[20:26] for v in BaseParserNZSM._split(line)]
        return int_header, float_header
