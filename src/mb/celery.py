#  Copyright (C) 2022-2024 Theodore Chang
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

import os

from celery import Celery
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "../../docker/.env"))


def rabbitmq_uri():
    username: str = os.getenv("RABBITMQ_USERNAME")
    password: str = os.getenv("RABBITMQ_PASSWORD")
    host: str = os.getenv("RABBITMQ_HOST")
    if username is None or password is None or host is None:
        raise RuntimeError("Missing rabbitmq related environment variables.")

    return f"amqp://{username}:{password}@{host}:5672/vhost"


celery = Celery(
    "mb",
    broker=rabbitmq_uri(),
    include=["mb.app.jp", "mb.app.nz"],
)
celery.conf.broker_connection_retry_on_startup = True
