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

import asyncio
import os.path
from time import sleep
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from mb.app.main import app
from mb.app.utility import User, bcrypt_hash, is_active
from mb.utility import env
from mb.utility.config import init_mongo, mongo_uri, rabbitmq_uri


@pytest.fixture(scope="session", autouse=True)
def celery_config():
    return {"broker_url": rabbitmq_uri(), "result_backend": mongo_uri()}


@pytest.fixture(scope="function", autouse=True)
def mock_celery(celery_session_app, celery_session_worker):
    while True:
        if celery_session_app.control.inspect().stats():
            break
        sleep(1)
    yield celery_session_worker


@pytest.fixture(scope="function", autouse=True)
async def mongo_connection(monkeypatch):
    with monkeypatch.context() as m:
        random_db: str = uuid4().hex
        m.setattr(env, "MONGO_DB_NAME", random_db)
        mongo_client = await init_mongo()
        yield
        mongo_client.drop_database(random_db)


@pytest.fixture(scope="module", autouse=True)
async def mock_client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


async def always_active():
    return User(
        username="test",
        email="test",
        last_name="test",
        first_name="test",
        hashed_password=bcrypt_hash("test"),
        disabled=False,
        can_upload=True,
        can_delete=True,
    )


@pytest.fixture(scope="function", autouse=True)
async def mock_client_superuser(mongo_connection):
    user = await always_active()
    await user.save()
    app.dependency_overrides[is_active] = always_active
    while True:
        saved_user = await User.find_one(User.username == "test")
        if saved_user is not None:
            break
        await asyncio.sleep(1)
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides = {}
    await user.delete()


@pytest.fixture(scope="function", autouse=True)
def pwd():
    return os.path.dirname(os.path.abspath(__file__))
