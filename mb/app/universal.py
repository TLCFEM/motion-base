#  Copyright (C) 2022 Theodore Chang
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
import asyncio
import uuid

from fastapi import Query

from mb.app.main import app
from mb.app.response import ListSequenceResponse, SequenceResponse
from mb.record.jp import NIED
from mb.record.nz import NZSM


async def retrieve_record(record_id: uuid.UUID, normalised: bool) -> SequenceResponse | None:
    result = await NIED.find_one(NIED.id == record_id)
    if not result:
        result = await NZSM.find_one(NZSM.id == record_id)

    if not result:
        return None

    interval, record = result.to_waveform(normalised=normalised, unit='cm/s/s')

    # noinspection PyTypeChecker
    return SequenceResponse(
        **result.dict(),
        endpoint=f'/waveform/{record_id}',
        interval=interval,
        data=record.tolist())


@app.get('/waveform/{file_id_or_name}', response_model=ListSequenceResponse)
async def download_single_waveform(
        record_ids: list[uuid.UUID],
        normalised: bool = Query(default=False)
):
    """
    Retrieve raw accelerograph waveform.
    """
    tasks = [retrieve_record(record_id, normalised) for record_id in record_ids]
    results = await asyncio.gather(*tasks)

    # noinspection PyTypeChecker
    return ListSequenceResponse(records=[result for result in results if result is not None])
