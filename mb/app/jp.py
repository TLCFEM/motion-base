#  Copyright (C) 2022 Theodore Chang
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
from http import HTTPStatus
from typing import cast

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile

from mb.app.response import SequenceResponse
from mb.app.utility import UploadTask, User, background_tasks, is_active, send_notification
from mb.record.jp import NIED, ParserNIED, retrieve_single_record
from mb.record.record import Record

router = APIRouter(tags=['Japan'])


async def _parse_archive_in_background(archive: UploadFile, task: UploadTask | None = None) -> list:
    records = await ParserNIED.parse_archive(
        archive_obj=archive.file,
        archive_name=archive.filename,
        task=task
    )
    return records


async def _parse_archive_in_background_task(archive: UploadFile, task: UploadTask):
    records = await _parse_archive_in_background(archive, task)
    if task.task_id in background_tasks:
        del background_tasks[task.task_id]
    mail_body = 'The following records are parsed:\n'
    mail_body += '\n'.join([f'{record}' for record in records])
    mail = {'body': mail_body}
    await send_notification(mail)


@router.post('/upload', status_code=HTTPStatus.ACCEPTED)
async def upload_archive(
        archive: UploadFile,
        tasks: BackgroundTasks,
        user: User = Depends(is_active),
        wait_for_result: bool = False):
    if not user.can_upload:
        raise HTTPException(HTTPStatus.UNAUTHORIZED, detail='User is not allowed to upload.')
    try:
        ParserNIED.validate_archive(archive.filename)
    except ValueError as e:
        raise HTTPException(HTTPStatus.BAD_REQUEST, detail=str(e)) from e

    if not wait_for_result:
        task = UploadTask()
        background_tasks[task.task_id] = task
        tasks.add_task(_parse_archive_in_background_task, archive, task)

        return {
            'message': 'successfully uploaded and will be processed in the background',
            'task_id': task.task_id
        }

    records = await _parse_archive_in_background(archive)

    return {'message': 'successfully uploaded and processed', 'records': records}


@router.get('/raw/jackpot', response_model=NIED)
async def download_single_random_raw_record():
    '''
    Retrieve a single random record from the database.
    '''
    result = await NIED.aggregate([{'$sample': {'size': 1}}], projection_model=NIED).to_list()
    if result:
        return result[0]

    raise HTTPException(HTTPStatus.NO_CONTENT, detail='Record not found')


@router.get('/waveform/jackpot', response_model=SequenceResponse)
async def download_single_random_waveform():
    '''
    Retrieve a single random waveform from the database.
    '''
    result = await download_single_random_raw_record()

    interval, record = result.to_waveform()
    return {'file_name': result.file_name, 'interval': interval, 'data': record.tolist()}


@router.get('/spectrum/jackpot', response_model=SequenceResponse)
async def download_single_random_spectrum():
    '''
    Retrieve a single random spectrum from the database.
    '''
    result = await download_single_random_raw_record()

    frequency, record = result.to_spectrum()
    return {'file_name': result.file_name, 'interval': frequency, 'data': record.tolist()}


@router.get('/raw/{file_name}', response_model=NIED)
async def download_single_raw_record(file_name: str, sub_category: str):
    '''
    Retrieve raw accelerograph record.
    The NIED collection has two sub-categories: `knt` and `kik`.
    This endpoint has a limit of 1 record per request since the file name is unique.
    In order to download more records, please use other endpoints.
    '''
    result: Record = await retrieve_single_record(sub_category.lower(), file_name.upper())
    if result:
        return cast(NIED, result)

    raise HTTPException(HTTPStatus.NOT_FOUND, detail='Record not found')


@router.get('/waveform/{file_name}', response_model=SequenceResponse)
async def download_single_waveform(file_name: str, sub_category: str, normalised: bool = False):
    '''
    Retrieve raw accelerograph waveform.
    The NIED collection has two sub-categories: `knt` and `kik`.
    This endpoint has a limit of 1 record per request since the file name is unique.
    In order to download more records, please use other endpoints.
    '''
    result: Record = await retrieve_single_record(sub_category.lower(), file_name.upper())

    if result:
        interval, record = result.to_waveform(normalised=normalised)
        return {'file_name': result.file_name, 'interval': interval, 'data': record.tolist()}

    raise HTTPException(HTTPStatus.NOT_FOUND, detail='Record not found')


@router.get('/spectrum/{file_name}', response_model=SequenceResponse)
async def download_single_spectrum(file_name: str, sub_category: str):
    '''
    Retrieve raw accelerograph spectrum.
    The NIED collection has two sub-categories: `knt` and `kik`.
    This endpoint has a limit of 1 record per request since the file name is unique.
    In order to download more records, please use other endpoints.
    '''
    result: Record = await retrieve_single_record(sub_category.lower(), file_name.upper())

    if result:
        frequency, record = result.to_spectrum()
        return {'file_name': result.file_name, 'interval': frequency, 'data': record.tolist()}

    raise HTTPException(HTTPStatus.NOT_FOUND, detail='Record not found')
