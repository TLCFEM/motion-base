#  Copyright (C) 2022 Theodore Chang
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

from beanie import init_beanie
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

from mb.app.utility import UploadTask, User
from mb.record.jp import NIED
from mb.record.nz import NZSM


def mongo_uri():
    if not load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')):
        raise RuntimeError('No .env file found')
    username: str = os.getenv('MONGO_USERNAME')
    password: str = os.getenv('MONGO_PASSWORD')
    host: str = os.getenv('MONGO_HOST')
    port: str = os.getenv('MONGO_PORT')
    return f'mongodb://{username}:{password}@{host}:{port}/'


async def init_mongo():
    client = AsyncIOMotorClient(mongo_uri())
    await init_beanie(database=client['StrongMotion'], document_models=[NIED, NZSM, User, UploadTask])
