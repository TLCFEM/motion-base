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
from typing import BinaryIO

from fastapi import UploadFile
from requests import delete

from mb.utility.env import MB_FS_ROOT


def _local_path(file_name: str, user_id: str, check_existence: bool = True):
    if not os.path.exists(folder := os.path.join(MB_FS_ROOT, user_id)):
        os.makedirs(folder)

    if not os.path.exists(path := os.path.abspath(os.path.join(folder, file_name))) or not check_existence:
        return path

    raise FileExistsError(f"File {path} already exists.")


def _iter(file: BinaryIO):
    while chunk := file.read(16 * 2**20):
        yield chunk


def store(upload: UploadFile, user_id: str):
    local_file_path: str = _local_path(upload.filename, user_id)
    with open(local_file_path, "wb") as file:
        for chunk in _iter(upload.file):
            file.write(chunk)

    return local_file_path


class FileProxy:
    def __init__(self, file_path: str, auth_token: str):
        self.file_path = file_path
        self.auth_token = auth_token

        self.file = None
        self.file_name = None

    @property
    def is_remote(self):
        # noinspection HttpUrlsUsage
        return self.file_path.startswith(("http://", "https://"))

    def __enter__(self):
        if self.is_remote:
            self.file = self.file_path
            self.file_name = os.path.basename(self.file_path.split("access/")[1])
        else:
            self.file = self.file_path
            self.file_name = os.path.basename(self.file_path)

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.is_remote:
            delete(self.file_path, headers={"Authorization": f"Bearer {self.auth_token}"})
        else:
            if os.path.exists(self.file_path):
                os.remove(self.file_path)
            if not os.listdir(folder := os.path.dirname(self.file_path)):
                os.rmdir(folder)


if __name__ == "__main__":
    pass
