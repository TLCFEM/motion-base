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

from asyncio import AbstractEventLoop, new_event_loop, set_event_loop

from celery import Celery
from celery.signals import worker_process_init, worker_process_shutdown
from pymongo import AsyncMongoClient

from mb.utility.config import mb_init_beanie, mongo_uri, rabbitmq_uri

celery = Celery(
    "mb",
    broker=rabbitmq_uri(),
    backend=mongo_uri(),
    include=["mb.app.jp", "mb.app.nz"],
)
celery.conf.broker_connection_retry_on_startup = True


global_loop: AbstractEventLoop = None  # noqa
mongo_client: AsyncMongoClient = None  # noqa


def get_stats():
    return celery.control.inspect().stats()


async def startup(db: str | None = None):
    global mongo_client
    if mongo_client is None:
        mongo_client = AsyncMongoClient(mongo_uri(), uuidRepresentation="standard")
        await mb_init_beanie(mongo_client, db)


async def shutdown():
    if mongo_client is not None:
        await mongo_client.close()


def _ensure_loop():
    global global_loop
    if global_loop is None:
        global_loop = new_event_loop()
        set_event_loop(global_loop)
    return global_loop


@worker_process_init.connect
def init_mongo_in_celery_worker(**_):
    _ensure_loop().run_until_complete(startup())


@worker_process_shutdown.connect
def shutdown_mongo_in_celery_worker(*_, **__):
    loop = _ensure_loop()
    loop.run_until_complete(shutdown())
    loop.close()


def execute_task(task):
    _ensure_loop().run_until_complete(task)
