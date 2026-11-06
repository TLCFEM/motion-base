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

import pint
import pytest

from mb.record.base_parser import BaseParserNIED, BaseParserNZSM
from mb.record.parser import ParserNZSM, _wrap_longitude


@pytest.mark.parametrize(
    "file_name,expected",
    [
        ("archive.tar.gz", True),
        ("ARCHIVE.TAR.GZ", True),
        ("archive.zip", False),
    ],
)
def test_nied_validate_archive(file_name, expected):
    assert BaseParserNIED.validate_archive(file_name) is expected


def test_nied_parse_unit():
    assert BaseParserNIED._parse_unit("value (gal)") == "gal"

    with pytest.raises(ValueError, match="No unit"):
        BaseParserNIED._parse_unit("value")

    with pytest.raises(ValueError, match="Multiple units"):
        BaseParserNIED._parse_unit("value (gal) (cm/s/s)")


def test_nied_normalise_unit():
    assert BaseParserNIED._normalise_unit("value (gal)") == str(pint.Unit("Gal"))
    assert BaseParserNIED._normalise_unit("value (cm/s/s)") == str(pint.Unit("cm/s/s"))


def test_nied_strip_unit():
    assert BaseParserNIED._strip_unit("1.0(gal)/100") == pytest.approx(0.01)
    assert BaseParserNIED._strip_unit("1.0/100") == pytest.approx(0.01)


def test_nied_parse_direction():
    assert BaseParserNIED._parse_direction("n-s") == "NS"


def test_nied_parse_value():
    assert BaseParserNIED._parse_value("100.0 (Hz)") == "100.0"

    with pytest.raises(ValueError, match="No value"):
        BaseParserNIED._parse_value("no numbers")

    with pytest.raises(ValueError, match="Multiple values"):
        BaseParserNIED._parse_value("1.0 2.0")


@pytest.mark.parametrize(
    "file_name,expected",
    [
        ("record.V1A", True),
        ("record.v2a", True),
        ("record.V2A.BIN", True),
        ("record.txt", False),
    ],
)
def test_nz_validate_file(file_name, expected):
    assert BaseParserNZSM.validate_file(file_name) is expected


def test_nz_parse_interval():
    assert BaseParserNZSM._parse_interval("sampling 0.01 ") == pytest.approx(0.01)

    with pytest.raises(ValueError, match="Sampling frequency"):
        BaseParserNZSM._parse_interval("no interval")


def test_nz_split():
    assert list(BaseParserNZSM._split("abcdefghij", 4)) == ["abcd", "efgh", "ij"]
    assert list(BaseParserNZSM._split("abcd\r\n", 4)) == ["abcd"]


def test_nz_parse_header(pwd):
    with open(pwd + "/data/D00129A02.V1A", encoding="utf-8") as file:
        lines = file.readlines()

    int_header, float_header = BaseParserNZSM._parse_header(lines)

    assert len(int_header) == 40
    assert len(float_header) == 60


@pytest.mark.parametrize(
    "longitude,expected",
    [
        (179.0, 179.0),
        (181.0, -179.0),
        (-181.0, 179.0),
        (541.0, -179.0),
    ],
)
def test_wrap_longitude(longitude, expected):
    assert _wrap_longitude(longitude) == pytest.approx(expected)


def test_nz_flags():
    assert ParserNZSM._flags("archive.zip") == (True, False, True)
    assert ParserNZSM._flags("archive.tar.gz") == (False, True, True)
    assert ParserNZSM._flags("record.v1a") == (False, False, False)
