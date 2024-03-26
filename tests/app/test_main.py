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

import os
from http import HTTPStatus

import pytest

from mb.record.async_record import Record


async def test_alive(mock_client):
    response = await mock_client.get("/alive")
    assert response.status_code == 200
    assert response.json() == {"message": "I'm alive!"}


@pytest.mark.parametrize(
    "file_name,status",
    [
        pytest.param("jp_test.knt.tar.gz", HTTPStatus.ACCEPTED, id="correct-name"),
        pytest.param("wrong_name", HTTPStatus.ACCEPTED, id="wrong-name"),
    ],
)
@pytest.mark.parametrize("if_wait", [pytest.param("true", id="wait-for-result"), pytest.param("false", id="no-wait")])
async def test_upload_jp(mock_client_superuser, mock_header, pwd, file_name, status, if_wait):
    with open(os.path.join(pwd, "data/jp_test.knt.tar.gz"), "rb") as file:
        files = {"archives": (file_name, file, "multipart/form-data")}
        response = await mock_client_superuser.post(
            f"/jp/upload?wait_for_result={if_wait}", files=files, headers=mock_header
        )
        assert response.status_code == status


@pytest.mark.parametrize(
    "file_name,status",
    [
        pytest.param("nz_test.zip", HTTPStatus.ACCEPTED, id="zip-file"),
        pytest.param("nz_test.tar.gz", HTTPStatus.ACCEPTED, id="correct-name"),
        pytest.param("wrong_name", HTTPStatus.ACCEPTED, id="wrong-name"),
    ],
)
@pytest.mark.parametrize("if_wait", [pytest.param("true", id="wait-for-result"), pytest.param("false", id="no-wait")])
async def test_upload_nz(mock_client_superuser, mock_header, pwd, file_name, status, if_wait):
    with open(os.path.join(pwd, f"data/{file_name}" if "zip" in file_name else "data/nz_test.tar.gz"), "rb") as file:
        files = {"archives": (file_name, file, "multipart/form-data")}
        response = await mock_client_superuser.post(
            f"/nz/upload?wait_for_result={if_wait}", files=files, headers=mock_header
        )
        assert response.status_code == status


@pytest.mark.parametrize(
    "data_type",
    [pytest.param("raw", id="raw"), pytest.param("waveform", id="waveform"), pytest.param("spectrum", id="spectrum")],
)
async def test_jackpot(mock_client, data_type):
    response = await mock_client.get(f"/{data_type}/jackpot")
    assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize("count_total", [True, False])
async def test_download_nz(mock_client, count_total):
    response = await mock_client.post(f"/query?count_total={count_total}", json={})
    assert response.status_code == HTTPStatus.OK


async def test_process(mock_client):
    record = await Record.aggregate([{"$sample": {"size": 1}}], projection_model=Record).to_list()
    response = await mock_client.post(
        f"/process?record_id={record[0].id}", json={"with_spectrum": True, "with_response_spectrum": True}
    )
    assert response.status_code == HTTPStatus.OK


async def test_acquire_token(mock_client_superuser):
    response = await mock_client_superuser.post(
        "/token",
        data={"username": "test", "password": "test"},
    )
    print(response.json())
    assert response.status_code == HTTPStatus.OK
