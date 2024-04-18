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

import os
import tarfile
from io import BytesIO
from pathlib import Path
from typing import BinaryIO

import structlog
from fastapi import UploadFile
from requests import delete, get, post

from mb.record.utility import str_factory, uuid5_str
from mb.utility.elastic import sync_elastic
from mb.utility.env import MB_FS_ROOT, MB_MAIN_SITE

_logger = structlog.get_logger(__name__)


def _local_path(file_name: str):
    fs_root: Path = Path(MB_FS_ROOT)
    if not fs_root.exists():
        os.makedirs(fs_root)

    folder: Path = fs_root / str_factory()
    if not folder.exists():
        os.makedirs(folder)

    path: Path = folder / file_name
    if not path.exists():
        return path, path.relative_to(fs_root)

    raise FileExistsError(f"File {path} already exists.")


def _iter(file: BinaryIO):
    while chunk := file.read(16 * 2**20):
        yield chunk


def store(upload: UploadFile) -> str:
    local_path, fs_path = _local_path(upload.filename)
    with open(local_path, "wb") as file:
        for chunk in _iter(upload.file):
            file.write(chunk)

    return f"{MB_MAIN_SITE}/access/{fs_path}"


def pack(uploads: list[UploadFile]):
    local_path, fs_path = _local_path(f'{uuid5_str("".join(upload.filename for upload in uploads))}.tar.gz')

    with tarfile.open(local_path, "w:gz") as archive:
        for upload in uploads:
            tar_info = tarfile.TarInfo(upload.filename.upper().rstrip(".BIN"))
            tar_info.size = upload.size
            archive.addfile(tar_info, upload.file)

    return f"{MB_MAIN_SITE}/access/{fs_path}"


class FileProxy:
    def __init__(self, file_uri: str, auth_token: str | None, *, always_delete_on_exit: bool = False):
        self._file_uri = file_uri
        self._auth_token = auth_token
        self._always_delete_on_exit = always_delete_on_exit

        self.file = None

    @property
    def is_remote(self):
        return not self._file_uri.startswith(MB_MAIN_SITE)

    @property
    def host_path(self):
        return self._file_uri.split("access/")[0]

    @property
    def fs_path(self):
        return self._file_uri.split("access/")[1]

    @property
    def file_name(self):
        return os.path.basename(self.fs_path)

    def bulk(self, records: list):
        def to_dict(record) -> dict:
            dict_data = record.to_mongo()
            for key in ("scale_factor", "raw_data", "raw_data_unit", "offset", "_id", "_cls"):
                dict_data.pop(key, None)
            dict_data["id"] = record.id
            return dict_data

        bulk_body: list = []
        for r in records:
            bulk_body.append({"index": {"_id": r.id}})
            bulk_body.append(to_dict(r))

        if bulk_body:
            if not self.is_remote:
                response = sync_elastic().bulk(index="record", body=bulk_body)
                if response["errors"]:
                    _logger.error(f"Failed to index file: {self._file_uri}")
            else:
                response = post(
                    f"{self.host_path}/index", headers={"Authorization": f"Bearer {self._auth_token}"}, json=bulk_body
                )
                if response.status_code != 200:
                    _logger.error(f"Failed to index file: {self._file_uri}")

        return [record.file_name for record in records]

    def __enter__(self):
        if self.is_remote:
            response = get(self._file_uri)
            if response.status_code != 200:
                raise ConnectionError(f"Failed to download file: {self._file_uri}")

            self.file = BytesIO(response.content)
        else:
            self.file = os.path.abspath(os.path.join(MB_FS_ROOT, self.fs_path))

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # do not try to delete files if there is an exception
        # the task will be retried
        if not exc_type or self._always_delete_on_exit:
            if self.is_remote and self._auth_token:
                response = delete(self._file_uri, headers={"Authorization": f"Bearer {self._auth_token}"})
                if response.status_code != 200:
                    _logger.error(f"Failed to delete file: {self._file_uri}")
            else:
                if os.path.exists(self.file):
                    os.remove(self.file)
                if not os.listdir(folder := os.path.dirname(self.file)):
                    os.rmdir(folder)


if __name__ == "__main__":
    pass
