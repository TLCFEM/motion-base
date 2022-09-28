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
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, UploadFile

from mb.app.response import IDListResponse, SequenceResponse
from mb.app.utility import User, create_task, is_active, send_notification
from mb.record.jp import NIED, ParserNIED, retrieve_single_record

router = APIRouter(tags=['Japan'])


async def _parse_archive_in_background(archive: UploadFile, task_id: UUID | None = None) -> list:
    records: list = await ParserNIED.parse_archive(
        archive_obj=archive.file,
        archive_name=archive.filename,
        task_id=task_id
    )
    return records


async def _parse_archive_in_background_task(archive: UploadFile, task_id: UUID):
    records: list = await _parse_archive_in_background(archive, task_id)
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
        task_id: UUID = await create_task()
        tasks.add_task(_parse_archive_in_background_task, archive, task_id)
        return {
            'message': 'successfully uploaded and will be processed in the background',
            'task_id': task_id
        }

    records: list = await _parse_archive_in_background(archive)

    return {'message': 'successfully uploaded and processed', 'records': records}


@router.get('/raw/jackpot', response_model=NIED)
async def download_single_random_raw_record():
    '''
    Retrieve a single random record from the database.
    '''
    result: list[NIED] = await NIED.aggregate([{'$sample': {'size': 1}}], projection_model=NIED).to_list()
    if result:
        return result[0]

    raise HTTPException(HTTPStatus.NO_CONTENT, detail='Record not found')


@router.get('/waveform/jackpot', response_model=SequenceResponse)
async def download_single_random_waveform():
    '''
    Retrieve a single random waveform from the database.
    '''
    result: NIED = await download_single_random_raw_record()

    interval, record = result.to_waveform(unit='cm/s/s')
    return {
        'id': result.id,
        'file_name': result.file_name,
        'latitude': result.latitude,
        'longitude': result.longitude,
        'station_latitude': result.station_latitude,
        'station_longitude': result.station_longitude,
        'interval': interval,
        'data': record.tolist()
    }


@router.get('/spectrum/jackpot', response_model=SequenceResponse)
async def download_single_random_spectrum():
    '''
    Retrieve a single random spectrum from the database.
    '''
    result: NIED = await download_single_random_raw_record()

    frequency, record = result.to_spectrum()
    return {
        'id': result.id,
        'file_name': result.file_name,
        'latitude': result.latitude,
        'longitude': result.longitude,
        'station_latitude': result.station_latitude,
        'station_longitude': result.station_longitude,
        'interval': frequency,
        'data': record.tolist()
    }


@router.get('/raw/{file_name}', response_model=NIED)
async def download_single_raw_record(file_name: str, sub_category: str):
    '''
    Retrieve raw accelerograph record.
    The NIED collection has two sub-categories: `knt` and `kik`.
    This endpoint has a limit of 1 record per request since the file name is unique.
    In order to download more records, please use other endpoints.
    '''
    result: NIED = await retrieve_single_record(sub_category.lower(), file_name.upper())
    if result:
        return result

    raise HTTPException(HTTPStatus.NOT_FOUND, detail='Record not found')


@router.get('/waveform/{file_name}', response_model=SequenceResponse)
async def download_single_waveform(file_name: str, sub_category: str, normalised: bool = False):
    '''
    Retrieve raw accelerograph waveform.
    The NIED collection has two sub-categories: `knt` and `kik`.
    This endpoint has a limit of 1 record per request since the file name is unique.
    In order to download more records, please use other endpoints.
    '''
    result: NIED = await retrieve_single_record(sub_category.lower(), file_name.upper())

    if result:
        interval, record = result.to_waveform(normalised=normalised, unit='cm/s/s')
        return {
            'id': result.id,
            'file_name': result.file_name,
            'latitude': result.latitude,
            'longitude': result.longitude,
            'station_latitude': result.station_latitude,
            'station_longitude': result.station_longitude,
            'interval': interval,
            'data': record.tolist()
        }

    raise HTTPException(HTTPStatus.NOT_FOUND, detail='Record not found')


@router.get('/spectrum/{file_name}', response_model=SequenceResponse)
async def download_single_spectrum(file_name: str, sub_category: str):
    '''
    Retrieve raw accelerograph spectrum.
    The NIED collection has two sub-categories: `knt` and `kik`.
    This endpoint has a limit of 1 record per request since the file name is unique.
    In order to download more records, please use other endpoints.
    '''
    result: NIED = await retrieve_single_record(sub_category.lower(), file_name.upper())

    if result:
        frequency, record = result.to_spectrum()
        return {
            'id': result.id,
            'file_name': result.file_name,
            'latitude': result.latitude,
            'longitude': result.longitude,
            'station_latitude': result.station_latitude,
            'station_longitude': result.station_longitude,
            'interval': frequency,
            'data': record.tolist()
        }

    raise HTTPException(HTTPStatus.NOT_FOUND, detail='Record not found')


@router.post('/query', response_model=IDListResponse)
async def query_records(
        min_magnitude: float = Query(default=0, ge=0, le=10),
        max_magnitude: float = Query(default=10, ge=0, le=10),
        sub_category: str | None = Query(default=None, regex='^(knt|kik)$'),
        page_size: int = Query(default=100, ge=1, le=1000),
        page_number: int = Query(default=0, ge=0)
):
    '''
    Query records from the database.
    '''
    query_dict = {
        '$and': [
            {'magnitude': {
                '$gte': min_magnitude,
                '$lte': max_magnitude
            }},
            {'sub_category': sub_category.lower() if sub_category else {'$regex': 'knt|kik', '$options': 'i'}}
        ]
    }

    result = NIED.find(query_dict).skip(page_number * page_size).limit(page_size)
    if result:
        return IDListResponse(query=query_dict, id=[record.id async for record in result])

    raise HTTPException(HTTPStatus.NO_CONTENT, detail='No records found')
