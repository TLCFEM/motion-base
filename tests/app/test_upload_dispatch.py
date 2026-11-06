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

import importlib

import pytest

from mb.app import dispatcher
from mb.record.async_record import UploadTask, create_task


class _FakeFileProxy:
    def __init__(self, file_uri, *, always_delete_on_exit):
        self.file = file_uri
        self.file_name = "test.tar.gz"
        self.always_delete_on_exit = always_delete_on_exit

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    async def bulk(self, records):
        return [record.file_name for record in records]


@pytest.mark.parametrize(
    "module_name,parser_name",
    [
        pytest.param("mb.app.jp", "ParserNIED", id="jp"),
        pytest.param("mb.app.nz", "ParserNZSM", id="nz"),
    ],
)
async def test_local_parse_error(
    monkeypatch, mongo_connection, module_name, parser_name
):
    module = importlib.import_module(module_name)
    parser = getattr(module, parser_name)

    async def fail(**kwargs):
        raise RuntimeError("parse failure")

    monkeypatch.setattr(module, "FileProxy", _FakeFileProxy)
    monkeypatch.setattr(parser, "parse_archive", fail)

    assert await module._parse_archive_local("s3://fake/test.tar.gz", "user") == []

    task_id = await create_task()
    assert (
        await module._parse_archive_local("s3://fake/test.tar.gz", "user", task_id)
        == []
    )
    assert await UploadTask.find_one(UploadTask.id == task_id) is None


@pytest.mark.parametrize(
    "module_name,parser_name",
    [
        pytest.param("mb.app.jp", "ParserNIED", id="jp"),
        pytest.param("mb.app.nz", "ParserNZSM", id="nz"),
    ],
)
async def test_worker_parse_error(
    monkeypatch, mongo_connection, module_name, parser_name
):
    module = importlib.import_module(module_name)
    parser = getattr(module, parser_name)

    async def fail(**kwargs):
        raise RuntimeError("parse failure")

    monkeypatch.setattr(module, "FileProxy", _FakeFileProxy)
    monkeypatch.setattr(parser, "parse_archive", fail)

    with pytest.raises(RuntimeError, match="parse failure"):
        await module._parse_archive_impl(
            "s3://fake/test.tar.gz", "user", None, True, False
        )

    task_id = "retry-task-id"
    with pytest.raises(RuntimeError, match="parse failure"):
        await module._parse_archive_impl(
            "s3://fake/test.tar.gz", "user", task_id, True, False
        )

    assert await UploadTask.find_one(UploadTask.id == task_id) is not None


async def test_dispatch_to_worker(monkeypatch):
    calls: list[tuple] = []

    async def has_workers():
        return True

    async def fake_create_task():
        return "task-id"

    class FakeTask:
        async def kiq(self, *args):
            calls.append(args)

    monkeypatch.setattr(dispatcher, "has_workers", has_workers)
    monkeypatch.setattr(dispatcher, "create_task", fake_create_task)

    response = await dispatcher.dispatch(
        None, ["archive-uri"], FakeTask(), None, "user-id", True
    )

    assert response.task_ids == ["task-id"]
    assert calls == [("archive-uri", "user-id", "task-id", True)]


async def test_dispatch_to_background_tasks(monkeypatch):
    added: list[tuple] = []

    async def has_workers():
        return False

    async def fake_create_task():
        return "task-id"

    class FakeBackgroundTasks:
        def add_task(self, *args):
            added.append(args)

    class FakeTask:
        async def kiq(self, *args):
            raise AssertionError("kiq should not be used")

    monkeypatch.setattr(dispatcher, "has_workers", has_workers)
    monkeypatch.setattr(dispatcher, "create_task", fake_create_task)

    response = await dispatcher.dispatch(
        FakeBackgroundTasks(), ["archive-uri"], FakeTask(), object, "user-id", False
    )

    assert response.task_ids == ["task-id"]
    assert len(added) == 1
    assert added[0][1:] == ("archive-uri", "user-id", "task-id", False)
