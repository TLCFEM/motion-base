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

from elastic_transport import ConnectionTimeout
from pymongo import AsyncMongoClient
from pymongo.errors import ServerSelectionTimeoutError
from taskiq import TaskiqEvents
from taskiq.middlewares import SmartRetryMiddleware
from taskiq_aio_pika import AioPikaBroker, Queue
from taskiq_mongodb import MongoResultBackend

from mb.utility.config import mb_init_beanie, mongo_uri, rabbitmq_uri
from mb.utility.env import MONGO_DB_NAME

QUEUE_NAME = "taskiq"

broker = (
    AioPikaBroker(
        rabbitmq_uri(),
        delay_queue=Queue(name="taskiq.delay"),
    )
    .with_result_backend(
        MongoResultBackend(
            mongo_uri(),
            MONGO_DB_NAME,
            collection_name="taskiq_results",
        )
    )
    .with_middlewares(
        SmartRetryMiddleware(
            # Taskiq counts total attempts, so four attempts equal three retries.
            default_retry_count=4,
            default_delay=10,
            types_of_exceptions=(
                ConnectionError,
                TimeoutError,
                ConnectionTimeout,
                ServerSelectionTimeoutError,
            ),
        )
    )
)


mongo_client: AsyncMongoClient | None = None


async def startup(db: str | None = None):
    global mongo_client
    if mongo_client is None:
        mongo_client = AsyncMongoClient(mongo_uri(), uuidRepresentation="standard")
        await mb_init_beanie(mongo_client, db)


async def shutdown():
    global mongo_client
    if mongo_client is not None:
        await mongo_client.close()
        mongo_client = None


@broker.on_event(TaskiqEvents.WORKER_STARTUP)
async def init_mongo_in_taskiq_worker(**_):
    await startup()


@broker.on_event(TaskiqEvents.WORKER_SHUTDOWN)
async def shutdown_mongo_in_taskiq_worker(*_, **__):
    await shutdown()


async def has_workers() -> bool:
    if broker.write_channel is None:
        return False

    try:
        # Ask the broker directly. AioPikaBroker caches declared queues, so a
        # normal passive declare would return the stale consumer count from
        # startup instead of the current one.
        channel = await broker.write_channel.get_underlay_channel()
        declaration = await channel.queue_declare(QUEUE_NAME, passive=True)
    except Exception:
        return False

    return declaration is not None and (declaration.consumer_count or 0) > 0
