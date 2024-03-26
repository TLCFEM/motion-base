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

import os
from uuid import uuid4

import pytest

from mb.record.async_parser import ParserNIED


@pytest.mark.parametrize("file_path", ["data/SZO0039901271027.NS"])
async def test_jp_parse_file(pwd, file_path):
    await ParserNIED.parse_file(os.path.join(pwd, file_path))


@pytest.mark.parametrize("file_path", ["data/jp_test.knt.tar.gz"])
async def test_jp_parse_archive(pwd, file_path):
    await ParserNIED.parse_archive(archive_obj=os.path.join(pwd, file_path), user_id=uuid4())
