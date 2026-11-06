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
from http import HTTPStatus
from uuid import uuid4

import pytest
from httpx2 import ASGITransport, AsyncClient

from mb.app import main as main_module
from mb.app.main import app
from mb.app.utility import User, is_active
from mb.record.async_record import UploadTask, create_task


def _restricted_user(*, can_upload: bool = False, can_delete: bool = False):
    async def _user():
        return User(
            username="restricted",
            email="restricted@example.com",
            last_name="restricted",
            first_name="restricted",
            hashed_password="unused",
            disabled=False,
            can_upload=can_upload,
            can_delete=can_delete,
        )

    return _user


async def _client_with_user(user_factory):
    app.dependency_overrides[is_active] = user_factory
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            yield client
    finally:
        app.dependency_overrides.pop(is_active, None)


async def test_profile_request(mock_client):
    response = await mock_client.get("/alive?__profile__=true")

    assert response.status_code == HTTPStatus.OK
    assert "html" in response.text.lower()


async def test_lifespan(monkeypatch):
    events: list[str] = []

    @asynccontextmanager
    async def fake_init_mongo(*args, **kwargs):
        events.append("mongo")
        yield None

    async def fake_create_superuser():
        events.append("superuser")

    class FakeBroker:
        async def startup(self):
            events.append("startup")

        async def shutdown(self):
            events.append("shutdown")

    monkeypatch.setattr(main_module, "init_mongo", fake_init_mongo)
    monkeypatch.setattr(main_module, "create_superuser", fake_create_superuser)
    monkeypatch.setattr(main_module, "broker", FakeBroker())

    async with main_module.lifespan(app):
        assert events == ["mongo", "superuser", "startup"]

    assert events[-1] == "shutdown"


async def test_task_status_endpoints(mock_client, mongo_connection):
    task_id = await create_task()

    response = await mock_client.get(f"/task/status/{task_id}")
    assert response.status_code == HTTPStatus.OK
    assert response.json()["id"] == task_id

    missing_id = str(uuid4())
    response = await mock_client.get(f"/task/status/{missing_id}")
    assert response.status_code == HTTPStatus.NOT_FOUND

    response = await mock_client.post("/task/status", json=[task_id, missing_id])
    assert response.status_code == HTTPStatus.OK
    tasks = response.json()["tasks"]
    assert tasks[0]["id"] == task_id
    assert tasks[1] is None

    task = await UploadTask.find_one(UploadTask.id == task_id)
    await task.delete()


async def test_jackpot_without_records(mock_client):
    response = await mock_client.get("/raw/jackpot")

    assert response.status_code == HTTPStatus.NO_CONTENT


@pytest.mark.parametrize("normalised", [True, False])
async def test_jackpot_waveform(sample_data, mock_client, normalised):
    response = await mock_client.get(
        f"/waveform/jackpot?normalised={str(normalised).lower()}"
    )

    assert response.status_code == HTTPStatus.OK
    assert response.json()["waveform"]


async def test_download_multiple_waveforms(sample_data, mock_client):
    record_ids = [record.id for record in sample_data[:2]]

    response = await mock_client.post("/waveform", json=record_ids)

    assert response.status_code == HTTPStatus.OK
    assert len(response.json()["records"]) == 2


async def test_query_with_all_filters(sample_data, mock_client):
    query = {
        "region": "nz",
        "min_magnitude": 0,
        "max_magnitude": 10,
        "category": "processed",
        "event_location": [172.0, -43.0],
        "max_event_distance": 1000000,
        "station_location": [172.0, -43.0],
        "max_station_distance": 1000000,
        "from_date": "1990-01-01T00:00:00",
        "to_date": "2030-01-01T00:00:00",
        "min_pga": 0,
        "max_pga": 1000,
        "file_name": "DS",
        "station_code": "DS",
        "direction": "E",
        "pagination": {
            "page_size": 5,
            "page_number": 0,
            "sort_by": "+magnitude",
        },
    }

    response = await mock_client.post("/query?count_total=true", json=query)

    assert response.status_code == HTTPStatus.OK
    body = response.json()
    assert body["pagination"]["total"] >= len(body["records"])
    assert body["pagination"]["sort_by"] == "+magnitude"


async def test_search_with_filters_and_search_after(sample_data, mock_client):
    query = {
        "region": "nz",
        "min_magnitude": 0,
        "max_magnitude": 10,
        "category": "processed",
        "event_location": [172.0, -43.0],
        "max_event_distance": 1000000,
        "station_location": [172.0, -43.0],
        "max_station_distance": 1000000,
        "from_date": "1990-01-01T00:00:00",
        "to_date": "2030-01-01T00:00:00",
        "min_pga": 0,
        "max_pga": 1000,
        "file_name": "20030821_121249_BDCS.V2A",
        "station_code": "BDCS",
        "direction": "S31E",
        "pagination": {
            "page_size": 1,
            "page_number": 0,
            "sort_by": "-magnitude",
        },
    }

    response = await mock_client.post("/search", json=query)
    assert response.status_code == HTTPStatus.OK
    body = response.json()
    assert len(body["records"]) == 1
    assert body["pagination"]["search_after"] is not None

    query["pagination"]["search_after"] = body["pagination"]["search_after"]
    response = await mock_client.post("/search", json=query)
    assert response.status_code == HTTPStatus.OK


async def test_search_invalid_sort(mock_client):
    response = await mock_client.post(
        "/search", json={"pagination": {"sort_by": "invalid"}}
    )

    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


async def test_index_records(mock_client_superuser):
    response = await mock_client_superuser.post(
        "/index",
        json={
            "records": [
                {"index": {"_id": f"test-{uuid4()}"}},
                {"file_name": "test.V1A", "region": "nz"},
            ]
        },
    )

    assert response.status_code == HTTPStatus.OK


async def test_index_forbidden(mongo_connection):
    async for client in _client_with_user(_restricted_user(can_upload=False)):
        response = await client.post("/index", json={"records": []})
        assert response.status_code == HTTPStatus.UNAUTHORIZED


async def test_purge_requires_authentication(mock_client):
    response = await mock_client.delete("/purge")

    assert response.status_code == HTTPStatus.UNAUTHORIZED


async def test_purge_forbidden(mongo_connection):
    async for client in _client_with_user(_restricted_user(can_delete=False)):
        response = await client.delete("/purge")
        assert response.status_code == HTTPStatus.UNAUTHORIZED


async def test_process_missing_record(mock_client):
    response = await mock_client.post(f"/process?record_id={uuid4()}", json={})

    assert response.status_code == HTTPStatus.NOT_FOUND


@pytest.mark.parametrize("path", ["/jp/upload", "/nz/upload"])
async def test_upload_forbidden(mongo_connection, path):
    async for client in _client_with_user(_restricted_user(can_upload=False)):
        response = await client.post(
            path,
            files={"archives": ("test.tar.gz", b"content", "application/gzip")},
        )
        assert response.status_code == HTTPStatus.UNAUTHORIZED


class _FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    async def json(self):
        return self.payload

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        return None


class _FakeSession:
    def __init__(self, payload):
        self.payload = payload

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        return None

    def post(self, *args, **kwargs):
        return _FakeResponse(self.payload)


@pytest.mark.parametrize(
    "payload,expected",
    [
        ({"success": True}, {"success": True}),
        (
            {"success": False, "error-codes": ["invalid-input-response"]},
            {
                "success": False,
                "errors": ["invalid-input-response"],
            },
        ),
    ],
)
async def test_turnstile(monkeypatch, mock_client, payload, expected):
    monkeypatch.setattr(main_module, "TURNSTILE_SECRET", "secret")
    monkeypatch.setattr(
        main_module.aiohttp, "ClientSession", lambda: _FakeSession(payload)
    )

    response = await mock_client.post("/turnstile", data={"turnstile_token": "token"})

    assert response.status_code == HTTPStatus.OK
    assert response.json() == expected


async def test_turnstile_not_configured(monkeypatch, mock_client):
    monkeypatch.setattr(main_module, "TURNSTILE_SECRET", "")

    response = await mock_client.post("/turnstile", data={"turnstile_token": "token"})

    assert response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
