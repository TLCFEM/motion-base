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

import os.path

import numpy as np
import pytest

from mb.record.parser import ParserNZSM
from mb.record.response_spectrum import response_spectrum
from mb.record.utility import str_factory


@pytest.mark.parametrize(
    "file_path",
    [
        "data/20110222_015029_MQZ.V2A",
        "data/20190904_070311_WAKS_20.V1A",
        "data/I06465B10.V2A",
        "data/D9644D08.V2A",
        "data/D5054A01.V2A",
    ],
)
def test_nz_parse_file(pwd, file_path):
    ParserNZSM.parse_file(os.path.join(pwd, file_path), str_factory())


@pytest.mark.parametrize("file_path", ["data/nz_test.tar.gz"])
def test_nz_parse_archive(pwd, file_path):
    ParserNZSM.parse_archive(
        archive_obj=os.path.join(pwd, file_path), user_id=str_factory()
    )


def test_nz_response_spectrum():
    motion = np.array([0, 1, 1, 0, 2, 0, 0], dtype=float)
    interval = 0.01
    period = np.arange(0.1, 0.2, interval)
    response_spectrum(0.05, interval, motion, period)
