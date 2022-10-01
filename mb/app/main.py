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

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from starlette.responses import RedirectResponse

from mb.app.jp import router as jp_router
from mb.app.nz import router as nz_router
from mb.app.utility import ACCESS_TOKEN_EXPIRE_MINUTES, Token, UploadTask, User, UserInformation, authenticate_user, \
    create_superuser, create_task, create_token, is_active
from mb.utility.config import init_mongo

app = FastAPI(docs_url='/docs', title='Strong Motion Database')
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
