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

import dataclasses
import os

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from mb.app.utility import User
from mb.record.jp import NIED
from mb.record.nz import NZSM


@dataclasses.dataclass
class MotionBaseConfig:
    username: str = os.getenv('MONGO_USERNAME')
    password: str = os.getenv('MONGO_PASSWORD')
    host: str = 'localhost'
    port: int = 27017
    mongo_uri: str = f'mongodb://{username}:{password}@{host}:{port}/'


async def init_mongo():
    client = AsyncIOMotorClient(MotionBaseConfig.mongo_uri)
    await init_beanie(database=client['StrongMotion'], document_models=[NIED, NZSM, User])
