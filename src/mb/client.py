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

import os.path
import uuid
from collections.abc import Generator
from http import HTTPStatus

import anyio
import httpx
import matplotlib.pyplot as plt
import numpy as np
from httpx_auth import OAuth2ResourceOwnerPasswordCredentials as OAuth2
from matplotlib.figure import Figure
from rich.console import Console
from rich.progress import track

from mb.app.response import PaginationConfig, QueryConfig, RecordResponse


class MBRecord(RecordResponse):
    @staticmethod
    def new_record(data: dict):
        return MBRecord(**{k: v for k, v in data.items() if v is not None})

    def plot_waveform(self, fig: Figure | None = None):
        if fig is None:
            fig = plt.figure(figsize=(10, 6), dpi=100)
            gca = fig.add_subplot(111)
            gca.set_xlabel("Time (s)")
            gca.set_ylabel(f"Acceleration Magnitude ({self.processed_data_unit})")
        else:
            gca = fig.gca()

        x_axis = np.arange(
            0, self.time_interval * len(self.waveform), self.time_interval
        )
        gca.plot(x_axis, self.waveform, label=self.id)

        fig.tight_layout()
        return fig

    def plot_spectrum(self, fig: Figure | None = None):
        self.to_spectrum()

        if fig is None:
            fig = plt.figure(figsize=(10, 6), dpi=100)
            gca = fig.add_subplot(111)
            gca.set_xlabel("Frequency (Hz)")
            gca.set_ylabel(f"Acceleration Magnitude ({self.processed_data_unit})")
        else:
            gca = fig.gca()

        x_axis = np.arange(
            0, self.frequency_interval * len(self.spectrum), self.frequency_interval
        )
        gca.plot(x_axis, self.spectrum, label=self.id)

        fig.tight_layout()
        return fig

    def plot_response_spectrum(
        self,
        damping_ratio: float = 0.05,
        period_bracket: np.ndarray = np.arange(0, 10, 0.01),
    ):
        self.to_response_spectrum(damping_ratio, period_bracket)

        fig = plt.figure(figsize=(10, 6), dpi=100)
        fig.add_subplot(311)
        plt.title(f"{self.id}")
        plt.plot(self.period, self.displacement_spectrum)
        plt.xlabel("Period (s)")
        plt.ylabel("SD")
        fig.add_subplot(312)
        plt.plot(self.period, self.velocity_spectrum)
        plt.xlabel("Period (s)")
        plt.ylabel("SV")
        fig.add_subplot(313)
        plt.plot(self.period, self.acceleration_spectrum)
        plt.xlabel("Period (s)")
        plt.ylabel("SA")
        fig.tight_layout()
        return fig

    def print(self):
        Console().print(self)


class MBClient:
    def __init__(
        self,
        host_url: str | None = None,
        username: str | None = None,
        password: str | None = None,
        **kwargs,
    ):
        """
        To create a new instance, provide the `host_url` such as `http://localhost:8000`.
        Apart from uploading new records, no need to assign `username` and `password`.
        Provide `semaphore` to limit the number of concurrent requests.

        All other keyword arguments are passed to `httpx.AsyncClient`.
        For example, to set a timeout of 10 seconds, use `timeout=10`.

        :param host_url: The URL of the server.
        :param username: The username for authentication.
        :param password: The password for authentication.
        :param kwargs: Additional arguments for `httpx.AsyncClient`.
        """
        self.host_url: str = host_url if host_url else "http://localhost:8000"
        while self.host_url.endswith("/"):
            self.host_url = self.host_url[:-1]
        self.username: str | None = username
        self.password: str | None = password
        self.auth: OAuth2 | None = (
            OAuth2(
                f"{self.host_url}/user/token",
                username=self.username,
                password=self.password,
            )
            if self.username and self.password
            else None
        )

        self.console = Console()

        kwargs["base_url"] = self.host_url
        if "timeout" not in kwargs:
            kwargs["timeout"] = None

        self.semaphore = anyio.Semaphore(kwargs.pop("semaphore", 10))

        self.client = httpx.AsyncClient(**kwargs)
        self.tasks: dict[str, float] = {}

        self.upload_size: int = 0
        self.download_size: int = 0
        self.current_upload_size: int = 0
        self.current_download_size: int = 0

        self.download_pool: list = []

    async def __aenter__(self) -> MBClient:
        if (await self.client.get("/alive")).status_code != HTTPStatus.OK:
            raise RuntimeError("Server is not reachable.")

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    def __iter__(self):
        return self.download_pool.__iter__()

    def __len__(self):
        return self.download_pool.__len__()

    def clear(self):
        self.download_pool.clear()
        self.download_size = 0
        self.current_download_size = 0

    def print(self, *args, **kwargs):
        self.console.print(*args, **kwargs)

    async def download(
        self,
        record: str | uuid.UUID | list[str | uuid.UUID] | MBRecord | list[MBRecord],
    ):
        if isinstance(record, list):
            self.download_size += len(record)
            async with anyio.create_task_group() as tg:
                for r in record:
                    tg.start_soon(self.download, r)
        else:
            record_id: str | uuid.UUID = (
                record.id if isinstance(record, MBRecord) else record
            )

            async with self.semaphore:
                result = await self.client.post("/waveform", json=[str(record_id)])
                self.current_download_size += 1
                if result.status_code != HTTPStatus.OK:
                    self.print(
                        f"Fail to download file [green]{record_id}[/]. "
                        f"[[red]{self.current_download_size}/{self.download_size}[/]]."
                    )
                else:
                    self.download_pool.append(
                        MBRecord.new_record(result.json()["records"][0])
                    )
                    self.print(
                        f"Successfully downloaded file [green]{record_id}[/]. "
                        f"[[red]{self.current_download_size}/{self.download_size}[/]]."
                    )

        return self

    @staticmethod
    async def _retry(
        fn,
        retries: int = 3,
        delay: float = 1,
        backoff: float = 2,
        exceptions=(Exception,),
    ):
        attempt: int = 0
        while True:
            try:
                return await fn()
            except exceptions:
                attempt += 1
                if attempt > retries:
                    raise
                await anyio.sleep(delay)
                delay *= backoff

    async def upload(
        self,
        region: str,
        path: str | Generator,
        wait_for_result: bool = False,
        overwrite_existing: bool = True,
    ):
        if self.auth is None:
            self.print("Upload requires authentication.")
            return

        if isinstance(path, Generator):
            async with anyio.create_task_group() as tg:
                for file in path:
                    tg.start_soon(self.upload, region, file, wait_for_result)
            return

        def _include(file_name: str) -> bool:
            file_name = file_name.lower()
            if file_name.endswith((".tar.gz", ".zip")):
                return True

            return "v1a" in file_name or "v2a" in file_name

        if os.path.isdir(path):
            file_list: list[str] = []
            for root, _, files in os.walk(path):
                file_list.extend(os.path.join(root, f) for f in files if _include(f))
            self.upload_size = len(file_list)
            self.current_upload_size = 0
            async with anyio.create_task_group() as tg:
                for file in file_list:
                    tg.start_soon(self.upload, region, file, wait_for_result)

            return

        if not _include(path) or not os.path.exists(path):
            if self.upload_size > 0:
                self.current_upload_size += 1
            return

        base_name = os.path.basename(path)

        async with self.semaphore:
            with open(path, "rb") as file:

                async def _post():
                    return await self.client.post(
                        f"/{region}/upload"
                        f"?wait_for_result={'true' if wait_for_result else 'false'}"
                        f"&overwrite_existing={'true' if overwrite_existing else 'false'}",
                        files={"archives": (base_name, file, "multipart/form-data")},
                        auth=self.auth,
                    )

                result = await self._retry(_post)
                if result.status_code != HTTPStatus.ACCEPTED:
                    raise RuntimeError("Failed to upload.")

            if self.upload_size > 0:
                self.current_upload_size += 1
                self.print(
                    f"Successfully uploaded file [green]{base_name}[/]. "
                    f"[[red]{self.current_upload_size}/{self.upload_size}[/]]."
                )
            else:
                self.print(f"Successfully uploaded file [green]{base_name}[/].")

            for task_id in result.json()["task_ids"]:
                self.tasks[task_id] = 0

    async def jackpot(self) -> MBRecord | None:
        result = await self.client.get("/waveform/jackpot")
        if result.status_code != HTTPStatus.OK:
            self.print("[red]Failed to get jackpot waveform.[/]")
            return None

        return MBRecord.new_record(result.json())

    async def search(self, query: QueryConfig | dict) -> list[MBRecord] | None:
        result = await self.client.post(
            "/query",
            json=query.model_dump(exclude_none=True)
            if isinstance(query, QueryConfig)
            else query,
        )
        if result.status_code != HTTPStatus.OK:
            self.print("[red]Failed to perform query.[/]")
            return None

        return [MBRecord.new_record(r) for r in result.json()["records"]]

    async def retrieve_all(self, query: QueryConfig | dict):
        search_after = None
        json_query = (
            query.model_dump(exclude_none=True)
            if isinstance(query, QueryConfig)
            else query
        )
        while True:
            if search_after is not None:
                json_query["pagination"]["search_after"] = search_after
            result = await self.client.post("/search", json=json_query)
            if result.status_code != HTTPStatus.OK:
                self.print("[red]Failed to perform query.[/]")
                return

            result_json = result.json()
            search_after = result_json["pagination"]["search_after"]

            if not result_json["records"]:
                return

            for r in result_json["records"]:
                yield MBRecord.new_record(r)

    async def task_status(self, task_id: str):
        result = await self.client.get(f"/task/status/{task_id}")
        if result.status_code != HTTPStatus.OK:
            del self.tasks[task_id]
            return

        response = result.json()
        self.tasks[task_id] = response["current_size"] / max(1, response["total_size"])
        self.print(f"{task_id}: {self.tasks[task_id]:.2%}")

    async def status(self):
        while self.tasks:
            for task_id in track(
                list(self.tasks.keys()),
                description="Checking status...",
                console=self.console,
            ):
                await self.task_status(task_id)
            await anyio.sleep(2)


async def main():
    async with MBClient("https://tlcfem.top:8443", timeout=100) as client:
        counter = 0
        async for _ in client.retrieve_all(
            QueryConfig(
                min_magnitude=6,
                min_pga=300,
                pagination=PaginationConfig(page_size=100),
            )
        ):
            counter += 1

        print(counter)


if __name__ == "__main__":
    anyio.run(main)
