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

import os

import structlog
from dotenv import load_dotenv

_logger = structlog.get_logger(__name__)

LOADED: bool = False

if not LOADED:
    if load_dotenv(os.path.join(os.path.dirname(__file__), "../../../docker/.env")):
        _logger.info("Using .env file.")
    else:
        _logger.info("No .env file found.")

MB_FASTAPI_WORKERS: str = os.getenv("MB_FASTAPI_WORKERS", "1")
MB_PORT: str = os.getenv("MB_PORT", "8000")
MB_FS_ROOT: str = os.getenv("MB_FS_ROOT", "./files")
MB_CELERY: str = os.getenv("MB_CELERY", "")
MB_MAIN_SITE: str = os.getenv("MB_MAIN_SITE", "http://localhost:8000")
while MB_MAIN_SITE.endswith("/"):
    MB_MAIN_SITE = MB_MAIN_SITE[:-1]

MB_SUPERUSER_USERNAME: str = os.getenv("MB_SUPERUSER_USERNAME")
MB_SUPERUSER_EMAIL: str = os.getenv("MB_SUPERUSER_EMAIL")
MB_SUPERUSER_FIRST_NAME: str = os.getenv("MB_SUPERUSER_FIRST_NAME")
MB_SUPERUSER_LAST_NAME: str = os.getenv("MB_SUPERUSER_LAST_NAME")
MB_SUPERUSER_PASSWORD: str = os.getenv("MB_SUPERUSER_PASSWORD")

MB_SECRET_KEY: str = os.getenv("MB_SECRET_KEY")
MB_ALGORITHM: str = os.getenv("MB_ALGORITHM", "HS256")
MB_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("MB_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

RABBITMQ_USERNAME: str = os.getenv("RABBITMQ_USERNAME")
RABBITMQ_PASSWORD: str = os.getenv("RABBITMQ_PASSWORD")
RABBITMQ_HOST: str = os.getenv("RABBITMQ_HOST", "localhost")

MONGO_USERNAME: str = os.getenv("MONGO_USERNAME")
MONGO_PASSWORD: str = os.getenv("MONGO_PASSWORD")
MONGO_HOST: str = os.getenv("MONGO_HOST", "localhost")
MONGO_PORT: str = os.getenv("MONGO_PORT", "27017")

if not LOADED:
    _logger.info(f"Hosting on {MB_MAIN_SITE}.")

    if MB_CELERY:
        _logger.info("Using celery.")
    else:
        _logger.info("Using self process as worker.")

    from fastapi import __version__ as fastapi_version
    from packaging import version

    if version.parse(fastapi_version) >= version.parse("0.106.0") and not MB_CELERY:
        raise RuntimeError("For 0.106.0 and later FastAPI versions, need to switch on celery.")

LOADED = True
