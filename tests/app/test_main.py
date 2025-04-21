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
from datetime import datetime
from http import HTTPStatus

import pytest

from mb.record.parser import ParserNZSM
from mb.record.sync_record import Record
from mb.record.utility import str_factory
from mb.utility.elastic import sync_elastic


async def test_redirect_to_docs(mock_client):
    response = await mock_client.get("/")
    assert response.status_code == HTTPStatus.TEMPORARY_REDIRECT


async def test_alive(mock_client):
    response = await mock_client.get("/alive")
    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"message": "I'm alive!"}


async def test_get_total(mock_client):
    response = await mock_client.get("/total")
    assert response.status_code == HTTPStatus.OK


async def test_get_stats(mock_client):
    response = await mock_client.get("/stats")
    assert response.status_code == HTTPStatus.OK


async def test_post_total(mock_client):
    response = await mock_client.post("/total")
    assert response.status_code == HTTPStatus.OK


async def test_for_test_only(mock_client):
    response = await mock_client.get("/test_endpoint")
    assert response.status_code == HTTPStatus.OK


@pytest.fixture(scope="function")
def sample_data(pwd):
    results = ParserNZSM.parse_archive(
        archive_obj=os.path.join(pwd, "data/nz_test.tar.gz"), user_id=str_factory()
    )

    def to_dict(record) -> dict:
        dict_data = record.to_mongo()
        for key in (
            "scale_factor",
            "raw_data",
            "raw_data_unit",
            "offset",
            "_id",
            "_cls",
        ):
            dict_data.pop(key, None)
        dict_data["id"] = record.id
        for k, v in dict_data.items():
            if isinstance(v, datetime):
                dict_data[k] = v.isoformat()

        return dict_data

    bulk_body: list = []
    for r in results:
        bulk_body.append({"index": {"_id": r.id}})
        bulk_body.append(to_dict(r))

    sync_elastic().bulk(index="record", body=bulk_body)

    yield Record.objects()


@pytest.mark.parametrize(
    "data_type",
    [
        pytest.param("raw", id="raw"),
        pytest.param("waveform", id="waveform"),
        pytest.param("spectrum", id="spectrum"),
    ],
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
        json={
            "with_filter": True,
            "with_spectrum": True,
            "with_response_spectrum": True,
        },
    )
    assert response.status_code == HTTPStatus.OK


async def test_search(sample_data, mock_client):
    response = await mock_client.post("/search")
    assert response.status_code == HTTPStatus.OK


async def test_purge(sample_data, mock_client):
    response = await mock_client.delete("/purge")
    assert response.status_code == HTTPStatus.OK
