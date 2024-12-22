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

import sys
from uuid import uuid4

from pydantic import BaseModel, Field


class Config(BaseModel):
    workers: int = Field(2, ge=1)
    host: str | None = Field(None)
    port: int = Field(8000, ge=1)
    overwrite_env: bool = Field(False)
    celery: bool = Field(False)
    debug: bool = Field(False)
    celery_config: list = Field([])


def run_app(setting: Config):
    if setting.celery:
        from mb.celery import celery

        from mb.utility.config import init_mongo
        import asyncio

        args: list = ["worker"]
        args.extend(setting.celery_config)
        if sys.platform == "win32":
            args.extend(
                ["--pool", "solo", "--hostname", uuid4().hex, "--loglevel", "info"]
            )

        asyncio.run(init_mongo())
        celery.start(args)
    else:
        from mb.utility.env import MB_FASTAPI_WORKERS, MB_PORT  # pylint: disable=import-outside-toplevel

        config: dict = {}

        if (
            workers := setting.workers
            if setting.overwrite_env
            else int(MB_FASTAPI_WORKERS)
        ) > 1:
            config["workers"] = workers
        elif setting.debug:
            config["reload"] = True
            config["log_level"] = "debug"

        if (port := setting.port if setting.overwrite_env else int(MB_PORT)) != 8000:
            config["port"] = port

        if setting.host:
            config["host"] = setting.host

        import uvicorn

        print(f"Run the app with the following arguments: {config}.")
        uvicorn.run("mb.app.main:app", **config)
