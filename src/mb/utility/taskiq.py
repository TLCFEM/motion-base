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

import asyncio

from aio_pika import connect_robust
from aio_pika.exceptions import CONNECTION_EXCEPTIONS
from aiormq.exceptions import ChannelNotFoundEntity
from pymongo import AsyncMongoClient
from pymongo.asynchronous.collection import AsyncCollection
from pymongo.asynchronous.database import AsyncDatabase
from taskiq.abc.result_backend import AsyncResultBackend
from taskiq.compat import model_dump, model_validate
from taskiq.result import TaskiqResult
from taskiq_aio_pika import AioPikaBroker

from mb.utility.config import (
    get_taskiq_collection,
    mongo_uri,
    rabbitmq_uri,
    taskiq_result,
)
from mb.utility.env import MONGO_DB_NAME


class MongoBackend(AsyncResultBackend):
    _client: AsyncMongoClient | None = None
    _collection: AsyncCollection | None = None
    _startup_lock = asyncio.Lock()

    async def startup(self):
        async with self._startup_lock:
            if self._collection is not None:
                return
            self._client = AsyncMongoClient(mongo_uri(), uuidRepresentation="standard")
            db: AsyncDatabase = self._client.get_database(MONGO_DB_NAME)
            if taskiq_result not in await db.list_collection_names():
                await db.create_collection(taskiq_result)
            self._collection = get_taskiq_collection(db)

    async def shutdown(self):
        if self._client is not None:
            await self._client.close()
        self._client = None
        self._collection = None

    async def set_result(self, task_id: str, result: TaskiqResult):
        await self.startup()
        header = {"task_id": task_id}
        await self._collection.update_one(
            header, {"$set": header | {"value": model_dump(result)}}, upsert=True
        )

    async def is_result_ready(self, task_id: str):
        await self.startup()
        target = await self._collection.find_one({"task_id": task_id})
        return target and "value" in target

    async def get_result(self, task_id: str, with_logs: bool = False):
        await self.startup()
        header = {"task_id": task_id}
        target = await self._collection.find_one(header)
        assert target

        result = model_validate(
            TaskiqResult,
            target["value"],
        )

        await self._collection.delete_one(header)

        return result


TASKIQ_DEFAULT_QUEUE_NAME = "taskiq"
TASKIQ_WORKER_CHECK_TIMEOUT = 2
taskiq_broker = None


def set_taskiq_broker():
    global taskiq_broker
    if taskiq_broker is None:
        taskiq_broker = AioPikaBroker(rabbitmq_uri()).with_result_backend(MongoBackend())
    return taskiq_broker


async def has_taskiq_worker() -> bool:
    try:
        connection = await connect_robust(
            rabbitmq_uri(), timeout=TASKIQ_WORKER_CHECK_TIMEOUT
        )
        async with connection:
            channel = await connection.channel()
            queue = await channel.declare_queue(TASKIQ_DEFAULT_QUEUE_NAME, passive=True)
            return bool(queue.declaration_result.consumer_count)
    except (ChannelNotFoundEntity, *CONNECTION_EXCEPTIONS, TimeoutError):
        return False
