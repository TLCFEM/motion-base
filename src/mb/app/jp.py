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
from fastapi import APIRouter, Depends, HTTPException, UploadFile, BackgroundTasks
from pymongo.errors import ServerSelectionTimeoutError

from .response import UploadResponse
from .utility import User, is_active, create_token
from ..celery import celery, get_stats
from ..record.parser import ParserNIED
from ..record.sync_record import create_task, delete_task
from ..utility.files import store, FileProxy

router = APIRouter(tags=["Japan"])


# noinspection DuplicatedCode
def _parse_archive_local(
    archive_uri: str, user_id: str, task_id: str | None = None, overwrite_existing: bool = True
) -> list[str]:
    try:
        with FileProxy(archive_uri, None, always_delete_on_exit=True) as archive_file:
            results = ParserNIED.parse_archive(
                archive_obj=archive_file.file,
                user_id=user_id,
                archive_name=archive_file.file_name,
                task_id=task_id,
                overwrite_existing=overwrite_existing,
            )
            return archive_file.bulk(results)
    except Exception as exc:
        # we need to handle the exception here
        # throwing exception in background task queue will terminate all tasks
        structlog.get_logger(__name__).error(f"Failed to parse archive {archive_uri}.", exc_info=exc)
        if task_id is not None:
            delete_task(task_id)
        return []


@celery.task(
    autoretry_for=(ConnectionError, TimeoutError, ServerSelectionTimeoutError),
    retry_kwargs={"max_retries": 3},
    default_retry_delay=10,
)
def _parse_archive(
    archive_uri: str, access_token: str, user_id: str, task_id: str | None = None, overwrite_existing: bool = True
) -> list[str]:
    try:
        with FileProxy(archive_uri, access_token) as archive_file:
            results = ParserNIED.parse_archive(
                archive_obj=archive_file.file,
                user_id=user_id,
                archive_name=archive_file.file_name,
                task_id=task_id,
                overwrite_existing=overwrite_existing,
            )
            return archive_file.bulk(results)
    except Exception as exc:
        if task_id is not None:
            create_task(task_id)
        raise exc


# noinspection DuplicatedCode
@router.post("/upload", status_code=HTTPStatus.ACCEPTED, response_model=UploadResponse)
async def upload_archive(
    archives: list[UploadFile],
    tasks: BackgroundTasks,
    user: User = Depends(is_active),
    wait_for_result: bool = False,
    overwrite_existing: bool = True,
):
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

    access_token: str = create_token(user.username).access_token
    has_worker: bool = get_stats() is not None

    valid_uris: list[str] = []
    for archive in archives:
        try:
            ParserNIED.validate_archive(archive.filename)
            valid_uris.append(store(archive))
        except ValueError:
            pass

    if not wait_for_result:
        task_id_pool: list[str] = []
        if has_worker:
            for archive_uri in valid_uris:
                task_id: str = create_task()
                _parse_archive.delay(archive_uri, access_token, user.id, task_id, overwrite_existing)
                task_id_pool.append(task_id)
        else:
            for archive_uri in valid_uris:
                task_id: str = create_task()
                tasks.add_task(_parse_archive_local, archive_uri, user.id, task_id, overwrite_existing)
                task_id_pool.append(task_id)

        return UploadResponse(
            message="Successfully uploaded and will be processed in the background.", task_ids=task_id_pool
        )

    if has_worker:
        records = [
            _parse_archive.delay(archive_uri, access_token, user.id, None, overwrite_existing).get()
            for archive_uri in valid_uris
        ]
    else:
        records = [_parse_archive_local(archive_uri, user.id, None, overwrite_existing) for archive_uri in valid_uris]

    return UploadResponse(
        message="Successfully uploaded and processed.", records=list(itertools.chain.from_iterable(records))
    )
