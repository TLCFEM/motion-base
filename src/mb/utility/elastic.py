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

from __future__ import annotations

import asyncio
import time

from elasticsearch import AsyncElasticsearch, Elasticsearch

from mb.utility.env import ELASTIC_HOST

async_client: AsyncElasticsearch | None = None
sync_client: Elasticsearch | None = None

delay: int = 5


def generate_elastic_mapping() -> dict:
    return {
        "properties": {
            "id": {"type": "text"},
            "file_name": {"type": "text"},
            "file_hash": {"type": "text"},
            "category": {"type": "text"},
            "region": {"type": "text"},
            "uploaded_by": {"type": "text"},
            "magnitude": {"type": "float"},
            "maximum_acceleration": {"type": "float"},
            "event_time": {"type": "date"},
            "event_location": {"type": "geo_point"},
            "depth": {"type": "float"},
            "station_code": {"type": "text"},
            "station_location": {"type": "geo_point"},
            "station_elevation": {"type": "float"},
            "station_elevation_unit": {"type": "text"},
            "record_time": {"type": "date"},
            "last_update_time": {"type": "date"},
            "sampling_frequency": {"type": "float"},
            "sampling_frequency_unit": {"type": "text"},
            "duration": {"type": "float"},
            "direction": {"type": "text"},
        }
    }


async def async_elastic():
    global async_client
    if async_client is None:
        # noinspection HttpUrlsUsage
        async_client = AsyncElasticsearch(f"http://{ELASTIC_HOST}:9200")

    counter: int = 0
    while True:
        if await async_client.ping():
            break
        else:
            counter += delay
            if counter > 600:
                raise ConnectionError("Elasticsearch is not available.")
            await asyncio.sleep(delay)
            continue

    if not await async_client.indices.exists(index="record"):
        await async_client.indices.create(
            index="record", mappings=generate_elastic_mapping()
        )

    return async_client


def sync_elastic():
    global sync_client
    if sync_client is None:
        # noinspection HttpUrlsUsage
        sync_client = Elasticsearch(f"http://{ELASTIC_HOST}:9200")

    counter: int = 0
    while True:
        if sync_client.ping():
            break
        else:
            counter += delay
            if counter > 600:
                raise ConnectionError("Elasticsearch is not available.")
            time.sleep(delay)
            continue

    if not sync_client.indices.exists(index="record"):
        sync_client.indices.create(index="record", mappings=generate_elastic_mapping())

    return sync_client
