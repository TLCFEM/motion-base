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

from celery import Celery

from mb.utility.config import mongo_uri, rabbitmq_uri

celery = Celery(
    "mb",
    broker=rabbitmq_uri(),
    backend=mongo_uri(),
    include=["mb.app.jp", "mb.app.nz"],
)
celery.conf.broker_connection_retry_on_startup = True


def get_stats():
    return celery.control.inspect().stats()
