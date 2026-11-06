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

import base64
import inspect
import json
import uuid
from datetime import UTC, datetime, timedelta
from http import HTTPStatus

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pytest

from mb.app.response import PaginationConfig, QueryConfig
from mb.client import MBClient, MBRecord, MBToken


class FakeResponse:
    def __init__(self, status_code=HTTPStatus.OK, payload=None):
        self.status_code = status_code
        self._payload = payload if payload is not None else {}

    def json(self):
        return self._payload


class FakeClient:
    def __init__(self, handler):
        self.handler = handler
        self.calls: list[tuple] = []
        self.closed = False

    async def _call(self, method, url, kwargs):
        result = self.handler(method, url, kwargs)
        return await result if inspect.isawaitable(result) else result

    async def get(self, url, **kwargs):
        self.calls.append(("GET", url, kwargs))
        return await self._call("GET", url, kwargs)

    async def post(self, url, **kwargs):
        self.calls.append(("POST", url, kwargs))
        return await self._call("POST", url, kwargs)

    async def aclose(self):
        self.closed = True


def _record_data(record_id="record-id"):
    return {
        "id": record_id,
        "file_name": "record.V1A",
        "time_interval": 0.1,
        "waveform": [0.0, 1.0, -1.0, 0.5],
        "processed_data_unit": "cm/s/s",
        "raw_data_unit": "cm/s/s",
    }


def _make_client(handler, **kwargs):
    client = MBClient("http://test", **kwargs)
    client.client = FakeClient(handler)
    client.print = lambda *args, **kwargs: None
    return client


def _token(expires_in: int = 3600, **claims) -> str:
    payload = {
        "exp": int((datetime.now(UTC) + timedelta(seconds=expires_in)).timestamp())
    }
    payload.update(claims)
    encoded = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=")
    return f"header.{encoded.decode()}.signature"


def test_mb_record_new_record():
    record = MBRecord.new_record(_record_data())

    assert record.id == "record-id"
    assert record.file_name == "record.V1A"


def test_mb_record_tables(tmp_path):
    record = MBRecord.new_record(_record_data())

    x_axis, y_axis = record.to_table()
    assert len(x_axis) == len(y_axis) == 4
    assert y_axis == record.waveform

    _, converted = record.to_table(unit="m/s/s")
    assert converted == pytest.approx(np.array(record.waveform) * 0.01)

    file_path = tmp_path / "record.txt"
    record.to_table_file(file_path.as_posix())
    assert len(file_path.read_text().splitlines()) == 4


def test_mb_record_plots():
    record = MBRecord.new_record(_record_data())

    figure = plt.figure()
    assert record.plot_waveform(figure) is figure
    plt.close(figure)

    figure = record.plot_waveform()
    assert figure is not None
    plt.close(figure)

    figure = plt.figure()
    assert record.plot_spectrum(figure) is figure
    plt.close(figure)

    figure = record.plot_spectrum()
    assert figure is not None
    plt.close(figure)

    figure = record.plot_response_spectrum(period_bracket=np.array([0.1, 0.2]))
    assert figure is not None
    plt.close(figure)

    plt.close("all")


def test_mb_token():
    token = MBToken(_token(expires_in=60))

    assert token.expiry.tzinfo is UTC
    assert token.expiry > datetime.now(UTC)


def test_client_initialisation():
    client = MBClient("http://example.com///", max_file_size=2)

    assert client.host_url == "http://example.com"
    assert client.max_file_size == 2 * 2**20
    assert len(client) == 0

    client.download_pool.append("record")
    assert len(client) == 1
    assert list(client) == ["record"]

    client.download_size = 1
    client.current_download_size = 1
    client.clear()
    assert len(client) == 0
    assert client.download_size == 0
    assert client.current_download_size == 0


async def test_client_context_manager():
    client = _make_client(
        lambda method, url, kwargs: FakeResponse(
            HTTPStatus.OK, {"message": "I'm alive!"}
        )
    )

    assert await client.__aenter__() is client
    await client.__aexit__(None, None, None)
    assert client.client.closed

    failing = _make_client(
        lambda method, url, kwargs: FakeResponse(HTTPStatus.INTERNAL_SERVER_ERROR)
    )
    with pytest.raises(RuntimeError, match="Server is not reachable"):
        await failing.__aenter__()


async def test_header_without_credentials():
    client = _make_client(lambda method, url, kwargs: FakeResponse())

    assert await client._header() == {}


async def test_header_cached_token():
    client = _make_client(
        lambda method, url, kwargs: pytest.fail("should not request a token")
    )
    client.username = "user"
    client.password = "password"
    client._token = MBToken(_token())

    assert (await client._header())["Authorization"].startswith("Bearer ")


async def test_header_expired_token():
    client = _make_client(
        lambda method, url, kwargs: FakeResponse(
            HTTPStatus.OK, {"access_token": _token()}
        )
    )
    client.username = "user"
    client.password = "password"
    client._token = MBToken(_token(expires_in=10))

    assert (await client._header())["Authorization"].startswith("Bearer ")
    assert client.client.calls[0][1].endswith("/user/token")


async def test_header_token_failure():
    client = _make_client(
        lambda method, url, kwargs: FakeResponse(HTTPStatus.UNAUTHORIZED)
    )
    client.username = "user"
    client.password = "password"

    assert await client._header() == {}


async def test_me():
    client = _make_client(
        lambda method, url, kwargs: FakeResponse(HTTPStatus.OK, {"username": "user"})
    )

    assert await client.me() == {"username": "user"}

    failing = _make_client(
        lambda method, url, kwargs: FakeResponse(HTTPStatus.UNAUTHORIZED)
    )
    with pytest.raises(RuntimeError, match="Failed to get user info"):
        await failing.me()


async def test_download():
    client = _make_client(
        lambda method, url, kwargs: FakeResponse(
            HTTPStatus.OK, {"records": [_record_data()]}
        )
    )

    await client.download("record-id")
    assert len(client.download_pool) == 1
    assert client.current_download_size == 1

    await client.download(uuid.uuid4())
    await client.download(MBRecord.new_record(_record_data("another")))
    assert len(client.download_pool) == 3

    await client.download(["a", "b"])
    assert len(client.download_pool) == 5
    assert client.download_size == 2


async def test_download_failure():
    client = _make_client(
        lambda method, url, kwargs: FakeResponse(HTTPStatus.INTERNAL_SERVER_ERROR)
    )

    await client.download("record-id")

    assert len(client.download_pool) == 0
    assert client.current_download_size == 1


async def test_retry():
    attempts = 0

    async def eventually_successful():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise ValueError("try again")
        return "ok"

    assert (
        await MBClient._retry(
            eventually_successful, retries=3, delay=0, exceptions=(ValueError,)
        )
        == "ok"
    )
    assert attempts == 3

    async def always_failing():
        raise ValueError("failure")

    with pytest.raises(ValueError, match="failure"):
        await MBClient._retry(
            always_failing, retries=1, delay=0, exceptions=(ValueError,)
        )


async def test_upload_requires_authentication():
    client = _make_client(lambda method, url, kwargs: FakeResponse())

    assert await client.upload("nz", "file.V1A") is None


async def test_upload_generator(tmp_path):
    path = tmp_path / "record.V1A"
    path.write_text("data")

    def files():
        yield path.as_posix()

    client = _make_client(
        lambda method, url, kwargs: FakeResponse(
            HTTPStatus.ACCEPTED, {"task_ids": ["task-id"]}
        ),
        username="user",
        password="password",
    )
    client._token = MBToken(_token())

    await client.upload("nz", files())

    assert client.tasks == {"task-id": 0}
    assert client.client.calls[0][1].endswith(
        "/nz/upload?wait_for_result=false&overwrite_existing=true"
    )


async def test_upload_directory(tmp_path):
    (tmp_path / "nested").mkdir()
    first = tmp_path / "a.V1A"
    second = tmp_path / "nested" / "b.v2a"
    ignored = tmp_path / "notes.txt"
    first.write_text("data")
    second.write_text("data")
    ignored.write_text("data")

    counter = 0

    def handler(method, url, kwargs):
        nonlocal counter
        counter += 1
        return FakeResponse(HTTPStatus.ACCEPTED, {"task_ids": [f"task-{counter}"]})

    client = _make_client(handler, username="user", password="password")
    client._token = MBToken(_token())

    await client.upload("nz", tmp_path.as_posix())

    assert client.upload_size == 2
    assert client.current_upload_size == 2
    assert set(client.tasks) == {"task-1", "task-2"}


async def test_upload_skips_files(tmp_path):
    missing = tmp_path / "missing.V1A"

    client = _make_client(
        lambda method, url, kwargs: pytest.fail("should not upload"),
        username="user",
        password="password",
    )

    await client.upload("nz", missing.as_posix())

    unsupported = tmp_path / "notes.txt"
    unsupported.write_text("data")
    await client.upload("nz", unsupported.as_posix())

    large = tmp_path / "large.V1A"
    large.write_text("data")
    small_limit = _make_client(
        lambda method, url, kwargs: pytest.fail("should not upload"),
        username="user",
        password="password",
        max_file_size=0.000001,
    )
    await small_limit.upload("nz", large.as_posix())


async def test_upload_failure(tmp_path):
    path = tmp_path / "record.V1A"
    path.write_text("data")

    client = _make_client(
        lambda method, url, kwargs: FakeResponse(HTTPStatus.BAD_REQUEST),
        username="user",
        password="password",
    )
    client._token = MBToken(_token())

    with pytest.raises(RuntimeError, match="Failed to upload"):
        await client.upload("nz", path.as_posix())


async def test_jackpot():
    client = _make_client(
        lambda method, url, kwargs: FakeResponse(HTTPStatus.OK, _record_data())
    )

    record = await client.jackpot()
    assert record is not None
    assert record.id == "record-id"

    failing = _make_client(
        lambda method, url, kwargs: FakeResponse(HTTPStatus.NO_CONTENT)
    )
    assert await failing.jackpot() is None


async def test_search():
    client = _make_client(
        lambda method, url, kwargs: FakeResponse(
            HTTPStatus.OK, {"records": [_record_data()]}
        )
    )

    records = await client.search(QueryConfig(min_magnitude=5))
    assert records is not None
    assert len(records) == 1

    records = await client.search({"min_magnitude": 5})
    assert records is not None

    failing = _make_client(
        lambda method, url, kwargs: FakeResponse(HTTPStatus.BAD_REQUEST)
    )
    assert await failing.search({}) is None


async def test_retrieve_all():
    calls = 0

    def handler(method, url, kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            return FakeResponse(
                HTTPStatus.OK,
                {
                    "records": [_record_data()],
                    "pagination": {"search_after": [1]},
                },
            )
        return FakeResponse(
            HTTPStatus.OK, {"records": [], "pagination": {"search_after": [2]}}
        )

    client = _make_client(handler)
    query = QueryConfig(pagination=PaginationConfig(page_size=1))

    records = [record async for record in client.retrieve_all(query)]

    assert len(records) == 1
    assert calls == 2

    failing = _make_client(
        lambda method, url, kwargs: FakeResponse(HTTPStatus.BAD_REQUEST)
    )
    assert [
        record
        async for record in failing.retrieve_all({"pagination": {"page_size": 1}})
    ] == []


async def test_task_status():
    client = _make_client(
        lambda method, url, kwargs: FakeResponse(
            HTTPStatus.OK, {"total_size": 4, "current_size": 2}
        )
    )
    client.tasks["task-id"] = 0

    await client.task_status("task-id")

    assert client.tasks["task-id"] == 0.5

    failing = _make_client(
        lambda method, url, kwargs: FakeResponse(HTTPStatus.NOT_FOUND)
    )
    failing.tasks["task-id"] = 0

    await failing.task_status("task-id")

    assert failing.tasks == {}


async def test_status(monkeypatch):
    async def no_sleep(_):
        return None

    monkeypatch.setattr("mb.client.anyio.sleep", no_sleep)

    client = _make_client(
        lambda method, url, kwargs: FakeResponse(HTTPStatus.NOT_FOUND)
    )
    client.tasks["task-id"] = 0

    await client.status()

    assert client.tasks == {}
