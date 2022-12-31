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

import asyncio
from datetime import timedelta
from http import HTTPStatus
from uuid import UUID

from fastapi import BackgroundTasks, Body, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm

from mb.app.jp import router as jp_router
from mb.app.nz import router as nz_router
from mb.app.process import processing_record
from mb.app.response import ProcessConfig, ListMetadataResponse, QueryConfig, ProcessedResponse, RecordResponse
from mb.app.universal import query_database, retrieve_record
from mb.app.utility import ACCESS_TOKEN_EXPIRE_MINUTES, Token, UploadTask, User, UserInformation, authenticate_user, \
    create_superuser, create_task, create_token, is_active
from mb.record.record import Record
from mb.utility.config import init_mongo

app = FastAPI(
    docs_url='/docs', title='Strong Motion Database',
    contact={'name': 'Theodore Chang', 'email': 'tlcfem@gmail.com'},
    description='A database for strong motion records.',
    license_info={'name': 'GNU General Public License v3.0'}
)
app.include_router(jp_router, prefix='/jp')
app.include_router(nz_router, prefix='/nz')
app.add_middleware(GZipMiddleware, minimum_size=1024)
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.on_event('startup')
async def init():
    await init_mongo()
    await create_superuser()


@app.get('/', response_class=RedirectResponse)
async def redirect_to_docs():
    return '/docs'


@app.get('/alive', tags=['status'])
async def alive():
    return {'message': 'I\'m alive!'}


@app.get('/task/status/{task_id}', tags=['status'], status_code=HTTPStatus.OK, response_model=UploadTask)
async def get_task_status(task_id: UUID) -> UploadTask:
    task = await UploadTask.find_one(UploadTask.id == task_id)
    if task is None:
        raise HTTPException(HTTPStatus.NOT_FOUND, detail='Task not found. It may have finished.')
    return task


@app.post('/token', tags=['account'], response_model=Token)
async def acquire_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            HTTPStatus.UNAUTHORIZED,
            detail='Incorrect username or password',
            headers={'WWW-Authenticate': 'Bearer'},
        )
    access_token = create_token(
        data={'sub': user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {'access_token': access_token, 'token_type': 'bearer'}


@app.get('/whoami', tags=['account'], response_model=UserInformation)
async def retrieve_myself(user: User = Depends(is_active)):
    return UserInformation(**user.dict())


async def async_task(task_id: UUID):
    await asyncio.sleep(10)
    task = await UploadTask.find_one(UploadTask.id == task_id)
    if task:
        await task.delete()


@app.get('/ten_second_delay', tags=['misc'])
async def for_test_only(tasks: BackgroundTasks):
    task_id = await create_task()
    tasks.add_task(async_task, task_id)
    return {'task_id': task_id}


async def get_random_record() -> Record:
    result: list[Record] = await Record.aggregate([{'$sample': {'size': 1}}], projection_model=Record).to_list()
    if result:
        return result[0]

    raise HTTPException(HTTPStatus.NO_CONTENT, detail='Record not found')


@app.get('/raw/jackpot', response_model=Record)
async def download_single_random_raw_record():
    """
    Retrieve a single random record from the database.
    """
    return await get_random_record()


@app.get('/waveform/jackpot', response_model=RecordResponse)
async def download_single_random_waveform(normalised: bool = False):
    """
    Retrieve a single random waveform from the database.
    """
    result: Record = await get_random_record()

    interval, record = result.to_waveform(normalised=normalised, unit='cm/s/s')
    # noinspection PyTypeChecker
    return RecordResponse(
        **result.dict(),
        endpoint='/waveform/jackpot',
        time_interval=interval,
        waveform=record.tolist())


@app.get('/spectrum/jackpot', response_model=RecordResponse)
async def download_single_random_spectrum():
    """
    Retrieve a single random spectrum from the database.
    """
    result: Record = await get_random_record()

    frequency, record = result.to_spectrum()
    # noinspection PyTypeChecker
    return RecordResponse(
        **result.dict(),
        endpoint='/spectrum/jackpot',
        frequency_interval=frequency,
        spectrum=record.tolist())


@app.post('/query', response_model=ListMetadataResponse)
async def query_records(query_config: QueryConfig = Body(...)):
    """
    Query records from the database.
    """
    result = await query_database(query_config)

    if not result:
        raise HTTPException(HTTPStatus.NO_CONTENT, detail='No records found.')

    return ListMetadataResponse(records=result)


@app.post('/process', response_model=ProcessedResponse)
async def process_record(record_id: UUID, process_config: ProcessConfig = Body(...)):
    result = await retrieve_record(record_id)

    if not result:
        raise HTTPException(HTTPStatus.NOT_FOUND, detail='Record not found.')

    return processing_record(result, process_config)
