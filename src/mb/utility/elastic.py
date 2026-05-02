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

from __future__ import annotations

import asyncio
import time
from contextlib import asynccontextmanager, contextmanager

from elasticsearch import AsyncElasticsearch, BadRequestError, Elasticsearch

from mb.utility.env import ELASTIC_HOST

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


@asynccontextmanager
async def async_elastic():
    # noinspection HttpUrlsUsage
    async with AsyncElasticsearch(f"http://{ELASTIC_HOST}:9200") as client:
        counter: int = 0
        while not await client.ping():
            counter += delay
            if counter > 600:
                raise ConnectionError("Elasticsearch is not available.")
            await asyncio.sleep(delay)

        if not await client.indices.exists(index="record"):
            try:
                await client.indices.create(
                    index="record", mappings=generate_elastic_mapping()
                )
            except BadRequestError as e:
                if not await client.indices.exists(index="record"):
                    raise e

        yield client


@contextmanager
def sync_elastic():
    # noinspection HttpUrlsUsage
    with Elasticsearch(f"http://{ELASTIC_HOST}:9200") as client:
        counter: int = 0
        while not client.ping():
            counter += delay
            if counter > 600:
                raise ConnectionError("Elasticsearch is not available.")
            time.sleep(delay)

        if not client.indices.exists(index="record"):
            client.indices.create(index="record", mappings=generate_elastic_mapping())

        yield client
