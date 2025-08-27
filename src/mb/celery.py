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

import asyncio

from celery import Celery
from celery.signals import worker_process_init, worker_process_shutdown
from mongoengine import disconnect

from mb.utility.config import init_mongo, mongo_uri, rabbitmq_uri

celery = Celery(
    "mb",
    broker=rabbitmq_uri(),
    backend=mongo_uri(),
    include=["mb.app.jp", "mb.app.nz"],
)
celery.conf.broker_connection_retry_on_startup = True


def get_stats():
    return celery.control.inspect().stats()


@worker_process_init.connect
def init_mongo_in_celery_worker(**_):
    asyncio.run(init_mongo())


@worker_process_shutdown.connect
def shutdown_mongo_in_celery_worker(*args, **kwargs):
    disconnect()
