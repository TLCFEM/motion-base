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


from asyncio import Semaphore, gather, run
from datetime import datetime
from pathlib import Path

import click
from aiohttp import BasicAuth, ClientSession
from bs4 import BeautifulSoup

BASE = "https://www.kyoshin.bosai.go.jp"
USER = ""
PASS = ""
SEM_LIMIT = 50
RETRY = 3
FILE_LIST = (".tar.gz",)


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
        full_url = f"{BASE}{url_path}/{file_name}"
        print(f"{datetime.now()} {counter}/{total} Downloading {full_url}")
        try:
            async with client.get(full_url, auth=BasicAuth(USER, PASS)) as response:
                if not response.ok:
                    return
                content = await response.read()
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
                    url_path = contents.find("title").text.split(" ")[-1]  # type: ignore
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
        async with client.get(remote, auth=BasicAuth(USER, PASS)) as response:
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
            if not href.startswith(("?", "/")) and "." not in href:
                children.append(href.rstrip("/"))

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
                pending_pool.add(
                    (local / x_stripped, f"{BASE}/kyoshin/download/{x_stripped}/")
                )

    await _execute_retry(_parse_once, pending_pool)

    with open(failed_file, "w") as file:
        for local_path, remote_url in pending_pool:
            file.write(f"{local_path},{remote_url}\n")


@click.command()
@click.argument("username", type=str)
@click.argument("password", type=str)
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
    default=Path.cwd() / "NIED",
    type=Path,
    help="Local root folder: where do you want to put the downloaded data? Default is ./NIED",
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
    default=["kik/alldata/", "knet/alldata/"],
    multiple=True,
    help="Specific remote target paths to parse, only used in parse mode, e.g. (also defaults), --targets kik/alldata/ --targets knet/alldata/",
)
def main(mode, username, password, root, parallel, retry, dry_run, targets):
    """
    \b
    NIED Seismic Data Crawling Utility
    ==================================

    This script provides an asynchronous command-line utility for downloading and
    mirroring strong-motion seismograph data from the NIED (https://www.kyoshin.bosai.go.jp)
    service.

    Only *.tar.gz files will be fetched.
    Those files contain waveform data in plain text.
    Binary files cannot be processed thus are not downloaded.
    Modify the FILE_LIST variable in the script to if you want to download other file types.

    \b
    Overview
    --------
    The tool works in two main phases:

    \b
    1. **Parse Mode (`parse`)**
    - Recursively traverses the remote server directory structure.
    - Creates a mirrored local folder tree.
    - Saves `index.htm` files representing remote directory listings.
    - Tracks failed directories in `failed.txt`, allowing resumption or retry.

    \b
    2. **Crawl Mode (`crawl`)**
    - Reads previously saved `index.htm` files.
    - Extracts `.tar.gz` file links and downloads them concurrently.
    - Maintains `items.txt` with a list of download targets.
    - Retries failed downloads up to a configurable number of attempts.

    \b
    3. **All Mode (`all`)**
    - Executes both `parse` and `crawl` phases in sequence.

    \b
    Features
    --------
    - Concurrent requests with configurable limits.
    - Automatic retry of failed downloads/directories.
    - Resumable: failed files/directories are logged and retried on subsequent runs.
    - Interactive prompts to choose between fresh starts or resuming from saved state.

    \b
    Additional Notes
    ----------------

    - **Disclaimer**: The data fetched by this script **may be subject to copyright**.
    This crawler is provided “as-is,” and **no responsibility is accepted** for any
    copyright or usage issues arising from downloading or using these data.

    - **Account Required**: A valid user account is needed to download waveform data
    (registration can be done via the official NIED registration page: https://hinetwww11.bosai.go.jp/nied/registration/).

    - **Rate Limit Considerations**: There may be server-imposed limitations. As of the
    time of writing, using up to 50 concurrent connections appears to be acceptable.
    """

    global USER, PASS, SEM_LIMIT, RETRY
    USER = username
    PASS = password
    SEM_LIMIT = parallel
    RETRY = retry

    if mode not in ("parse", "crawl", "all"):
        print("Invalid mode, choose from parse, crawl or all.")
        return

    if dry_run:
        print(f"Mode: {mode}")
        print(f"Username: {USER}")
        print(f"Password: {'*' * len(PASS)}")
        print(f"Root path: {root}")
        print(f"Parallel limit: {SEM_LIMIT}")
        print(f"Retry attempts: {RETRY}")
        print(f"Targets: {targets}")
    else:
        root.mkdir(parents=True, exist_ok=True)

        if mode == "parse":
            run(parse(root, targets))
        elif mode == "crawl":
            run(crawl(root))
        else:
            run(parse(root, targets))
            run(crawl(root))


if __name__ == "__main__":
    main()
