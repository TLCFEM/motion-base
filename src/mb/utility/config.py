#  Copyright (C) 2022-2023 Theodore Chang
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

import structlog
from beanie import init_beanie
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

from ..app.utility import UploadTask, User
from ..record.record import Record

_logger = structlog.get_logger(__name__)


def mongo_uri():
    if load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")):
        _logger.info("Using .env file.")
    else:
        _logger.info("No .env file found.")

    username: str = os.getenv("MONGO_USERNAME")
    password: str = os.getenv("MONGO_PASSWORD")
    host: str = os.getenv("MONGO_HOST")
    port: str = os.getenv("MONGO_PORT")
    if username is None or password is None or host is None or port is None:
        raise RuntimeError("Missing mongo related environment variables.")

    return f"mongodb://{username}:{password}@{host}:{port}/"


async def init_mongo():
    await init_beanie(
        database=AsyncIOMotorClient(mongo_uri())["StrongMotion"], document_models=[Record, User, UploadTask]
    )
