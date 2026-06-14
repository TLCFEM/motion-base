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


from fastapi import BackgroundTasks

from ..celery import get_stats
from ..record.async_record import create_task
from .response import UploadResponse


async def dispatch(
    tasks: BackgroundTasks,
    valid_uris: list[str],
    parse_archive,
    parse_archive_local,
    user_id: str,
    overwrite_existing: bool,
):
    task_id_pool: list[str] = []

    if get_stats() is not None:
        for archive_uri in valid_uris:
            task_id: str = await create_task()
            parse_archive.delay(archive_uri, user_id, task_id, overwrite_existing)
            task_id_pool.append(task_id)
    else:
        for archive_uri in valid_uris:
            task_id: str = await create_task()
            tasks.add_task(
                parse_archive_local, archive_uri, user_id, task_id, overwrite_existing
            )
            task_id_pool.append(task_id)

    return UploadResponse(
        message="Successfully uploaded and will be processed in the background.",
        task_ids=task_id_pool,
        records=None,
    )
