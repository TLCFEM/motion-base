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

from uuid import uuid4

import pytest
from taskiq.depends.progress_tracker import TaskProgress, TaskState
from taskiq.result import TaskiqResult

from mb.taskiq_mongo import MongoResultBackend, ResultIsMissingError
from mb.utility.config import mongo_uri


def _result(value="result", log="log") -> TaskiqResult:
    return TaskiqResult(
        is_err=False,
        log=log,
        return_value=value,
        execution_time=0.1,
    )


@pytest.fixture
async def backend():
    database = f"taskiq_test_{uuid4().hex}"
    backend = MongoResultBackend(mongo_uri(), database, ttl_seconds=60)
    await backend.startup()

    try:
        yield backend
    finally:
        await backend.client.drop_database(database)
        await backend.shutdown()


async def test_result_lifecycle(backend):
    assert not await backend.is_result_ready("missing")

    await backend.set_result("task-id", _result())

    assert await backend.is_result_ready("task-id")

    result = await backend.get_result("task-id")
    assert result.return_value == "result"
    assert result.log is None

    result = await backend.get_result("task-id", with_logs=True)
    assert result.log == "log"

    document = await backend.collection.find_one({"task_id": "task-id"})
    assert document is not None
    assert "expire_at" in document


async def test_progress_and_missing_result(backend):
    assert await backend.get_progress("task-id") is None

    await backend.set_progress(
        "task-id", TaskProgress(state=TaskState.STARTED, meta=25)
    )

    progress = await backend.get_progress("task-id")
    assert progress is not None
    assert progress.state == TaskState.STARTED
    assert progress.meta == 25

    assert not await backend.is_result_ready("task-id")

    with pytest.raises(ResultIsMissingError):
        await backend.get_result("task-id")


async def test_result_without_ttl():
    database = f"taskiq_test_{uuid4().hex}"
    backend = MongoResultBackend(mongo_uri(), database, ttl_seconds=0)
    await backend.startup()

    try:
        await backend.set_result("task-id", _result())

        document = await backend.collection.find_one({"task_id": "task-id"})
        assert document is not None
        assert "expire_at" not in document
    finally:
        await backend.client.drop_database(database)
        await backend.shutdown()


async def test_result_removed_after_read():
    database = f"taskiq_test_{uuid4().hex}"
    backend = MongoResultBackend(
        mongo_uri(), database, keep_results=False, ttl_seconds=60
    )
    await backend.startup()

    try:
        await backend.set_result("task-id", _result())
        assert await backend.is_result_ready("task-id")

        await backend.get_result("task-id")

        assert not await backend.is_result_ready("task-id")
        with pytest.raises(ResultIsMissingError):
            await backend.get_result("task-id")
    finally:
        await backend.client.drop_database(database)
        await backend.shutdown()
