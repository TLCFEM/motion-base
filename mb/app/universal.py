#  Copyright (C) 2022-2023 Theodore Chang
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
from uuid import UUID

from mb.app.response import QueryConfig
from mb.record.record import Record, MetadataRecord


async def retrieve_record(record_id: UUID):
    return await Record.find_one(Record.id == record_id)


async def query_database(query: QueryConfig):
    find_result = Record.find(query.generate_query_string())

    return find_result.skip(query.page_number * query.page_size).limit(query.page_size).project(MetadataRecord)
