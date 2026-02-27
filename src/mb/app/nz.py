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

import itertools
from http import HTTPStatus

import structlog
from elastic_transport import ConnectionTimeout

# noinspection PyPackageRequirements
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile
from pymongo.errors import ServerSelectionTimeoutError

from ..celery import celery, get_stats
from ..record.parser import ParserNZSM
from ..record.sync_record import create_task, delete_task
from ..utility.files import FileProxy, pack, store
from .response import UploadResponse
from .utility import User, create_token, is_active

router = APIRouter(tags=["New Zealand"])


# noinspection DuplicatedCode
def _parse_archive_local(
    archive_uri: str,
    user_id: str,
    task_id: str | None = None,
    overwrite_existing: bool = True,
) -> list[str]:
    try:
        with FileProxy(archive_uri, None, always_delete_on_exit=True) as archive_file:
            results = ParserNZSM.parse_archive(
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
        structlog.get_logger(__name__).error(
            f"Failed to parse archive {archive_uri}.", exc_info=exc
        )
        if task_id is not None:
            delete_task(task_id)
        return []


@celery.task(
    autoretry_for=(
        ConnectionError,
        TimeoutError,
        ConnectionTimeout,
        ServerSelectionTimeoutError,
    ),
    retry_kwargs={"max_retries": 3},
    default_retry_delay=10,
)
def _parse_archive(
    archive_uri: str,
    access_token: str,
    user_id: str,
    task_id: str | None = None,
    overwrite_existing: bool = True,
) -> list[str]:
    try:
        with FileProxy(archive_uri, access_token) as archive_file:
            results = ParserNZSM.parse_archive(
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
def upload_archive(
    archives: list[UploadFile],
    tasks: BackgroundTasks,
    user: User = Depends(is_active),
    wait_for_result: bool = False,
    overwrite_existing: bool = True,
):
    """
    Upload a compressed archive.

    The archive shall be gzip-compressed tarball or zip archive.
    All files will be checked and those with ".V2A" and/or ".V1A" extensions will be parsed.
    It is possible to upload ".V2A" and/or ".V1A" files directly.
    In this case, those file will be packed into a tarball and then processed.

    Two modes are supported, one can choose to wait for the result or not.
    If the result is not waited, the task ID will be returned.
    Use `/task/status/{task_id}` to check the status of the target task.
    """
    if not user.can_upload:
        raise HTTPException(
            HTTPStatus.UNAUTHORIZED, detail="User is not allowed to upload."
        )

    access_token: str = create_token(user.username).access_token
    has_worker: bool = get_stats() is not None

    valid_uris: list[str] = []
    plain_files: list[UploadFile] = []
    for archive in archives:
        if archive.filename.endswith((".tar.gz", ".zip")):
            valid_uris.append(store(archive))
        else:
            plain_files.append(archive)

    if plain_files:
        valid_uris.append(pack(plain_files))

    if not wait_for_result:
        task_id_pool: list[str] = []
        if has_worker:
            for archive_uri in valid_uris:
                task_id: str = create_task()
                _parse_archive.delay(
                    archive_uri, access_token, user.id, task_id, overwrite_existing
                )
                task_id_pool.append(task_id)
        else:
            for archive_uri in valid_uris:
                task_id: str = create_task()
                tasks.add_task(
                    _parse_archive_local,
                    archive_uri,
                    user.id,
                    task_id,
                    overwrite_existing,
                )
                task_id_pool.append(task_id)

        return UploadResponse(
            message="Successfully uploaded and will be processed in the background.",
            task_ids=task_id_pool,
            records=None,
        )

    if has_worker:
        records = [
            _parse_archive.delay(
                archive_uri, access_token, user.id, None, overwrite_existing
            ).get()
            for archive_uri in valid_uris
        ]
    else:
        records = [
            _parse_archive_local(archive_uri, user.id, None, overwrite_existing)
            for archive_uri in valid_uris
        ]

    return UploadResponse(
        message="Successfully uploaded and processed.",
        records=list(itertools.chain.from_iterable(records)),
        task_ids=None,
    )
