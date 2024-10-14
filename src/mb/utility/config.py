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
from mongoengine import connect, disconnect
from motor.motor_asyncio import AsyncIOMotorClient

from .env import (
    MONGO_DB_NAME,
    MONGO_HOST,
    MONGO_PORT,
    MONGO_USERNAME,
    MONGO_PASSWORD,
    RABBITMQ_HOST,
    RABBITMQ_PORT,
    RABBITMQ_USERNAME,
    RABBITMQ_PASSWORD,
)
from ..app.utility import User
from ..record.async_record import Record, UploadTask


def rabbitmq_uri():
    return f"amqp://{RABBITMQ_USERNAME}:{RABBITMQ_PASSWORD}@{RABBITMQ_HOST}:{RABBITMQ_PORT}/vhost"


def mongo_uri():
    return f"mongodb://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/"


async def init_mongo():
    uri = mongo_uri()
    mongo_client = connect(
        host=f"{uri}{MONGO_DB_NAME}?authSource=admin", uuidrepresentation="standard"
    )
    await init_beanie(
        database=AsyncIOMotorClient(uri, uuidRepresentation="standard")[MONGO_DB_NAME],
        document_models=[Record, User, UploadTask],
    )
    return mongo_client


async def shutdown_mongo():
    disconnect()
