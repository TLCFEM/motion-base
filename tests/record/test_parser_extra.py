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

import tarfile
import zipfile
from io import BytesIO

import pytest

from mb.record.async_record import NIED, NZSM, UploadTask, create_task
from mb.record.parser import ParserNIED, ParserNZSM
from mb.record.utility import str_factory
from mb.utility import UPath


def _tar_bytes(files: dict[str, bytes]) -> BytesIO:
    buffer = BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
        for name, content in files.items():
            info = tarfile.TarInfo(name)
            info.size = len(content)
            archive.addfile(info, BytesIO(content))
    return BytesIO(buffer.getvalue())


def _zip_bytes(files: dict[str, bytes]) -> BytesIO:
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    return BytesIO(buffer.getvalue())


def _read(path: str) -> bytes:
    with open(path, "rb") as file:
        return file.read()


async def test_nied_parse_archive_with_invalid_file(pwd, mongo_connection):
    buffer = _tar_bytes(
        {
            "bad.NS": b"not a valid NIED file",
            "SZO0039901271027.NS": _read(f"{pwd}/data/SZO0039901271027.NS"),
        }
    )

    records = await ParserNIED.parse_archive(
        archive_obj=buffer,
        user_id=str_factory(),
        archive_name="kik_test.tar.gz",
    )

    assert len(records) == 1
    assert records[0].file_name == "SZO0039901271027.NS"
    assert records[0].region == "jp"

    # Parsing the same file again exercises the overwrite branch.
    records = await ParserNIED.parse_archive(
        archive_obj=_tar_bytes(
            {"SZO0039901271027.NS": _read(f"{pwd}/data/SZO0039901271027.NS")}
        ),
        user_id=str_factory(),
        archive_name="knt_test.tar.gz",
    )

    assert len(records) == 1
    assert await NIED.find_all().count() == 1


async def test_nied_parse_archive_errors(pwd, mongo_connection):
    assert (
        await ParserNIED._parse_archive(
            BytesIO(b"not a tarball"), None, "knt", str_factory(), True
        )
        == []
    )

    assert (
        await ParserNIED._parse_archive(
            BytesIO(b""),
            None,
            "knt",
            str_factory(),
            True,
            current_depth=ParserNIED.MAX_DEPTH,
        )
        == []
    )

    with pytest.raises(ValueError, match="Need archive name"):
        await ParserNIED.parse_archive(archive_obj=BytesIO(b""), user_id=str_factory())


async def test_nied_parse_archive_with_task(pwd, mongo_connection):
    task_id = await create_task()

    records = await ParserNIED.parse_archive(
        archive_obj=UPath(pwd) / "data/jp_test.knt.tar.gz",
        user_id=str_factory(),
        task_id=task_id,
    )

    assert len(records) == 6
    assert await UploadTask.find_one(UploadTask.id == task_id) is None


async def test_nz_parse_archive_errors(mongo_connection):
    assert (
        await ParserNZSM._parse_archive(
            "tar", BytesIO(b"not a tarball"), None, str_factory(), True
        )
        == []
    )
    assert (
        await ParserNZSM._parse_archive(
            "zip", BytesIO(b"not a zip file"), None, str_factory(), True
        )
        == []
    )
    assert (
        await ParserNZSM._parse_archive(
            "tar",
            BytesIO(b""),
            None,
            str_factory(),
            True,
            current_depth=ParserNZSM.MAX_DEPTH,
        )
        == []
    )

    with pytest.raises(ValueError, match="Need archive name"):
        await ParserNZSM.parse_archive(archive_obj=BytesIO(b""), user_id=str_factory())

    with pytest.raises(ValueError, match="File name is required"):
        await ParserNZSM.parse_file(BytesIO(b""), str_factory())


@pytest.mark.parametrize("archive_type", ["tar", "zip"])
async def test_nz_parse_archive_with_invalid_files(pwd, mongo_connection, archive_type):
    files = {
        "readme.txt": b"ignore me",
        "bad.V1A": b"not a valid NZSM file",
        "D9644D08.V2A": _read(f"{pwd}/data/D9644D08.V2A"),
    }

    if archive_type == "tar":
        archive_obj = _tar_bytes(files)
        archive_name = "test.tar.gz"
    else:
        archive_obj = _zip_bytes(files)
        archive_name = "test.zip"

    records = await ParserNZSM.parse_archive(
        archive_obj=archive_obj,
        user_id=str_factory(),
        archive_name=archive_name,
    )

    assert len(records) == 3
    assert await NZSM.find_all().count() == 3


async def test_nz_parse_file_with_trailing_blank_lines(pwd, mongo_connection):
    content = _read(f"{pwd}/data/D00129A02.V1A") + b"\n\n"

    records = await ParserNZSM.parse_file(
        BytesIO(content), str_factory(), "D00129A02.V1A"
    )

    assert len(records) == 3


async def test_nz_parse_file_twice(pwd, mongo_connection):
    user_id = str_factory()
    path = f"{pwd}/data/D9644D08.V2A"

    first = await ParserNZSM.parse_file(path, user_id)
    second = await ParserNZSM.parse_file(path, user_id)

    assert len(second) == len(first) == 3
    assert await NZSM.find_all().count() == 3


async def test_nz_parse_archive_with_task(pwd, mongo_connection):
    task_id = await create_task()

    records = await ParserNZSM.parse_archive(
        archive_obj=UPath(pwd) / "data/nz_test.tar.gz",
        user_id=str_factory(),
        task_id=task_id,
    )

    assert len(records) == 6
    assert await UploadTask.find_one(UploadTask.id == task_id) is None
