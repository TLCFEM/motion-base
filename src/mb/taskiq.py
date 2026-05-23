#  Copyright (C) 2022-2026 Theodore Chang
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

from typing import Any

from elastic_transport import ConnectionTimeout
from pymongo import AsyncMongoClient
from pymongo.errors import ServerSelectionTimeoutError
from taskiq import (
    AsyncResultBackend,
    SimpleRetryMiddleware,
    TaskiqEvents,
    TaskiqResult,
    TaskiqState,
)
from taskiq_aio_pika import AioPikaBroker

from mb.utility.config import rabbitmq_uri


class MongoResultBackend(AsyncResultBackend[Any]):
    def __init__(self) -> None:
        self._client: AsyncMongoClient | None = None
        self._collection = None

    async def startup(self) -> None:
        from mb.utility.config import mongo_uri
        from mb.utility.env import MONGO_DB_NAME

        self._client = AsyncMongoClient(mongo_uri(), uuidRepresentation="standard")
        self._collection = self._client[MONGO_DB_NAME]["taskiq_results"]

    async def shutdown(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None

    async def set_result(self, task_id: str, result: TaskiqResult[Any]) -> None:
        await self._collection.replace_one(
            {"_id": task_id},
            {"_id": task_id, "data": result.model_dump_json()},
            upsert=True,
        )

    async def is_result_ready(self, task_id: str) -> bool:
        return await self._collection.count_documents({"_id": task_id}) > 0

    async def get_result(
        self,
        task_id: str,
        with_logs: bool = False,
    ) -> TaskiqResult[Any]:
        doc = await self._collection.find_one({"_id": task_id})
        if doc is None:
            raise ValueError(f"Result for task {task_id} is not ready.")
        return TaskiqResult.model_validate_json(doc["data"])


taskiq_broker = AioPikaBroker(rabbitmq_uri()).with_middlewares(
    SimpleRetryMiddleware(
        default_retry_count=3,
        default_retry_label=True,
        types_of_exceptions=(
            ConnectionError,
            TimeoutError,
            ConnectionTimeout,
            ServerSelectionTimeoutError,
        ),
    )
).with_result_backend(MongoResultBackend())

_broker_available: bool = False


def get_stats():
    return True if _broker_available else None


@taskiq_broker.on_event(TaskiqEvents.WORKER_STARTUP)
async def init_worker(state: TaskiqState):
    from mb.utility.config import init_mongo_for_worker

    state.mongo_client = await init_mongo_for_worker()


@taskiq_broker.on_event(TaskiqEvents.WORKER_SHUTDOWN)
async def shutdown_worker(state: TaskiqState):
    if hasattr(state, "mongo_client"):
        await state.mongo_client.close()
