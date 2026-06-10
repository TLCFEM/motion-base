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

import os
import tarfile
from os.path import basename
from shutil import copyfileobj
from tempfile import TemporaryDirectory
from urllib.parse import quote

import structlog
from fastapi import UploadFile

from mb.record.utility import str_factory, uuid5_str
from mb.utility import UPath
from mb.utility.elastic import async_elastic
from mb.utility.env import (
    MB_FS_BUCKET,
    MB_FS_HOST,
    MB_FS_PASSWORD,
    MB_FS_PERSISTENT,
    MB_FS_PORT,
    MB_FS_USERNAME,
)

_logger = structlog.get_logger(__name__)


def _remote_path(uri: str):
    # noinspection HttpUrlsUsage
    return UPath(
        uri,
        key=MB_FS_USERNAME,
        secret=MB_FS_PASSWORD,
        endpoint_url=f"http://{MB_FS_HOST}:{MB_FS_PORT}",
    )


def _remote_bucket():
    bucket: UPath = _remote_path(f"s3://{MB_FS_BUCKET}")
    bucket.mkdir(0o777, True, True)
    return bucket


def _remote_obj(file_name: str):
    remote_obj: UPath = _remote_bucket() / str_factory() / quote(basename(file_name))
    if not remote_obj.exists():
        return remote_obj.absolute()

    raise FileExistsError(f"File {remote_obj} already exists.")


def store(upload: UploadFile) -> str:
    remote_obj = _remote_obj(upload.filename)
    with remote_obj.open("wb") as remote_file:
        copyfileobj(upload.file, remote_file, 16 * 2**20)

    return remote_obj.as_uri()


def pack(uploads: list[UploadFile]):
    tmp_file: str = f"{uuid5_str(''.join(v.filename for v in uploads))}.tar.gz"
    remote_obj = _remote_obj(tmp_file)

    with TemporaryDirectory() as tmp_dir:
        with tarfile.open(tmp_path := UPath(tmp_dir) / tmp_file, "w:gz") as archive:
            for upload in uploads:
                tar_info = tarfile.TarInfo(upload.filename.upper().rstrip(".BIN"))
                tar_info.size = upload.size
                archive.addfile(tar_info, upload.file)

        remote_obj.fs.put_file(tmp_path, remote_obj.path)

    return remote_obj.as_uri()


def serialize_records(records: list):
    bulk_body: list = []
    for r in records:
        bulk_body.append({"index": {"_id": r.id}})
        bulk_body.append(
            r.model_dump(
                # mode="json",
                exclude={"scale_factor", "raw_data", "raw_data_unit", "offset"},
                exclude_none=True,
                exclude_unset=True,
            )
        )

    return bulk_body


class FileProxy:
    def __init__(self, file_uri: str, *, always_delete_on_exit: bool):
        self.file = _remote_path(file_uri)
        self._always_delete_on_exit = always_delete_on_exit

    @property
    def file_name(self):
        return os.path.basename(self.file.path)

    async def bulk(self, records: list):
        if bulk_body := serialize_records(records):
            async with async_elastic() as client:
                response = await client.bulk(index="record", body=bulk_body)
            if response["errors"]:
                _logger.error(f"Failed to index file: {self.file}")

        return [record.file_name for record in records]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # do not try to delete files if there is an exception
        # the task will be retried
        if not MB_FS_PERSISTENT and (not exc_type or self._always_delete_on_exit):
            self.file.unlink()


if __name__ == "__main__":
    pass
