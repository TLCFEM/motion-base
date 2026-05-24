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

from pydantic import BaseModel, Field


class Config(BaseModel):
    workers: int = Field(default=2, ge=1)
    host: str | None = Field(default=None)
    port: int = Field(default=8000, ge=1)
    overwrite_env: bool = Field(default=False)
    worker: bool = Field(default=False)
    debug: bool = Field(default=False)
    worker_config: list = Field(default_factory=list)


def run_worker(args: list):
    from taskiq.cli.worker.args import WorkerArgs
    from taskiq.cli.worker.run import run_worker

    worker_args = WorkerArgs.from_cli(args)
    run_worker(worker_args)


def run_app(setting: Config):
    if setting.worker:
        args = setting.worker_config
        if not args:
            args = ["mb.utility.taskiq:taskiq_broker", "mb.app.jp", "mb.app.nz"]
        run_worker(args)
    else:
        from mb.utility.env import (  # pylint: disable=import-outside-toplevel
            MB_FASTAPI_WORKERS,
            MB_PORT,
        )

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
