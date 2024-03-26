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

import os.path

import pytest
from httpx import AsyncClient

from mb.app.main import app
from mb.app.utility import User, is_active, crypt_context
from mb.utility.config import init_mongo


# @pytest.fixture(scope="session")
# def celery_config():
#     return {"broker_url": "amqp://", "result_backend": "mongodb://"}


@pytest.fixture(scope="function", autouse=True)
async def mongo_connection():
    await init_mongo()


@pytest.fixture(scope="function", autouse=True)
async def mock_client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


async def always_active():
    return User(
        username="test",
        email="test",
        last_name="test",
        first_name="test",
        hashed_password=crypt_context.hash("test"),
        disabled=False,
        can_upload=True,
        can_delete=True,
    )


@pytest.fixture(scope="function", autouse=True)
async def mock_client_superuser():
    app.dependency_overrides[is_active] = always_active
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides = {}


@pytest.fixture(scope="function", autouse=True)
async def mock_header():
    return {"WWW-Authenticate": "Bearer"}


@pytest.fixture(scope="function", autouse=True)
def pwd():
    return os.path.dirname(os.path.abspath(__file__))
