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
import uuid

from mb.app.response import SequenceResponse
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