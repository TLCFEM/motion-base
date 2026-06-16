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


import pytest

from mb.record.parser import ParserNIED
from mb.record.utility import str_factory
from mb.utility import UPath


@pytest.mark.parametrize("file_path", ["data/SZO0039901271027.NS"])
async def test_jp_parse_file(pwd, file_path, mongo_connection):
    result = await ParserNIED.parse_file((UPath(pwd) / file_path).as_posix())
    assert result.model_dump(
        mode="json",
        exclude_none=True,
        exclude_defaults=True,
        exclude={"raw_data", "id", "uploaded_by"},
    ) == {
        "file_hash": "f738850f18d5d1494c0059b8c784b0b9bce347db3e217be23379ad7c4db4f8d1",
        "region": "jp",
        "magnitude": 3.6,
        "maximum_acceleration": 25.836,
        "event_time": "1999-01-27T10:27:00+09:00",
        "event_location": [139.647, 34.82],
        "depth": 38.0,
        "station_code": "SZO003",
        "station_location": [139.0544, 34.8158],
        "station_elevation": 149.0,
        "station_elevation_unit": "meter",
        "record_time": "1999-01-27T10:27:55+09:00",
        "last_update_time": "1999-01-27T10:00:00+09:00",
        "sampling_frequency": 100.0,
        "sampling_frequency_unit": "hertz",
        "duration": 119.0,
        "direction": "NS",
        "scale_factor": 0.0002384185791015625,
        "raw_data_unit": "galileo",
    }


@pytest.mark.parametrize(
    "file_path", ["data/jp_test.knt.tar.gz", "data/jp_recursive.tar.gz"]
)
async def test_jp_parse_archive(pwd, file_path, mongo_connection):
    results = await ParserNIED.parse_archive(
        archive_obj=UPath(pwd) / file_path, user_id=str_factory()
    )
    assert len(results) == 6
