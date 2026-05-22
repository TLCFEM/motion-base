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

from pymongo.asynchronous.database import AsyncDatabase
from taskiq.abc.result_backend import AsyncResultBackend
from taskiq.compat import model_dump, model_validate
from taskiq.result import TaskiqResult
from taskiq_aio_pika import AioPikaBroker

from mb.utility.config import get_taskiq_collection, rabbitmq_uri


class MongoBackend(AsyncResultBackend):
    def __init__(self, db: AsyncDatabase):
        self._collection = get_taskiq_collection(db)

    async def set_result(self, task_id: str, result: TaskiqResult):
        header = {"task_id": task_id}
        await self._collection.update_one(
            header, {"$set": header | {"value": model_dump(result)}}, True
        )

    async def is_result_ready(self, task_id: str):
        target = await self._collection.find_one({"task_id": task_id})
        return target and "value" in target

    async def get_result(self, task_id: str, with_logs: bool = False):
        target = await self._collection.find_one(header := {"task_id": task_id})
        assert target

        result = model_validate(
            TaskiqResult,
            target["value"],
        )

        await self._collection.delete_one(header)

        return result


taskiq_broker = None


def set_taskiq_broker(db: AsyncDatabase):
    global taskiq_broker
    if not taskiq_broker:
        taskiq_broker = AioPikaBroker(rabbitmq_uri(), MongoBackend(db))
    return taskiq_broker
