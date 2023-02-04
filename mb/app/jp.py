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
import itertools
from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile

from mb.app.utility import User, create_task, is_active, send_notification
from mb.record.parser import ParserNIED

router = APIRouter(tags=['Japan'])


async def _parse_archive_in_background(archive: UploadFile, user_id: UUID, task_id: UUID | None = None) -> list:
    records: list = await ParserNIED.parse_archive(
        archive_obj=archive.file,
        user_id=user_id,
        archive_name=archive.filename,
        task_id=task_id
    )
    return records


async def _parse_archive_in_background_task(archive: UploadFile, user_id: UUID, task_id: UUID):
    records: list = await _parse_archive_in_background(archive, user_id, task_id)
    mail_body = 'The following records are parsed:\n'
    mail_body += '\n'.join([f'{record}' for record in records])
    mail = {'body': mail_body}
    await send_notification(mail)


@router.post('/upload', status_code=HTTPStatus.ACCEPTED)
async def upload_archive(
        archives: list[UploadFile],
        tasks: BackgroundTasks,
        user: User = Depends(is_active),
        wait_for_result: bool = False):
    if not user.can_upload:
        raise HTTPException(HTTPStatus.UNAUTHORIZED, detail='User is not allowed to upload.')

    valid_archives: list[UploadFile] = []
    for archive in archives:
        try:
            ParserNIED.validate_archive(archive.filename)
            valid_archives.append(archive)
        except ValueError:
            pass

    if not wait_for_result:
        task_id_pool: list[UUID] = []
        for archive in valid_archives:
            task_id: UUID = await create_task()
            tasks.add_task(_parse_archive_in_background_task, archive, user.id, task_id)
            task_id_pool.append(task_id)

        return {
            'message': 'successfully uploaded and will be processed in the background',
            'task_id': task_id_pool
        }

    records: list = [await _parse_archive_in_background(archive, user.id) for archive in valid_archives]

    return {'message': 'successfully uploaded and processed', 'records': list(itertools.chain.from_iterable(records))}
