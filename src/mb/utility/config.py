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

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from .env import (
    MONGO_HOST,
    MONGO_PASSWORD,
    MONGO_PORT,
    MONGO_USERNAME,
    RABBITMQ_HOST,
    RABBITMQ_PASSWORD,
    RABBITMQ_USERNAME,
)
from ..app.utility import UploadTask, User
from ..record.record import Record


def rabbitmq_uri():
    if RABBITMQ_USERNAME is None or RABBITMQ_PASSWORD is None or RABBITMQ_HOST is None:
        raise RuntimeError("Missing rabbitmq related environment variables.")

    return f"amqp://{RABBITMQ_USERNAME}:{RABBITMQ_PASSWORD}@{RABBITMQ_HOST}:5672/vhost"


def mongo_uri():
    if MONGO_USERNAME is None or MONGO_PASSWORD is None or MONGO_HOST is None or MONGO_PORT is None:
        raise RuntimeError("Missing mongo related environment variables.")

    return f"mongodb://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/"


async def init_mongo():
    await init_beanie(
        database=AsyncIOMotorClient(mongo_uri())["StrongMotion"], document_models=[Record, User, UploadTask]
    )
