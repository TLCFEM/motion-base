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
import os

import click
import structlog
import uvicorn
from dotenv import load_dotenv

_logger = structlog.get_logger(__name__)


def run_app(**kwargs):
    if load_dotenv(os.path.join(os.path.dirname(__file__), "../../docker/.env")):
        _logger.info("Using .env file.")
    else:
        _logger.info("No .env file found.")

    workers = os.getenv("WORKERS", None)
    if workers is None:
        workers = kwargs.get("workers", 1)

    config: dict = {}

    if workers > 1:
        config["workers"] = workers
        config["log_level"] = "info"
    else:
        config["reload"] = True
        config["log_level"] = "debug"

    if "host" in kwargs:
        config["host"] = kwargs["host"]

    uvicorn.run("mb.app.main:app", **config)


@click.command()
@click.option("--workers", default=1, help="Number of workers.")
def run(workers: int = 1):
    if workers > 1:
        run_app(workers=workers)
    else:
        run_app()


if __name__ == "__main__":
    run()
