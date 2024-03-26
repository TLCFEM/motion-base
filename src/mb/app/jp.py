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

import itertools
from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile

from .response import UploadResponse
from .utility import User, create_task, is_active
from ..celery import celery
from ..record.sync_parser import ParserNIED
from ..utility.files import store

router = APIRouter(tags=["Japan"])


@celery.task
def _parse_archive_in_background(archive: str, user_id: UUID, task_id: UUID | None = None) -> list[str]:
    return ParserNIED.parse_archive(archive_obj=archive, user_id=user_id, task_id=task_id)


@router.post("/upload", status_code=HTTPStatus.ACCEPTED, response_model=UploadResponse)
async def upload_archive(archives: list[UploadFile], user: User = Depends(is_active), wait_for_result: bool = False):
    """
    Upload a compressed archive.

    The archive must be gzip-compressed tarball.
    The zip-compressed archive is not supported due to some technical issues.
    All valid files will be parsed.

    Two modes are supported, one can choose to wait for the result or not.
    If the result is not waited, the task ID will be returned.
    Use `/task/status/{task_id}` to check the status of the target task.
    """
    if not user.can_upload:
        raise HTTPException(HTTPStatus.UNAUTHORIZED, detail="User is not allowed to upload.")

    valid_archives: list[str] = []
    for archive in archives:
        try:
            ParserNIED.validate_archive(archive.filename)
            valid_archives.append(store(archive))
        except ValueError:
            pass

    if not wait_for_result:
        task_id_pool: list[UUID] = []
        for archive in valid_archives:
            task_id: UUID = await create_task()
            _parse_archive_in_background.delay(archive, user.id, task_id)
            task_id_pool.append(task_id)

        return UploadResponse(
            message="Successfully uploaded and will be processed in the background.", task_ids=task_id_pool
        )

    return UploadResponse(
        message="Successfully uploaded and processed.",
        records=list(
            itertools.chain.from_iterable(
                [_parse_archive_in_background.delay(archive, user.id) for archive in valid_archives]
            )
        ),
    )
