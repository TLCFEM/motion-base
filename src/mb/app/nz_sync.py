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

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from pymongo.errors import ServerSelectionTimeoutError

from .response import UploadResponse
from .utility import User, is_active, create_token
from ..celery import celery
from ..record.sync_parser import ParserNZSM
from ..record.sync_record import create_task
from ..utility.files import store, FileProxy

router = APIRouter(tags=["New Zealand"])


@celery.task(
    autoretry_for=(ConnectionError, TimeoutError, ServerSelectionTimeoutError),
    retry_kwargs={"max_retries": 3},
    default_retry_delay=10,
)
def _parse_archive(archive_uri: str, access_token: str, user_id: str, task_id: str | None = None) -> list[str]:
    try:
        with FileProxy(archive_uri, access_token) as archive_file:
            return ParserNZSM.parse_archive(
                archive_obj=archive_file.file, user_id=user_id, archive_name=archive_file.file_name, task_id=task_id
            )
    except Exception as exc:
        if task_id is not None:
            create_task(task_id)
        raise exc


@router.post("/upload", status_code=HTTPStatus.ACCEPTED, response_model=UploadResponse)
async def upload_archive(archives: list[UploadFile], user: User = Depends(is_active), wait_for_result: bool = False):
    """
    Upload a compressed archive.

    The archive must be gzip-compressed tarball or zip archive.
    All files will be checked and those with ".V2A" and/or ".V1A" extensions will be parsed.

    Two modes are supported, one can choose to wait for the result or not.
    If the result is not waited, the task ID will be returned.
    Use `/task/status/{task_id}` to check the status of the target task.
    """
    if not user.can_upload:
        raise HTTPException(HTTPStatus.UNAUTHORIZED, detail="User is not allowed to upload.")

    access_token: str = create_token(user.username).access_token

    valid_uris: list[str] = []
    for archive in archives:
        if archive.filename.endswith((".tar.gz", ".zip")):
            valid_uris.append(store(archive))

    if not wait_for_result:
        task_id_pool: list[str] = []
        for archive_uri in valid_uris:
            task_id: str = create_task()
            _parse_archive.delay(archive_uri, access_token, user.id, task_id)
            task_id_pool.append(task_id)

        return UploadResponse(
            message="Successfully uploaded and will be processed in the background.", task_ids=task_id_pool
        )

    return UploadResponse(
        message="Successfully uploaded and processed.",
        records=list(
            itertools.chain.from_iterable(
                [_parse_archive.delay(archive_uri, access_token, user.id).get() for archive_uri in valid_uris]
            )
        ),
    )
