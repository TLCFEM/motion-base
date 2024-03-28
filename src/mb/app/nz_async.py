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

import structlog
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile

from .response import UploadResponse
from .utility import User, is_active, send_notification
from ..record.async_parser import ParserNZSM
from ..record.async_record import create_task
from ..utility.files import FileProxy, store

router = APIRouter(tags=["New Zealand"])

_logger = structlog.get_logger(__name__)


# noinspection DuplicatedCode
async def _parse_archive_in_background(archive_uri: str, user_id: str, task_id: str | None = None) -> list:
    with FileProxy(archive_uri, None) as archive_file:
        return await ParserNZSM.parse_archive(
            archive_obj=archive_file.file, user_id=user_id, archive_name=archive_file.file_name, task_id=task_id
        )


async def _parse_archive_in_background_task(archive_uri: str, user_id: str, task_id: str):
    records: list = await _parse_archive_in_background(archive_uri, user_id, task_id)
    mail_body = "The following records are parsed:\n"
    mail_body += "\n".join([f"{record}" for record in records])
    mail = {"body": mail_body}
    await send_notification(mail)


@router.post("/upload", status_code=HTTPStatus.ACCEPTED, response_model=UploadResponse)
async def upload_archive(
    archives: list[UploadFile], tasks: BackgroundTasks, user: User = Depends(is_active), wait_for_result: bool = False
):
    """
    Upload a compressed archive.

    The archive must be gzip-compressed tarball.
    The zip-compressed archive is not supported due to some technical issues.
    All files will be checked and those with ".V2A" and/or ".V1A" extensions will be parsed.

    Two modes are supported, one can choose to wait for the result or not.
    If the result is not waited, the task ID will be returned.
    Use `/task/status/{task_id}` to check the status of the target task.
    """
    if not user.can_upload:
        raise HTTPException(HTTPStatus.UNAUTHORIZED, detail="User is not allowed to upload.")

    valid_uris: list[str] = []
    for archive in archives:
        # ".zip" does not work, see: https://github.com/python/cpython/issues/70363
        if archive.filename.endswith(".tar.gz"):
            valid_uris.append(store(archive))

    if not wait_for_result:
        task_id_pool: list[str] = []
        for archive_uri in valid_uris:
            task_id: str = await create_task()
            tasks.add_task(_parse_archive_in_background_task, archive_uri, user.id, task_id)
            task_id_pool.append(task_id)

        return UploadResponse(
            message="Successfully uploaded and will be processed in the background.", task_ids=task_id_pool
        )

    return UploadResponse(
        message="Successfully uploaded and processed.",
        records=list(
            itertools.chain.from_iterable(
                [await _parse_archive_in_background(archive_uri, user.id) for archive_uri in valid_uris]
            )
        ),
    )
