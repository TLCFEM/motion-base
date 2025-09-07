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

import os
from http import HTTPStatus

import pytest

from mb import celery


@pytest.mark.parametrize(
    "file_name,status",
    [
        pytest.param("jp_test.knt.tar.gz", HTTPStatus.ACCEPTED, id="correct-name"),
        pytest.param("wrong_name", HTTPStatus.ACCEPTED, id="wrong-name"),
    ],
)
@pytest.mark.parametrize(
    "if_wait",
    [pytest.param("true", id="wait-for-result"), pytest.param("false", id="no-wait")],
)
@pytest.mark.parametrize(
    "if_celery",
    [pytest.param(True, id="with-celery"), pytest.param(False, id="no-celery")],
)
async def test_upload_jp(
    monkeypatch,
    mock_client_superuser,
    pwd,
    file_name,
    status,
    if_wait,
    if_celery,
):
    if if_celery:

        def return_none():
            return None

        monkeypatch.setattr(celery, "get_stats", return_none)

    with open(os.path.join(pwd, "data/jp_test.knt.tar.gz"), "rb") as file:
        response = await mock_client_superuser.post(
            f"/jp/upload?wait_for_result={if_wait}",
            files={"archives": (file_name, file, "multipart/form-data")},
        )
        assert response.status_code == status
