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

import os.path
from io import BytesIO
from typing import BinaryIO

import structlog
from fastapi import UploadFile
from requests import delete, get

from mb.utility.env import MB_FS_ROOT, MB_MAIN_SITE

_logger = structlog.get_logger(__name__)


def _local_path(file_name: str, user_id: str, check_existence: bool = True):
    if not os.path.exists(MB_FS_ROOT):
        os.makedirs(MB_FS_ROOT)

    if not os.path.exists(folder := os.path.join(MB_FS_ROOT, user_id)):
        os.makedirs(folder)

    fs_path: str = os.path.join(user_id, file_name)

    if not os.path.exists(path := os.path.abspath(os.path.join(folder, file_name))) or not check_existence:
        return path, fs_path

    raise FileExistsError(f"File {path} already exists.")


def _iter(file: BinaryIO):
    while chunk := file.read(16 * 2**20):
        yield chunk


def store(upload: UploadFile, user_id: str) -> str:
    local_path, fs_path = _local_path(upload.filename, user_id)
    with open(local_path, "wb") as file:
        for chunk in _iter(upload.file):
            file.write(chunk)

    return f"{MB_MAIN_SITE}/access/{fs_path}"


class FileProxy:
    def __init__(self, file_uri: str, auth_token: str):
        self._file_uri = file_uri
        self._auth_token = auth_token

        self.file = None

    @property
    def is_remote(self):
        return not self._file_uri.startswith(MB_MAIN_SITE)

    @property
    def fs_path(self):
        return self._file_uri.split("access/")[1]

    @property
    def file_name(self):
        return os.path.basename(self.fs_path)

    def __enter__(self):
        if self.is_remote:
            response = get(self._file_uri)
            if response.status_code != 200:
                _logger.error(f"Failed to download file: {self._file_uri}")
                self.file = BytesIO()
            else:
                self.file = BytesIO(response.content)
        else:
            self.file = os.path.abspath(os.path.join(MB_FS_ROOT, self.fs_path))

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.is_remote:
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
