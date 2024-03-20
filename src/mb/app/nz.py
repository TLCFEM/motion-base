#  Copyright (C) 2022-2023 Theodore Chang
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
import os
import tarfile
from http import HTTPStatus
from uuid import UUID

import structlog
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile

from .response import UploadResponse
from .utility import UploadTask, User, create_task, is_active, send_notification
from ..record.parser import ParserNZSM

router = APIRouter(tags=["New Zealand"])

_logger = structlog.get_logger(__name__)


async def _parse_archive_in_background(archive: UploadFile, user_id: UUID, task_id: UUID | None = None) -> list:
    task: UploadTask | None = None
    if task_id is not None:
        task = await UploadTask.find_one(UploadTask.id == task_id)

    records: list = []
    with tarfile.open(mode="r:gz", fileobj=archive.file) as archive_obj:
        if task:
            task.pid = os.getpid()
            task.total_size = len(archive_obj.getnames())
        for f in archive_obj:
            if task:
                task.current_size += 1
                await task.save()
            if not f.name.endswith(".V2A"):
                continue
            target = archive_obj.extractfile(f)
            if target:
                try:
                    records.extend(await ParserNZSM.parse_archive(target, user_id, os.path.basename(f.name)))
                except Exception as e:
                    _logger.critical("Failed to parse.", file_name=f.name, exc_info=e)

    if task:
        await task.delete()

    return records


async def _parse_archive_in_background_task(archive: UploadFile, user_id: UUID, task_id: UUID):
    records: list = await _parse_archive_in_background(archive, user_id, task_id)
    mail_body = "The following records are parsed:\n"
    mail_body += "\n".join([f"{record}" for record in records])
    mail = {"body": mail_body}
    await send_notification(mail)


@router.post("/upload", status_code=HTTPStatus.ACCEPTED, response_model=UploadResponse)
async def upload_archive(
    archives: list[UploadFile], tasks: BackgroundTasks, user: User = Depends(is_active), wait_for_result: bool = False
):
    if not user.can_upload:
        raise HTTPException(HTTPStatus.UNAUTHORIZED, detail="User is not allowed to upload.")

    valid_archives: list[UploadFile] = []
    for archive in archives:
        if archive.filename.endswith(".tar.gz"):
            valid_archives.append(archive)

    if not wait_for_result:
        task_id_pool: list[UUID] = []
        for archive in valid_archives:
            task_id: UUID = await create_task()
            tasks.add_task(_parse_archive_in_background_task, archive, user.id, task_id)
            task_id_pool.append(task_id)

        return UploadResponse(
            message="Successfully uploaded and will be processed in the background.", task_ids=task_id_pool
        )

    return UploadResponse(
        message="Successfully uploaded and processed.",
        records=list(
            itertools.chain.from_iterable(
                [await _parse_archive_in_background(archive, user.id) for archive in valid_archives]
            )
        ),
    )
