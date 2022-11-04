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
from datetime import datetime, timedelta
from http import HTTPStatus
from uuid import UUID

from fastapi import BackgroundTasks, Body, Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm

from mb.app.jp import router as jp_router
from mb.app.nz import router as nz_router
from mb.app.response import ListSequenceResponse, MetadataListResponse, MetadataResponse
from mb.app.universal import query_database, retrieve_record
from mb.app.utility import ACCESS_TOKEN_EXPIRE_MINUTES, QueryConfig, Token, UploadTask, User, UserInformation, \
    authenticate_user, \
    create_superuser, create_task, create_token, is_active
from mb.utility.config import init_mongo

app = FastAPI(
    docs_url='/docs',
    title='Strong Motion Database',
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


@app.post('/waveform', response_model=ListSequenceResponse)
async def download_multiple_waveform(
        record_ids: list[UUID],
        normalised: bool = Query(default=False)
):
    """
    Retrieve raw accelerograph waveform.
    """
    tasks = [retrieve_record(record_id, normalised) for record_id in record_ids]
    results = await asyncio.gather(*tasks)

    # noinspection PyTypeChecker
    return ListSequenceResponse(records=[result for result in results if result is not None])


@app.post('/query', response_model=MetadataListResponse)
async def query_records(
        query: QueryConfig | None = Body(default=None),
        min_magnitude: float | None = Query(default=None, ge=0, le=10),
        max_magnitude: float | None = Query(default=None, ge=0, le=10),
        sub_category: str | None = Query(default=None),
        event_location: list[float, float] | None = Query(default=None, min_items=2, max_items=2),
        station_location: list[float, float] | None = Query(default=None, min_items=2, max_items=2),
        max_event_distance: float | None = Query(
            default=None, ge=0, description='maximum distance from the given location in km'),
        max_station_distance: float | None = Query(
            default=None, ge=0, description='maximum distance from the given location in km'),
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
    if query is None:
        query = QueryConfig()

    if min_magnitude is not None:
        query.min_magnitude = min_magnitude
    if max_magnitude is not None:
        query.max_magnitude = max_magnitude
    if sub_category is not None:
        query.sub_category = sub_category
    if event_location is not None:
        query.event_location = event_location
    if station_location is not None:
        query.station_location = station_location
    if max_event_distance is not None:
        query.max_event_distance = max_event_distance
    if max_station_distance is not None:
        query.max_station_distance = max_station_distance
    if from_date is not None:
        query.from_date = from_date
    if to_date is not None:
        query.to_date = to_date
    if min_pga is not None:
        query.min_pga = min_pga
    if max_pga is not None:
        query.max_pga = max_pga
    if event_name is not None:
        query.event_name = event_name
    if direction is not None:
        query.direction = direction
    if page_size is not None:
        query.page_size = page_size
    if page_number is not None:
        query.page_number = page_number

    result, counter = await query_database(query.generate_query_string(), query.page_size, query.page_number)
    if result:
        return MetadataListResponse(
            query=query.dict(), total=counter,
            result=[MetadataResponse(**r.dict(), endpoint='/query') for record in result async for r in record])

    raise HTTPException(HTTPStatus.NO_CONTENT, detail='No records found')
