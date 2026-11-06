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

import asyncio
import os.path
from uuid import uuid4

import pytest
from httpx2 import ASGITransport, AsyncClient

from mb.app.main import app
from mb.app.utility import User, bcrypt_hash, is_active, is_admin
from mb.record.async_record import Record
from mb.record.parser import ParserNZSM
from mb.record.utility import str_factory
from mb.utility import UPath, env
from mb.utility.config import init_mongo
from mb.utility.elastic import async_elastic
from mb.utility.files import serialize_records


@pytest.fixture(scope="function")
async def mongo_connection(monkeypatch):
    monkeypatch.setattr(env, "MONGO_DB_NAME", random_db := uuid4().hex)
    async with init_mongo(random_db) as mongo_client:
        yield
        await mongo_client.drop_database(random_db)


@pytest.fixture(scope="function")
async def mock_client(mongo_connection):
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


@pytest.fixture(scope="function")
async def mock_client_superuser(monkeypatch, mongo_connection):
    monkeypatch.setitem(app.dependency_overrides, is_active, always_active)
    monkeypatch.setitem(app.dependency_overrides, is_admin, always_active)
    user = await always_active()
    await user.save()
    while (await User.find_one(User.username == "test")) is None:
        await asyncio.sleep(1)
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    await user.delete()
    while (await User.find_one(User.username == "test")) is not None:
        await asyncio.sleep(1)


@pytest.fixture(scope="function")
def pwd():
    return os.path.dirname(os.path.abspath(__file__))


@pytest.fixture(scope="function")
async def sample_data(pwd, mongo_connection):
    results = await ParserNZSM.parse_archive(
        archive_obj=UPath(pwd) / "data/nz_test.tar.gz", user_id=str_factory()
    )

    async with async_elastic() as client:
        await client.bulk(
            index="record", body=serialize_records(results), refresh=True
        )

    yield await Record.find_all().to_list()
