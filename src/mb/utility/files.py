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
from uuid import uuid5, NAMESPACE_OID

from fastapi import UploadFile

from mb.utility.env import MB_FS_ROOT


def local_path(file_name: str, check_existence: bool = True):
    if not os.path.exists(folder := os.path.join(MB_FS_ROOT, str(uuid5(NAMESPACE_OID, file_name)))):
        os.makedirs(folder)

    if not os.path.exists(path := os.path.abspath(os.path.join(folder, file_name))) or not check_existence:
        return path

    raise FileExistsError(f"File {path} already exists.")


def _iter(file: BinaryIO):
    while chunk := file.read(16 * 2**20):
        yield chunk


def store(upload: UploadFile):
    local_file_path: str = local_path(upload.filename)
    with open(local_file_path, "wb") as file:
        for chunk in _iter(upload.file):
            file.write(chunk)

    return local_file_path


if __name__ == "__main__":
    pass
