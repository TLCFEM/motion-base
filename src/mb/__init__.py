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

import sys

import click


def run_app(**kwargs):
    if kwargs.get("celery", False):
        from mb.celery import celery

        from mb.utility.config import init_mongo
        import asyncio

        args: list = ["worker"]
        if sys.platform == "win32":
            args.extend(["--pool", "solo", "--loglevel", "info"])

        asyncio.run(init_mongo())
        celery.start(args)
    else:
        from mb.utility.env import MB_FASTAPI_WORKERS, MB_PORT  # pylint: disable=import-outside-toplevel

        workers = MB_FASTAPI_WORKERS
        if kwargs.get("overwrite_env", False) and "workers" in kwargs:
            workers = kwargs["workers"]

        workers = int(workers)

        config: dict = {}

        if workers > 1:
            config["workers"] = workers
            config["log_level"] = "info"
        else:
            config["reload"] = True
            config["log_level"] = "debug"

        port = MB_PORT
        if kwargs.get("overwrite_env", False) and "port" in kwargs:
            port = kwargs["port"]
        config["port"] = int(port)

        if "host" in kwargs:
            config["host"] = kwargs["host"]

        import uvicorn

        uvicorn.run("mb.app.main:app", **config)


@click.command()
@click.option("--workers", default=1, show_default=True, type=int, help="Number of workers.")
@click.option("--overwrite-env", is_flag=True, help="Overwrite environment variables.")
def run(workers: int = 1, overwrite_env: bool = False):
    params: dict = {}
    if overwrite_env:
        params["overwrite_env"] = overwrite_env
    if workers > 1:
        params["workers"] = workers

    run_app(**params)


if __name__ == "__main__":
    run()
