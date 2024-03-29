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

import os.path
from contextlib import asynccontextmanager
from http import HTTPStatus
from uuid import UUID

from beanie.operators import In
from fastapi import Body, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import RedirectResponse, FileResponse

from ..celery import get_stats
from ..utility.env import MB_CELERY, MB_FS_ROOT

if MB_CELERY:
    from .jp_sync import router as jp_router
    from .nz_sync import router as nz_router
else:
    from .jp_async import router as jp_router
    from .nz_async import router as nz_router


from .user import router as user_router

from .process import process_record_local, process_record_via_celery
from .response import (
    ProcessConfig,
    ListMetadataResponse,
    QueryConfig,
    ProcessedResponse,
    RecordResponse,
    RawRecordResponse,
    PaginationResponse,
    UploadTasksResponse,
    UploadTaskResponse,
    ListRecordResponse,
)
from .utility import (
    User,
    create_superuser,
    is_active,
)
from ..record.async_record import Record, MetadataRecord, UploadTask
from ..utility.config import init_mongo, shutdown_mongo


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):  # noqa # pylint: disable=unused-argument
    await init_mongo()
    await create_superuser()
    yield
    await shutdown_mongo()


app = FastAPI(
    docs_url="/docs",
    title="Strong Motion Database",
    contact={"name": "Theodore Chang", "email": "tlcfem@gmail.com"},
    description="A database for strong motion records.",
    license_info={"name": "GNU General Public License v3.0"},
    lifespan=lifespan,
)
app.include_router(jp_router, prefix="/jp")
app.include_router(nz_router, prefix="/nz")
app.include_router(user_router, prefix="/user")
app.add_middleware(GZipMiddleware, minimum_size=1024)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "DELETE"],
)


@app.get("/", response_class=RedirectResponse)
async def redirect_to_docs():
    return "/docs"


@app.get("/alive", tags=["status"])
async def alive():
    return {"message": "I'm alive!"}


@app.get("/total", tags=["status"])
async def total():
    return {"total": await Record.find(Record.magnitude > 0).count()}


@app.get("/task/status/{task_id}", tags=["status"], status_code=HTTPStatus.OK, response_model=UploadTaskResponse)
async def get_task_status(task_id: UUID) -> UploadTaskResponse:
    if (task := await UploadTask.find_one(UploadTask.id == str(task_id))) is None:
        raise HTTPException(HTTPStatus.NOT_FOUND, detail="Task not found. It may have finished.")
    return UploadTaskResponse(**task.dict())


@app.post("/task/status/", tags=["status"], status_code=HTTPStatus.OK, response_model=UploadTasksResponse)
async def post_task_status(task_ids: list[UUID]) -> UploadTasksResponse:
    tasks: list = [None] * len(task_ids)
    for i, task_id in enumerate(task_ids):
        if (task := await UploadTask.find_one(UploadTask.id == str(task_id))) is not None:
            tasks[i] = task.dict()

    return UploadTasksResponse(tasks=tasks)


@app.get("/test_endpoint", tags=["misc"])
async def for_test_only():
    return {"message": "Test endpoint."}


async def get_random_record() -> Record:
    result: list[Record] = await Record.aggregate([{"$sample": {"size": 1}}], projection_model=Record).to_list()
    if result:
        return result[0]

    raise HTTPException(HTTPStatus.NO_CONTENT, detail="Record not found.")


@app.get("/raw/jackpot", response_model=RawRecordResponse)
async def download_single_random_raw_record():
    """
    Retrieve a single random record from the database.
    """
    result: Record = await get_random_record()
    return RawRecordResponse(**result.dict(), endpoint="/raw/jackpot")


@app.get("/waveform/jackpot", response_model=RecordResponse)
async def download_single_random_waveform(normalised: bool = False):
    """
    Retrieve a single random waveform from the database.
    """
    result: Record = await get_random_record()

    interval, record = result.to_waveform(normalised=normalised, unit="cm/s/s")
    # noinspection PyTypeChecker
    return RecordResponse(
        **result.dict(), endpoint="/waveform/jackpot", time_interval=interval, waveform=record.tolist()
    )


@app.get("/spectrum/jackpot", response_model=RecordResponse)
async def download_single_random_spectrum():
    """
    Retrieve a single random spectrum from the database.
    """
    result: Record = await get_random_record()

    frequency, record = result.to_spectrum()
    # noinspection PyTypeChecker
    return RecordResponse(
        **result.dict(), endpoint="/spectrum/jackpot", frequency_interval=frequency, spectrum=record.tolist()
    )


@app.post("/waveform", response_model=ListRecordResponse)
async def download_waveform(record_id: UUID | list[UUID]):
    """
    Retrieve waveform from the database by given IDs.
    """

    results: list[Record] = await Record.find(
        In(Record.id, [str(x) for x in record_id] if isinstance(record_id, list) else [str(record_id)])
    ).to_list()

    def _populate_waveform(result: Record):
        interval, record = result.to_waveform(unit="cm/s/s")
        return RecordResponse(**result.dict(), endpoint="/waveform", time_interval=interval, waveform=record.tolist())

    return ListRecordResponse(records=[_populate_waveform(result) for result in results])


@app.post("/query", response_model=ListMetadataResponse)
async def query_records(query: QueryConfig = Body(...), count_total: bool = False):
    """
    Query records from the database.

    Since the query involves computing the distance between two points, it is slow to count the total number of records.
    If you do not need the total number of records, set `count_total` to `false`.
    If you need the total number of records, set `count_total` to `true`.
    If `count_total` is set to `true`, the total number of records will be returned.
    The computation depends on whether the query asks to filter by location.
    """

    geo, other = query.generate_query_string()

    filtered = Record.find({**geo, **other})
    result = filtered.skip(query.page_number * query.page_size).limit(query.page_size).project(MetadataRecord)

    if not count_total:
        record_count: int = 0
    elif not geo:
        record_count = await filtered.count()
    else:
        key: str = "event_location" if "event_location" in geo else "station_location"

        aggregation: dict = {
            "$geoNear": {
                "near": geo[key]["$nearSphere"],
                "key": key,
                "distanceField": "dist.calculated",
                "maxDistance": geo[key]["$maxDistance"],
                "spherical": True,
            }
        }
        if other:
            aggregation["$geoNear"]["query"] = other
        record_count = (await Record.aggregate([aggregation, {"$count": "total"}]).to_list())[0]["total"]

    response: ListMetadataResponse = ListMetadataResponse(
        records=await result.to_list(),
        pagination=PaginationResponse(total=record_count, page_size=query.page_size, page_number=query.page_number),
    )
    for item in response.records:
        item.endpoint = "/query"
    return response


@app.post("/process", response_model=ProcessedResponse)
async def process_record(record_id: UUID, process_config: ProcessConfig = Body(...)):
    if result := await Record.find_one(Record.id == str(record_id)):
        light_work: bool = not process_config.with_filter and not process_config.with_response_spectrum
        if (stats := get_stats()) is None or len(stats) == 1 or light_work:
            # consider only calculating frequency spectrum is not so expensive and can be done locally
            # assuming the only worker is deployed on the same machine so that do not pay the cost of serialization
            return process_record_local(result, process_config)

        # if filtering, or response spectra, is required, offload the task to workers
        return process_record_via_celery.delay(
            result.dict(exclude_none=True, exclude_unset=True, exclude_defaults=True),
            process_config.dict(exclude_none=True, exclude_unset=True, exclude_defaults=True),
        ).get()

    raise HTTPException(HTTPStatus.NOT_FOUND, detail="Record not found.")


@app.get("/access/{file_path:path}", tags=["misc"], response_class=FileResponse)
async def download_file(file_path: str):
    if not MB_FS_ROOT:
        raise HTTPException(HTTPStatus.NOT_FOUND, detail="File system is not available.")

    local_path = os.path.join(MB_FS_ROOT, file_path)
    if not os.path.exists(local_path):
        raise HTTPException(HTTPStatus.NOT_FOUND, detail="File not found.")

    return FileResponse(local_path)


@app.delete("/access/{file_path:path}", tags=["misc"])
async def delete_file(file_path: str, user: User = Depends(is_active)):
    if not user.can_delete:
        raise HTTPException(HTTPStatus.UNAUTHORIZED, detail="User is not allowed to delete files.")

    if not MB_FS_ROOT:
        raise HTTPException(HTTPStatus.NOT_FOUND, detail="File system is not available.")

    local_path = os.path.join(MB_FS_ROOT, file_path)
    if not os.path.exists(local_path):
        raise HTTPException(HTTPStatus.NOT_FOUND, detail="File not found.")

    try:
        os.remove(local_path)
        if not os.listdir(parent := os.path.dirname(local_path)):
            os.rmdir(parent)
    except OSError:
        raise HTTPException(HTTPStatus.INTERNAL_SERVER_ERROR, detail="Failed to delete file.")

    return {"message": "File deleted."}
