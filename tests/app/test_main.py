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

from mb.record.sync_parser import ParserNZSM
from mb.record.sync_record import Record
from mb.record.utility import str_factory


async def test_redirect_to_docs(mock_client):
    response = await mock_client.get("/")
    assert response.status_code == HTTPStatus.TEMPORARY_REDIRECT


async def test_alive(mock_client):
    response = await mock_client.get("/alive")
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"message": "I'm alive!"}


async def test_total(mock_client):
    response = await mock_client.get("/total")
    assert response.status_code == HTTPStatus.OK


async def test_for_test_only(mock_client):
    response = await mock_client.get("/test_endpoint")
    assert response.status_code == HTTPStatus.OK


@pytest.fixture(scope="function")
def sample_data(pwd):
    ParserNZSM.parse_archive(archive_obj=os.path.join(pwd, "data/nz_test.tar.gz"), user_id=str_factory())

    yield Record.objects()


@pytest.mark.parametrize(
    "data_type",
    [pytest.param("raw", id="raw"), pytest.param("waveform", id="waveform"), pytest.param("spectrum", id="spectrum")],
)
async def test_jackpot(sample_data, mock_client, data_type):
    response = await mock_client.get(f"/{data_type}/jackpot")
    assert response.status_code == HTTPStatus.OK


async def test_waveform(sample_data, mock_client):
    response = await mock_client.post("/waveform", json=sample_data[0].id)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize("count_total", [True, False])
async def test_query(mock_client, count_total):
    response = await mock_client.post(f"/query?count_total={count_total}", json={})
    assert response.status_code == HTTPStatus.OK


async def test_process(sample_data, mock_celery, mock_client):
    response = await mock_client.post(
        f"/process?record_id={sample_data[0].id}",
        json={"with_filter": True, "with_spectrum": True, "with_response_spectrum": True},
    )
    assert response.status_code == HTTPStatus.OK
