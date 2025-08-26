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


task_pool = set()
pending_pool = set()
total = 0
counter = 0


async def _fetch_file(
    pack: tuple[Path, str, str], client: ClientSession, semaphore: Semaphore
):
    global counter

    file_folder, url_path, file_name = pack

    file_path = file_folder / file_name
    if file_path.exists() and file_path.stat().st_size > 0:
        counter += 1
        return

    async with semaphore:
        counter += 1
        full_url = f"{BASE}{url_path}/{file_name}"
        print(f"{datetime.now()} {counter}/{total} Downloading {full_url}")
        try:
            async with client.get(full_url, auth=BasicAuth(USER, PASS)) as response:
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
                        file_name = link.get("href")  # type: ignore
                        if file_name.endswith(".tar.gz"):  # type: ignore
                            file.write(f"{index.parent},{url_path},{file_name}\n")

    with open(root_list) as file:
        for line in file:
            folder, url_path, file_name = line.strip().split(",")
            task_pool.add((Path(folder), url_path, file_name))

    local_retry = RETRY
    while task_pool and local_retry > 0:
        local_retry -= 1
        await _crawl_once()

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
            response_content = await response.read()
        contents = BeautifulSoup(response_content, "html.parser")
        if contents.find("title").text == "500 Internal Server Error":  # type: ignore
            print(f">>> 500 Error: {remote}")
            pending_pool.add((local, remote))
            return

        pending_pool.discard((local, remote))
        local.mkdir(parents=True, exist_ok=True)
        with open(local / "index.htm", "wb") as file:
            file.write(response_content)
        for link in contents.find_all("a"):
            href = link.get("href")  # type: ignore
            if not href.startswith(("?", "/")) and "." not in href:  # type: ignore
                children.append(href.rstrip("/"))

    await gather(
        *[
            _parse_next(local / child, f"{remote}{child}/", client, semaphore)
            for child in children
        ]
    )


async def parse(local: Path):
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
        for x in ("kik/alldata/", "knet/alldata/"):
            pending_pool.add((local / x, f"{BASE}/kyoshin/download/{x}"))

    semaphore = Semaphore(SEM_LIMIT)
    async with ClientSession() as client:
        await gather(*[_parse_next(x, y, client, semaphore) for x, y in pending_pool])

    with open(failed_file, "w") as file:
        for local_path, remote_url in pending_pool:
            file.write(f"{local_path},{remote_url}\n")


@click.command()
@click.argument("mode", type=str)
@click.argument("username", type=str)
@click.argument("password", type=str)
@click.option("--root", default=Path.cwd() / "NIED", type=Path, help="Root folder.")
@click.option("--parallel", default=10, type=int, help="Number of concurrent requests.")
@click.option("--retry", default=3, type=int, help="Number of retry attempts.")
@click.option("--dry-run", default=False, is_flag=True, help="Dry run.")
def main(mode, username, password, root, parallel, retry, dry_run):
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
    else:
        if mode == "parse":
            run(parse(root))
        elif mode == "crawl":
            run(crawl(root))
        else:
            run(parse(root))
            run(crawl(root))


if __name__ == "__main__":
    main()
