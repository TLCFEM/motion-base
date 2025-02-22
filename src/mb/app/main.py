#  Copyright (C) 2022-2025 Theodore Chang
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
from fastapi.responses import RedirectResponse, FileResponse, HTMLResponse
from pyinstrument import Profiler
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware

from .jp import router as jp_router
from .nz import router as nz_router
from .process import process_record_local
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
    TotalResponse,
    MetadataResponse,
    BulkRequest,
)
from .user import router as user_router
from .utility import (
    User,
    create_superuser,
    is_active,
)
from ..record.async_record import Record, MetadataRecord, UploadTask
from ..utility.config import init_mongo, shutdown_mongo
from ..utility.elastic import async_elastic
from ..utility.env import MB_FS_ROOT


@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):  # noqa # pylint: disable=unused-argument
    client = await async_elastic()
    await init_mongo()
    await create_superuser()
    yield
    await shutdown_mongo()
    await client.close()


async def profile_request(request, call_next):
    if not request.query_params.get("__profile__", False):
        return await call_next(request)

    with Profiler(async_mode="enabled") as profiler:
        await call_next(request)

    return HTMLResponse(profiler.output_html())


app = FastAPI(
    docs_url="/docs",
    title="Strong Motion Database",
    contact={"name": "Theodore Chang", "email": "tlcfem@gmail.com"},
    description="A database for strong motion records.",
    license_info={"name": "GNU General Public License v3.0"},
    lifespan=lifespan,
    middleware=[
        Middleware(GZipMiddleware, minimum_size=1024, compresslevel=8),
        Middleware(
            CORSMiddleware, allow_origins=["*"], allow_methods=["GET", "POST", "DELETE"]
        ),
        Middleware(BaseHTTPMiddleware, dispatch=profile_request),
    ],
)
app.include_router(jp_router, prefix="/jp")
app.include_router(nz_router, prefix="/nz")
app.include_router(user_router, prefix="/user")


@app.get("/", response_class=RedirectResponse)
async def redirect_to_docs():
    return "/docs"


@app.get("/alive", tags=["status"])
async def alive():
    return {"message": "I'm alive!"}


@app.post("/total", tags=["status"], response_model=TotalResponse)
async def post_total(
    query: QueryConfig | list[QueryConfig] = QueryConfig(min_magnitude=0),
):
    if isinstance(query, QueryConfig):
        query = [query]
    return {
        "total": [await Record.find(q.generate_query_string()).count() for q in query]
    }


@app.get("/total", tags=["status"], response_model=TotalResponse)
async def get_total():
    return {
        "total": [
            await Record.find(
                QueryConfig(min_magnitude=0).generate_query_string()
            ).count()
        ]
    }


@app.get(
    "/task/status/{task_id}",
    tags=["status"],
    status_code=HTTPStatus.OK,
    response_model=UploadTaskResponse,
)
async def get_task_status(task_id: UUID) -> UploadTaskResponse:
    if (task := await UploadTask.find_one(UploadTask.id == str(task_id))) is None:
        raise HTTPException(
            HTTPStatus.NOT_FOUND, detail="Task not found. It may have finished."
        )
    return UploadTaskResponse(**task.model_dump())


@app.post(
    "/task/status/",
    tags=["status"],
    status_code=HTTPStatus.OK,
    response_model=UploadTasksResponse,
)
async def post_task_status(task_ids: list[UUID]) -> UploadTasksResponse:
    tasks: list = [None] * len(task_ids)
    for i, task_id in enumerate(task_ids):
        if (
            task := await UploadTask.find_one(UploadTask.id == str(task_id))
        ) is not None:
            tasks[i] = task.model_dump()

    return UploadTasksResponse(tasks=tasks)


@app.get("/test_endpoint", tags=["misc"])
async def for_test_only():
    return {"message": "Test endpoint."}


async def get_random_record() -> Record:
    result: list[Record] = await Record.aggregate(
        [{"$sample": {"size": 1}}], projection_model=Record
    ).to_list()
    if result:
        return result[0]

    raise HTTPException(HTTPStatus.NO_CONTENT, detail="Record not found.")


@app.get("/raw/jackpot", response_model=RawRecordResponse)
async def download_single_random_raw_record():
    """
    Retrieve a single random record from the database.
    """
    result: Record = await get_random_record()
    return RawRecordResponse(
        **result.model_dump(exclude_none=True), endpoint="/raw/jackpot"
    )


@app.get("/waveform/jackpot", response_model=RecordResponse)
async def download_single_random_waveform(normalised: bool = False):
    """
    Retrieve a single random waveform from the database.
    """
    result: Record = await get_random_record()

    interval, record = result.to_waveform(normalised=normalised, unit="cm/s/s")
    # noinspection PyTypeChecker
    return RecordResponse(
        **result.model_dump(exclude_none=True),
        endpoint="/waveform/jackpot",
        time_interval=interval,
        waveform=record.tolist(),
        processed_data_unit="cm/s/s",
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
        **result.model_dump(exclude_none=True),
        endpoint="/spectrum/jackpot",
        frequency_interval=frequency,
        spectrum=record.tolist(),
    )


@app.post("/waveform", response_model=ListRecordResponse)
async def download_waveform(record_id: UUID | list[UUID]):
    """
    Retrieve waveform from the database by given IDs.
    """

    results: list[Record] = await Record.find(
        In(
            Record.id,
            [str(x) for x in record_id]
            if isinstance(record_id, list)
            else [str(record_id)],
        )
    ).to_list()

    def _populate_waveform(result: Record):
        interval, record = result.to_waveform(unit="cm/s/s")
        return RecordResponse(
            **result.model_dump(exclude_none=True),
            endpoint="/waveform",
            time_interval=interval,
            waveform=record.tolist(),
            processed_data_unit="cm/s/s",
        )

    return ListRecordResponse(
        records=[_populate_waveform(result) for result in results]
    )


@app.post("/query", response_model=ListMetadataResponse)
async def query_records(query: QueryConfig = QueryConfig(), count_total: bool = False):
    """
    Query records from the database.

    Since the query involves computing the distance between two points, it is slow to count the total number of records.
    If you do not need the total number of records, set `count_total` to `false`.
    If you need the total number of records, set `count_total` to `true`.
    If `count_total` is set to `true`, the total number of records will be returned.
    The computation depends on whether the query asks to filter by location.
    """
    pagination = query.pagination

    filtered = Record.find(query.generate_query_string()).sort(pagination.sort_by)
    record_count: int = 0 if not count_total else await filtered.count()

    skip_size: int = pagination.page_number * pagination.page_size
    result = (
        filtered.skip(skip_size).limit(pagination.page_size).project(MetadataRecord)
    )

    response: ListMetadataResponse = ListMetadataResponse(
        records=[
            MetadataResponse(**(x.model_dump(exclude_none=True)))
            for x in await result.to_list()
        ],
        pagination=PaginationResponse(total=record_count, **pagination.model_dump()),
    )
    for item in response.records:
        item.endpoint = "/query"
    return response


@app.post("/search", response_model=ListMetadataResponse)
async def search_records(query: QueryConfig = QueryConfig()):
    """
    Query records from the database using elastic search.
    """
    pagination = query.pagination

    page_size: int = pagination.page_size
    page_number: int = min(pagination.page_number, 10000 // page_size - 1)

    client = await async_elastic()
    results = await client.search(
        index="record",
        query=query.generate_elastic_query(),
        from_=page_number * page_size,
        size=page_size,
    )

    return ListMetadataResponse(
        records=[
            MetadataResponse(endpoint="/search", **x["_source"])
            for x in results["hits"]["hits"]
        ],
        pagination=PaginationResponse(
            total=results["hits"]["total"]["value"],
            sort_by=pagination.sort_by,
            page_size=page_size,
            page_number=page_number,
        ),
    )


@app.get("/stats")
async def aggregation_stats():
    client = await async_elastic()
    results = await client.search(
        index="record",
        query={"range": {"magnitude": {"gte": 1, "lte": 10}}},
        aggs={
            "magnitude": {"histogram": {"field": "magnitude", "interval": 1}},
            "pga": {"histogram": {"field": "maximum_acceleration", "interval": 10}},
        },
        size=0,
    )

    return results["aggregations"]


@app.post("/index")
async def index_records(body: BulkRequest = Body(...), user: User = Depends(is_active)):
    """
    Index records.
    """
    if not user.can_upload:
        raise HTTPException(
            HTTPStatus.UNAUTHORIZED, detail="User is not allowed to upload files."
        )

    client = await async_elastic()

    return await client.bulk(index="record", body=body.records)


@app.post("/process", response_model=ProcessedResponse)
async def process_record(record_id: UUID, process_config: ProcessConfig = Body(...)):
    if result := await Record.find_one(Record.id == str(record_id)):
        return process_record_local(result, process_config)

    raise HTTPException(HTTPStatus.NOT_FOUND, detail="Record not found.")


@app.get("/access/{file_path:path}", tags=["misc"], response_class=FileResponse)
async def download_file(file_path: str):
    if not MB_FS_ROOT:
        raise HTTPException(
            HTTPStatus.NOT_FOUND, detail="File system is not available."
        )

    local_path = os.path.join(MB_FS_ROOT, file_path)
    if not os.path.exists(local_path):
        raise HTTPException(HTTPStatus.NOT_FOUND, detail="File not found.")

    return FileResponse(local_path)


@app.delete("/access/{file_path:path}", tags=["misc"])
async def delete_file(file_path: str, user: User = Depends(is_active)):
    if not user.can_delete:
        raise HTTPException(
            HTTPStatus.UNAUTHORIZED, detail="User is not allowed to delete files."
        )

    if not MB_FS_ROOT:
        raise HTTPException(
            HTTPStatus.NOT_FOUND, detail="File system is not available."
        )

    local_path = os.path.join(MB_FS_ROOT, file_path)
    if not os.path.exists(local_path):
        raise HTTPException(HTTPStatus.NOT_FOUND, detail="File not found.")

    try:
        os.remove(local_path)
        if not os.listdir(parent := os.path.dirname(local_path)):
            os.rmdir(parent)
    except OSError:
        raise HTTPException(
            HTTPStatus.INTERNAL_SERVER_ERROR, detail="Failed to delete file."
        )

    return {"message": "File deleted."}
