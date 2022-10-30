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
import itertools
from datetime import datetime
from http import HTTPStatus
from uuid import UUID

import numpy as np
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, UploadFile

from mb.app.response import MetadataListResponse, MetadataResponse, ResponseSpectrumResponse, SequenceResponse, \
    SequenceSpectrumResponse
from mb.app.utility import User, create_task, generate_query_string, is_active, send_notification
from mb.record.jp import MetadataNIED, NIED, ParserNIED, retrieve_single_record
from mb.record.record import apply_filter, filter_regex, get_window, window_regex, zero_stuff
from mb.record.response_spectrum import response_spectrum

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


@router.post('/process', response_model=SequenceSpectrumResponse)
async def process_record(
        record_id: UUID,
        upsampling_rate: int | None = Query(None, ge=1),
        filter_length: int | None = Query(None, ge=8, description='half filter length, default to 8'),
        filter_type: str | None = Query(
            None, regex=filter_regex,
            description='filter type, any of `lowpass`, `highpass`, `bandpass`, `bandstop`'),
        window_type: str | None = Query(
            None, regex=window_regex,
            description=
            'window type, any of `flattop`, `blackmanharris`, `nuttall`, `hann`, `hamming`, `kaiser`, `chebwin`'),
        low_cut: float | None = Query(None, ge=0., description='low cut frequency in Hz, default to 0.05 Hz'),
        high_cut: float | None = Query(None, ge=0., description='high cut frequency in Hz, default to 40 Hz'),
        damping_ratio: float | None = Query(None, ge=0., le=1., description='damping ratio, default to 0.05'),
        period_end: float | None = Query(None, ge=0., description='maximum period of interest, default to 20 s'),
        period_step: float | None = Query(None, ge=0., description='period step, default to 0.05 s'),
        normalised: bool | None = Query(None, description='whether to normalise record, default to False'),
        with_spectrum: bool | None = Query(None, description='whether to perform DFT, default to False'),
        with_response_spectrum: bool | None = Query(
            None, description='whether to perform response spectrum, default to False'),
):
    result: NIED = await retrieve_single_record(record_id)

    if not result:
        raise HTTPException(HTTPStatus.NOT_FOUND, detail='Record not found.')

    record = SequenceSpectrumResponse(**result.dict())

    time_interval, waveform = result.to_waveform(unit='cm/s/s')

    if with_spectrum is None:
        with_spectrum = False
    if with_response_spectrum is None:
        with_response_spectrum = False

    if upsampling_rate is None:
        upsampling_rate = 1
    if filter_length is None:
        filter_length = 8
    if filter_type is None:
        filter_type = 'bandpass'
    if window_type is None:
        window_type = 'nuttall'
    if low_cut is None:
        low_cut = .05
    if high_cut is None:
        high_cut = 40.

    if low_cut >= high_cut:
        raise HTTPException(
            HTTPStatus.BAD_REQUEST,
            detail='Low cut frequency should be smaller than high cut frequency.')

    if damping_ratio is None:
        damping_ratio = 0.05
    if period_end is None:
        period_end = 20.
    if period_step is None:
        period_step = 0.05
    if normalised is None:
        normalised = False

    upsampled_interval = time_interval / upsampling_rate

    f0 = min(max(2 * low_cut * upsampled_interval, 0), 1)
    f1 = min(max(2 * high_cut * upsampled_interval, 0), 1)

    new_waveform: np.ndarray = apply_filter(
        get_window(filter_type, window_type, filter_length, [f0, f1], ratio=upsampling_rate),
        zero_stuff(upsampling_rate, waveform))

    record.time_interval = upsampled_interval
    record.waveform = new_waveform.tolist()
    if with_spectrum:
        frequency_interval, spectrum = NIED.perform_fft(1 / upsampled_interval, new_waveform)
        record.frequency_interval = frequency_interval
        record.spectrum = spectrum.tolist()
    if with_response_spectrum:
        period = np.arange(0, period_end + period_step, period_step)
        spectrum = response_spectrum(damping_ratio, upsampled_interval, new_waveform, period)
        record.response_spectrum = spectrum.tolist()

    return record


@router.post('/query', response_model=MetadataListResponse)
async def query_records(
        min_magnitude: float | None = Query(default=None, ge=0, le=10),
        max_magnitude: float | None = Query(default=None, ge=0, le=10),
        sub_category: str | None = Query(default=None, regex='^(knt|kik)$'),
        event_location: list[float, float] | None = Query(default=None, min_items=2, max_items=2),
        station_location: list[float, float] | None = Query(default=None, min_items=2, max_items=2),
        from_date: datetime | None = Query(default=None),
        to_date: datetime | None = Query(default=None),
        min_pga: float | None = Query(default=None),
        max_pga: float | None = Query(default=None),
        event_name: str | None = Query(default=None),
        direction: str | None = Query(default=None),
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
        to_date=to_date,
        min_pga=min_pga,
        max_pga=max_pga,
        event_name=event_name,
        direction=direction,
    )

    if page_size is None:
        page_size = 10
    if page_number is None:
        page_number = 0

    result = NIED.find(query_dict).skip(page_number * page_size).limit(page_size).project(MetadataNIED)
    if result:
        return MetadataListResponse(
            query=query_dict,
            result=[MetadataResponse(**record.dict()) async for record in result])

    raise HTTPException(HTTPStatus.NO_CONTENT, detail='No records found')


@router.get('/raw/jackpot', response_model=NIED)
async def download_single_random_raw_record():
    """
    Retrieve a single random record from the database.
    """
    result: list[NIED] = await NIED.aggregate([{'$sample': {'size': 1}}], projection_model=NIED).to_list()
    if result:
        return result[0]

    raise HTTPException(HTTPStatus.NO_CONTENT, detail='Record not found')


@router.get('/waveform/jackpot', response_model=SequenceResponse)
async def download_single_random_waveform(normalised: bool = False):
    """
    Retrieve a single random waveform from the database.
    """
    result: NIED = await download_single_random_raw_record()

    interval, record = result.to_waveform(normalised=normalised, unit='cm/s/s')
    # noinspection PyTypeChecker
    return SequenceResponse(**result.dict(), interval=interval, data=record.tolist())


@router.get('/spectrum/jackpot', response_model=SequenceResponse)
async def download_single_random_spectrum():
    """
    Retrieve a single random spectrum from the database.
    """
    result: NIED = await download_single_random_raw_record()

    frequency, record = result.to_spectrum()
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
    result: NIED = await download_single_random_raw_record()

    interval, record = result.to_waveform(normalised=normalised, unit='cm/s/s')
    period = np.arange(0, period_end + period_step, period_step)
    spectrum = response_spectrum(damping_ratio, interval, record, period)
    # noinspection PyTypeChecker
    return ResponseSpectrumResponse(**result.dict(), data=spectrum.tolist())


@router.get('/raw/{file_id_or_name}', response_model=NIED)
async def download_single_raw_record(
        file_id_or_name: str,
        sub_category: str | None = Query(default=None, regex='^(knt|kik)$')
):
    """
    Retrieve raw accelerograph record.
    The NIED collection has two sub-categories: `knt` and `kik`.
    This endpoint has a limit of 1 record per request since the file name is unique.
    In order to download more records, please use other endpoints.
    """
    result: NIED = await retrieve_single_record(file_id_or_name, sub_category)

    if result:
        return result

    raise HTTPException(HTTPStatus.NOT_FOUND, detail='Record not found')


@router.get('/waveform/{file_id_or_name}', response_model=SequenceResponse)
async def download_single_waveform(
        file_id_or_name: str,
        sub_category: str | None = Query(default=None, regex='^(knt|kik)$'),
        normalised: bool = Query(default=False)
):
    """
    Retrieve raw accelerograph waveform.
    The NIED collection has two sub-categories: `knt` and `kik`.
    This endpoint has a limit of 1 record per request since the file name is unique.
    In order to download more records, please use other endpoints.
    """
    result: NIED = await retrieve_single_record(file_id_or_name, sub_category)

    if result:
        interval, record = result.to_waveform(normalised=normalised, unit='cm/s/s')
        # noinspection PyTypeChecker
        return SequenceResponse(**result.dict(), interval=interval, data=record.tolist())

    raise HTTPException(HTTPStatus.NOT_FOUND, detail='Record not found')


@router.get('/spectrum/{file_id_or_name}', response_model=SequenceResponse)
async def download_single_spectrum(
        file_id_or_name: str,
        sub_category: str | None = Query(default=None, regex='^(knt|kik)$')
):
    """
    Retrieve raw accelerograph spectrum.
    The NIED collection has two sub-categories: `knt` and `kik`.
    This endpoint has a limit of 1 record per request since the file name is unique.
    In order to download more records, please use other endpoints.
    """
    result: NIED = await retrieve_single_record(file_id_or_name, sub_category)

    if result:
        frequency, record = result.to_spectrum()
        # noinspection PyTypeChecker
        return SequenceResponse(**result.dict(), interval=frequency, data=record.tolist())

    raise HTTPException(HTTPStatus.NOT_FOUND, detail='Record not found')


@router.get('/response_spectrum/{file_id_or_name}', response_model=ResponseSpectrumResponse)
async def download_single_response_spectrum(
        file_id_or_name: str,
        sub_category: str | None = Query(default=None, regex='^(knt|kik)$'),
        damping_ratio: float = Query(0.05, ge=0., le=1.),
        period_end: float = Query(20., ge=0.),
        period_step: float = Query(0.05, ge=0.),
        normalised: bool = Query(default=False)):
    """
    Retrieve a single response spectrum from the database according to the file ID or name.
    """
    result: NIED = await retrieve_single_record(file_id_or_name, sub_category)

    interval, record = result.to_waveform(normalised=normalised, unit='cm/s/s')
    period = np.arange(0, period_end + period_step, period_step)
    spectrum = response_spectrum(damping_ratio, interval, record, period)
    # noinspection PyTypeChecker
    return ResponseSpectrumResponse(**result.dict(), data=spectrum.tolist())
