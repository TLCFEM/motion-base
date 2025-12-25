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

from contextlib import asynccontextmanager

from beanie import init_beanie
from mongoengine import connect, disconnect
from pymongo import AsyncMongoClient

from ..app.utility import User
from ..record.async_record import Record, UploadTask
from .env import (
    MONGO_DB_NAME,
    MONGO_HOST,
    MONGO_PASSWORD,
    MONGO_PORT,
    MONGO_USERNAME,
    RABBITMQ_HOST,
    RABBITMQ_PASSWORD,
    RABBITMQ_PORT,
    RABBITMQ_USERNAME,
)


def rabbitmq_uri():
    return f"amqp://{RABBITMQ_USERNAME}:{RABBITMQ_PASSWORD}@{RABBITMQ_HOST}:{RABBITMQ_PORT}/vhost"


def mongo_uri():
    return f"mongodb://{MONGO_USERNAME}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/"


def _init_mongo_impl(uri: str, db: str | None):
    return connect(
        host=f"{uri}{db or MONGO_DB_NAME}?authSource=admin",
        uuidrepresentation="standard",
    )


def init_mongo_sync(db: str | None = None):
    return _init_mongo_impl(mongo_uri(), db)


@asynccontextmanager
async def init_mongo(db: str | None = None):
    await init_beanie(
        database=AsyncMongoClient(
            uri := mongo_uri(), uuidRepresentation="standard"
        ).get_database(db or MONGO_DB_NAME),
        document_models=[Record, User, UploadTask],
    )

    yield _init_mongo_impl(uri, db)

    disconnect()
