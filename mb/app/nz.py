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
import os
import tarfile
from datetime import datetime
from http import HTTPStatus
from uuid import UUID

import numpy as np
import structlog
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, UploadFile

from mb.app.response import MetadataListResponse, MetadataResponse, ResponseSpectrumResponse, SequenceResponse
from mb.app.utility import UploadTask, User, create_task, generate_query_string, is_active, send_notification
from mb.record.nz import MetadataNZSM, NZSM, ParserNZSM, retrieve_single_record
from mb.record.response_spectrum import response_spectrum

router = APIRouter(tags=['New Zealand'])

_logger = structlog.get_logger(__name__)


def _validate_record_type(record_type: str) -> str:
    type_char = record_type.lower()[0]
    if type_char not in {'a', 'v', 'd'}:
        raise HTTPException(400, detail='Record type must be one of `acceleration`, `velocity` or `displacement`.')

    return type_char


async def _parse_archive_in_background(archive: UploadFile, user_id: UUID, task_id: UUID | None = None) -> list:
    task: UploadTask | None = None
    if task_id is not None:
        task = await UploadTask.find_one(UploadTask.id == task_id)

    records: list = []
    with tarfile.open(mode='r:gz', fileobj=archive.file) as archive_obj:
        if task:
            task.total_size = len(archive_obj.getnames())
        for f in archive_obj:
            if task:
                task.current_size += 1
                await task.save()
            if not f.name.endswith('.V2A'):
                continue
            target = archive_obj.extractfile(f)
            if target:
                try:
                    records.extend(await ParserNZSM.parse_archive(target, user_id, os.path.basename(f.name)))
                except Exception as e:
                    _logger.critical('Failed to parse.', file_name=f.name, exe_info=e)

    if task:
        await task.delete()

    return records


async def _parse_archive_in_background_task(archive: UploadFile, user_id: UUID, task_id: UUID):
    records: list = await _parse_archive_in_background(archive, user_id, task_id)
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
    if not archive.filename.endswith('.tar.gz'):
        raise HTTPException(HTTPStatus.BAD_REQUEST, detail='Archive must be a tar.gz file.')

    if not wait_for_result:
        task_id: UUID = await create_task()
        tasks.add_task(_parse_archive_in_background_task, archive, user.id, task_id)

        return {
            'message': 'successfully uploaded and will be processed in the background',
            'task_id': task_id,
        }

    records: list = await _parse_archive_in_background(archive, user.id)

    return {'message': 'successfully uploaded and processed', 'records': records}


@router.post('/query', response_model=MetadataListResponse)
async def query_records(
        min_magnitude: float | None = Query(default=None, ge=0, le=10),
        max_magnitude: float | None = Query(default=None, ge=0, le=10),
        sub_category: str | None = Query(default=None, regex='^(un)?processed$'),
        event_location: list[float, float] | None = Query(default=None, min_items=2, max_items=2),
        station_location: list[float, float] | None = Query(default=None, min_items=2, max_items=2),
        from_date: datetime | None = Query(default=None),
        to_date: datetime | None = Query(default=None),
        page_size: int | None = Query(default=None, ge=1, le=1000),
        page_number: int | None = Query(default=None, ge=0)
):
    """
    Query records from the database.
    """
    query_dict: dict = generate_query_string(
        min_magnitude=min_magnitude,
        max_magnitude=max_magnitude,
        sub_category=sub_category,
        event_location=event_location,
        station_location=station_location,
        from_date=from_date,
        to_date=to_date
    )

    if page_size is None:
        page_size = 10
    if page_number is None:
        page_number = 0

    result = NZSM.find(query_dict).skip(page_number * page_size).limit(page_size).project(MetadataNZSM)
    if result:
        return MetadataListResponse(
            query=query_dict,
            result=[MetadataResponse(**record.dict()) async for record in result])

    raise HTTPException(HTTPStatus.NO_CONTENT, detail='No records found')


@router.get('/raw/jackpot', response_model=NZSM)
async def download_single_random_raw_record():
    '''
    Retrieve a single random record from the database.
    '''
    result: list[NZSM] = await NZSM.aggregate([{'$sample': {'size': 1}}], projection_model=NZSM).to_list()
    if result:
        return result[0]

    raise HTTPException(HTTPStatus.NO_CONTENT, detail='Record not found')


@router.get('/waveform/jackpot', response_model=SequenceResponse)
async def download_single_random_waveform(normalised: bool = False):
    '''
    Retrieve a single random waveform from the database.
    '''
    result: NZSM = await download_single_random_raw_record()

    interval, record = result.to_waveform(normalised=normalised, unit='cm/s/s')
    # noinspection PyTypeChecker
    return SequenceResponse(**result.dict(), interval=interval, data=record.tolist())


@router.get('/spectrum/jackpot', response_model=SequenceResponse)
async def download_single_random_spectrum():
    '''
    Retrieve a single random spectrum from the database.
    '''
    result: NZSM = await download_single_random_raw_record()

    frequency, record = result.to_spectrum(unit='cm/s/s')
    # noinspection PyTypeChecker
    return SequenceResponse(**result.dict(), interval=frequency, data=record.tolist())


@router.get('/response_spectrum/jackpot', response_model=ResponseSpectrumResponse)
async def download_single_random_response_spectrum(
        damping_ratio: float = Query(0.05, ge=0., le=1.),
        period_end: float = Query(20., ge=0.),
        period_step: float = Query(0.05, ge=0.),
        normalised: bool = Query(default=False)):
    """
    Retrieve a single random response spectrum from the database.
    """
    result: NZSM = await download_single_random_raw_record()

    interval, record = result.to_waveform(normalised=normalised, unit='cm/s/s')
    period = np.arange(0, period_end + period_step, period_step)
    spectrum = response_spectrum(damping_ratio, interval, record, period)
    # noinspection PyTypeChecker
    return ResponseSpectrumResponse(**result.dict(), data=spectrum.tolist())


@router.get('/raw/{file_id_or_name}', response_model=NZSM)
async def download_single_raw_record(file_id_or_name: str):
    '''
    Retrieve raw record.
    The NZStrongMotion collection has acceleration records.
    This endpoint has a limit of 1 record per request since the file name is unique.
    In order to download more records, please use other endpoints.
    '''
    result: NZSM = await retrieve_single_record(file_id_or_name)
    if result:
        return result

    raise HTTPException(HTTPStatus.NOT_FOUND, detail='Record not found')


@router.get('/waveform/{file_id_or_name}', response_model=SequenceResponse)
async def download_single_waveform(file_id_or_name: str, normalised: bool = False):
    '''
    Retrieve raw waveform.
    The NZStrongMotion collection has acceleration records.
    This endpoint has a limit of 1 record per request since the file name is unique.
    In order to download more records, please use other endpoints.
    '''
    result: NZSM = await retrieve_single_record(file_id_or_name)

    if result:
        interval, record = result.to_waveform(normalised=normalised, unit='cm/s/s')
        # noinspection PyTypeChecker
        return SequenceResponse(**result.dict(), interval=interval, data=record.tolist())

    raise HTTPException(HTTPStatus.NOT_FOUND, detail='Record not found')


@router.get('/spectrum/{file_id_or_name}', response_model=SequenceResponse)
async def download_single_spectrum(file_id_or_name: str):
    '''
    Retrieve raw spectrum.
    The NZStrongMotion collection has acceleration records.
    This endpoint has a limit of 1 record per request since the file name is unique.
    In order to download more records, please use other endpoints.
    '''
    result: NZSM = await retrieve_single_record(file_id_or_name)

    if result:
        frequency, record = result.to_spectrum(unit='cm/s/s')
        # noinspection PyTypeChecker
        return SequenceResponse(**result.dict(), interval=frequency, data=record.tolist())

    raise HTTPException(HTTPStatus.NOT_FOUND, detail='Record not found')


@router.get('/response_spectrum/{file_id_or_name}', response_model=ResponseSpectrumResponse)
async def download_single_response_spectrum(
        file_id_or_name: str,
        damping_ratio: float = Query(0.05, ge=0., le=1.),
        period_end: float = Query(20., ge=0.),
        period_step: float = Query(0.05, ge=0.),
        normalised: bool = Query(default=False)):
    """
    Retrieve a single response spectrum from the database.
    """
    result: NZSM = await retrieve_single_record(file_id_or_name)

    interval, record = result.to_waveform(normalised=normalised, unit='cm/s/s')
    period = np.arange(0, period_end + period_step, period_step)
    spectrum = response_spectrum(damping_ratio, interval, record, period)
    # noinspection PyTypeChecker
    return ResponseSpectrumResponse(**result.dict(), data=spectrum.tolist())
