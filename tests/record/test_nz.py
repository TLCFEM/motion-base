#  Copyright (C) 2022-2023 Theodore Chang
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
import asyncio
import os.path
import tarfile
from uuid import uuid4

import numpy as np
import pytest

from mb.record.parser import ParserNZSM
from mb.record.response_spectrum import response_spectrum


@pytest.mark.parametrize('file_path', ['data/20110222_015029_MQZ.V2A'])
async def test_nz_parse_archive(pwd, file_path):
    await ParserNZSM.parse_archive(os.path.join(pwd, file_path), uuid4())


@pytest.mark.parametrize('file_path', ['data/nz_test.tar.gz'])
async def test_nz_parse_archive(pwd, file_path):
    file = os.path.join(pwd, file_path)
    with tarfile.open(name=file, mode='r:gz') as archive_obj:
        tasks = []
        for f in archive_obj.getnames():
            target = archive_obj.extractfile(f)
            if target:
                tasks.append(ParserNZSM.parse_archive(target, uuid4(), f))
        await asyncio.gather(*tasks)


def test_nz_response_spectrum():
    motion = np.array([0, 1, 1, 0, 2, 0, 0])
    interval = .01
    period = np.arange(.1, .2, interval)
    response_spectrum(.05, interval, motion, period)
