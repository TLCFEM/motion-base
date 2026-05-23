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

from elastic_transport import ConnectionTimeout
from pymongo.errors import ServerSelectionTimeoutError
from taskiq import SimpleRetryMiddleware, TaskiqEvents, TaskiqState
from taskiq_aio_pika import AioPikaBroker

from mb.utility.config import rabbitmq_uri

broker = AioPikaBroker(rabbitmq_uri()).with_middlewares(
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
)

_broker_available: bool = False


def get_stats():
    return True if _broker_available else None


@broker.on_event(TaskiqEvents.WORKER_STARTUP)
async def init_worker(state: TaskiqState):
    from mb.utility.config import init_mongo_for_worker

    state.mongo_client = await init_mongo_for_worker()


@broker.on_event(TaskiqEvents.WORKER_SHUTDOWN)
async def shutdown_worker(state: TaskiqState):
    if hasattr(state, "mongo_client"):
        state.mongo_client.close()
