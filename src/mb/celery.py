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

from asyncio import new_event_loop

from celery import Celery
from celery.signals import worker_process_init, worker_process_shutdown

from mb.utility.config import (
    mongo_uri,
    rabbitmq_uri,
    shutdown,
    startup,
)

celery = Celery(
    "mb",
    broker=rabbitmq_uri(),
    backend=mongo_uri(),
    include=["mb.app.jp", "mb.app.nz"],
)
celery.conf.broker_connection_retry_on_startup = True


global_event_loop = new_event_loop()


def get_stats():
    return celery.control.inspect().stats()


@worker_process_init.connect
def init_mongo_in_celery_worker(**_):
    global_event_loop.run_until_complete(startup())


@worker_process_shutdown.connect
def shutdown_mongo_in_celery_worker(*_, **__):
    global_event_loop.run_until_complete(shutdown())
