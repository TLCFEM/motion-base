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


import uuid
import zipfile
from asyncio import Semaphore, gather, run
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

import click
from aiohttp import ClientSession
from bs4 import BeautifulSoup

DOMAIN = "https://data.geonet.org.nz"
BASE = f"{DOMAIN}/seismic-products/strong-motion/volume-products"
SEM_LIMIT = 10
RETRY = 3
FILE_LIST = (".v1a", ".v2a")


task_pool = set()
pending_pool = set()
total = 0
counter = 0


async def _execute_retry(fn, pool):
    global counter

    local_retry = RETRY
    while pool and local_retry > 0:
        counter = 0
        local_retry -= 1
        await fn()


async def _fetch_file(
    pack: tuple[Path, str, str], client: ClientSession, semaphore: Semaphore
):
    global counter

    file_folder, url_path, file_name = pack

    file_path = file_folder / file_name
    if file_path.exists() and file_path.stat().st_size > 0:
        counter += 1
        task_pool.remove(pack)
        return

    async with semaphore:
        counter += 1
        full_url = "/".join(
            [DOMAIN] + list(x for x in url_path.split("/") if x) + [file_name]
        )
        print(f"{datetime.now()} {counter}/{total} Downloading {full_url}")
        try:
            async with client.get(full_url) as response:
                if not response.ok:
                    return
                content = await response.read()
            if content:
                with open(file_path, "wb") as file:
                    file.write(content)
            task_pool.remove(pack)
        except Exception:  # noqa
            print(f">>> Fail to download {full_url}")


async def _crawl_once():
    global total
    total = len(task_pool)

    semaphore = Semaphore(SEM_LIMIT)
    async with ClientSession() as client:
        await gather(*[_fetch_file(task, client, semaphore) for task in task_pool])


async def crawl(root_path: Path):
    root_list = root_path / "items.txt"

    start_new: bool = True
    if root_list.exists():
        print(
            "The previous list of files is detected, do you want to download from scratch? (y/N)"
        )
        start_new = input().strip().lower() == "y"

    if start_new:
        with open(root_list, "w") as file:
            for index in root_path.rglob("index.htm"):
                with open(index) as f:
                    contents = BeautifulSoup(f, "html.parser")
                    url_path = quote(
                        contents.find("title").text.removeprefix("Index of ")
                    )
                    for link in contents.find_all("a"):
                        file_name: str = link.get("href")  # type: ignore
                        if file_name.lower().endswith(FILE_LIST):
                            file.write(f"{index.parent},{url_path},{file_name}\n")

    with open(root_list) as file:
        for line in file:
            folder, url_path, file_name = line.strip().split(",")
            task_pool.add((Path(folder), url_path, file_name))

    await _execute_retry(_crawl_once, task_pool)

    with open(root_list, "w") as file:
        for folder, url_path, file_name in task_pool:
            file.write(f"{folder},{url_path},{file_name}\n")


async def _parse_next(
    local: Path, remote: str, client: ClientSession, semaphore: Semaphore
):
    children: list = []

    async with semaphore:
        print(f"Creating directory: {local} from {remote}")
        async with client.get(remote) as response:
            if not response.ok:
                print(f">>> Error: {remote}")
                pending_pool.add((local, remote))
                return
            response_content = await response.read()

        pending_pool.discard((local, remote))
        local.mkdir(parents=True, exist_ok=True)
        with open(local / "index.htm", "wb") as file:
            file.write(response_content)
        for link in BeautifulSoup(response_content, "html.parser").find_all("a"):
            href: str = link.get("href")  # type: ignore
            if not href.startswith(("/", "Vol3", "Vol4", "plots")) and "." not in href:
                children.append(href.strip("/"))

    await gather(
        *[
            _parse_next(local / child, f"{remote}{child}/", client, semaphore)
            for child in children
        ]
    )


async def _parse_once():
    semaphore = Semaphore(SEM_LIMIT)
    async with ClientSession() as client:
        await gather(*[_parse_next(x, y, client, semaphore) for x, y in pending_pool])


async def parse(local: Path, targets: list[str]):
    failed_file = local / "failed.txt"

    start_new: bool = True
    if failed_file.exists():
        print(
            "The previous failed links are detected, do you want to create server structure from scratch? (y/N)"
        )
        start_new = input().strip().lower() == "y"

    if not start_new:
        with open(failed_file) as file:
            for line in file:
                local_path, remote_url = line.strip().split(",")
                pending_pool.add((Path(local_path), remote_url))
    else:
        for x in targets:
            if x_stripped := "/".join(v for v in x.split("/") if v):
                pending_pool.add((local / x_stripped, f"{BASE}/{x_stripped}/"))

    await _execute_retry(_parse_once, pending_pool)

    with open(failed_file, "w") as file:
        for local_path, remote_url in pending_pool:
            file.write(f"{local_path},{remote_url}\n")


def compress(root: Path):
    root.mkdir(parents=True, exist_ok=True)

    batch_size = 4000
    file_list = [p for p in root.rglob("*") if p.suffix.lower() in FILE_LIST]
    batches = [
        file_list[i : i + batch_size] for i in range(0, len(file_list), batch_size)
    ]

    def __compress(_fl):
        zip_file_name = f"{uuid.uuid4().hex}.zip"
        with zipfile.ZipFile(
            root / zip_file_name, "w", zipfile.ZIP_DEFLATED
        ) as archive:
            for f in _fl:
                if f.stat().st_size > 0:
                    archive.write(f, f.relative_to(root))
        return zip_file_name

    created = []
    with ProcessPoolExecutor() as executor:
        futures = {executor.submit(__compress, batch): len(batch) for batch in batches}
        for future in as_completed(futures):
            zip_path = future.result()
            created.append(zip_path)
            print(f"Created {zip_path} with {futures[future]} files.")


@click.command()
@click.option(
    "--mode",
    "-m",
    default="all",
    type=str,
    help="Mode of operation: parse, crawl, or all. Default is all.",
)
@click.option(
    "--root",
    "-r",
    default=Path.cwd() / "NZSM",
    type=Path,
    help="Local root folder: where do you want to put the downloaded data? Default is ./NZSM",
)
@click.option(
    "--parallel",
    "-p",
    default=10,
    type=int,
    help="Number of concurrent requests. Default is 10.",
)
@click.option(
    "--retry", default=3, type=int, help="Number of retry attempts. Default is 3."
)
@click.option("--dry-run", default=False, is_flag=True, help="Dry run.")
@click.option(
    "--targets",
    "-t",
    default=["/"],
    multiple=True,
    help="Specific remote target paths to parse, only used in parse mode, e.g. (also defaults), --targets 2016 --targets 2007/09_Sep",
)
def main(mode, root, parallel, retry, dry_run, targets):
    """
    \b
    GeoNet Strong-Motion Data Downloader
    ====================================

    This script provides an asynchronous command-line tool to mirror and download
    seismic strong-motion "volume-products" from GeoNet
    (https://data.geonet.org.nz/seismic-products/strong-motion/volume-products).

    It supports two primary operations:

    \b
    1. **Parse mode (`parse`)**
        - Recursively crawls the remote directory structure.
        - Recreates the folder hierarchy locally.
        - Saves each directory listing as an ``index.htm`` file.
        - Skips unwanted entries (``/Vol3``, ``/Vol4``, ``/plots``, and file links).
        - Tracks failed requests in ``failed.txt`` for resuming later.

    \b
    2. **Crawl mode (`crawl`)**
        - Reads all locally saved ``index.htm`` files.
        - Extracts strong-motion data files (``.v1a`` and ``.v2a``).
        - Downloads missing files into the mirrored folder structure.
        - Tracks unfinished downloads in ``items.txt`` for resuming later.

    \b
    3. **All mode (`all`, default)**
        - Executes ``parse`` followed by ``crawl``.
    """

    global SEM_LIMIT, RETRY
    SEM_LIMIT = parallel
    RETRY = retry

    if mode not in ("parse", "crawl", "all", "pack"):
        print("Invalid mode, choose from parse, crawl or all.")
        return

    if dry_run:
        print(f"Mode: {mode}")
        print(f"Root path: {root}")
        print(f"Parallel limit: {SEM_LIMIT}")
        print(f"Retry attempts: {RETRY}")
        print(f"Targets: {targets}")
    else:
        if mode == "pack":
            compress(root)
        elif mode == "parse":
            run(parse(root, targets))
        elif mode == "crawl":
            run(crawl(root))
        else:
            run(parse(root, targets))
            run(crawl(root))


if __name__ == "__main__":
    main()
