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
from __future__ import annotations

import os.path
import uuid
from http import HTTPStatus

import anyio
import httpx
import matplotlib.pyplot as plt
import numpy as np
from httpx_auth import OAuth2ResourceOwnerPasswordCredentials
from rich.console import Console
from rich.progress import track

from mb.app.response import QueryConfig, RecordResponse
from mb.record.response_spectrum import response_spectrum
from mb.record.utility import apply_filter, zero_stuff


class MBRecord(RecordResponse):
    def filter(self, window, upsampling: int = 1):
        new_waveform: np.ndarray = apply_filter(window * upsampling, zero_stuff(upsampling, self.waveform))
        self.time_interval /= upsampling
        # noinspection PyTypeChecker
        self.waveform = new_waveform.tolist()

    def plot_waveform(self):
        fig = plt.figure()
        x_axis = np.arange(0, self.time_interval * len(self.waveform), self.time_interval)
        plt.plot(x_axis, self.waveform)
        plt.title(f"{self.id}")
        plt.xlabel("Time (s)")
        plt.ylabel("Acceleration (Gal)")
        fig.tight_layout()
        return fig

    def plot_spectrum(self):
        if self.frequency_interval is None or self.spectrum is None:
            self.to_spectrum()

        fig = plt.figure()
        x_axis = np.arange(0, self.frequency_interval * len(self.spectrum), self.frequency_interval)
        plt.plot(x_axis, self.spectrum)
        plt.title(f"{self.id}")
        plt.xlabel("Frequency (Hz)")
        plt.ylabel("Acceleration Magnitude (Gal)")
        fig.tight_layout()
        return fig

    def plot_response_spectrum(self):
        if None in (self.period, self.displacement_spectrum, self.velocity_spectrum, self.acceleration_spectrum):
            self.to_response_spectrum(0.05, np.arange(0, 10, 0.01))

        fig = plt.figure()
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

    def to_spectrum(self):
        if self.time_interval is None or self.waveform is None:
            raise RuntimeError("Cannot convert to spectrum.")

        self.frequency_interval = 1 / (self.time_interval * len(self.waveform))
        self.spectrum = 2 * np.abs(np.fft.rfft(self.waveform)) / len(self.waveform)

    def to_response_spectrum(self, damping_ratio: float, period: list[float] | np.ndarray):
        if isinstance(period, np.ndarray):
            # noinspection PyTypeChecker
            self.period = period.tolist()
            spectra = response_spectrum(damping_ratio, self.time_interval, np.array(self.waveform), period)
        else:
            self.period = period
            spectra = response_spectrum(
                damping_ratio, self.time_interval, np.array(self.waveform), np.array(self.period)
            )
        self.displacement_spectrum = spectra[:, 0].tolist()
        self.velocity_spectrum = spectra[:, 1].tolist()
        self.acceleration_spectrum = spectra[:, 2].tolist()

    def print(self):
        Console().print(self)


class MBClient:
    def __init__(self, host_url: str | None = None, username: str | None = None, password: str | None = None, **kwargs):
        self.host_url = host_url if host_url else "http://localhost:8000"
        self.username = username
        self.password = password
        self.auth: OAuth2ResourceOwnerPasswordCredentials | None = (
            OAuth2ResourceOwnerPasswordCredentials(
                f"{self.host_url}/token",
                username=self.username,
                password=self.password,
            )
            if self.username and self.password
            else None
        )

        self.console = Console()

        kwargs["base_url"] = self.host_url
        if "timeout" not in kwargs:
            kwargs["timeout"] = 60

        self.semaphore = anyio.Semaphore(kwargs.pop("semaphore", 10))

        self.client = httpx.AsyncClient(**kwargs)
        self.tasks: dict[str, float] = {}

        self.upload_size = 0
        self.download_size = 0
        self.current_upload_size = 0
        self.current_download_size = 0

        self.download_pool: list = []

    async def __aenter__(self) -> MBClient:
        result = await self.client.get("/alive")
        if result.status_code != HTTPStatus.OK:
            raise RuntimeError("Server is not reachable.")

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    def print(self, *args, **kwargs):
        self.console.print(*args, **kwargs)

    async def download(self, record_id: str | uuid | list[str | uuid], normalised: bool = False):
        if isinstance(record_id, list):
            self.download_pool = []
            self.download_size = len(record_id)
            self.current_download_size = 0
            async with anyio.create_task_group() as tg:
                for r in record_id:
                    tg.start_soon(self.download, r, normalised)

            return

        async with self.semaphore:
            self.current_download_size += 1
            result = await self.client.post(f"/waveform?normalised={str(normalised).lower()}", json=[str(record_id)])
            if result.status_code != HTTPStatus.OK:
                return

            record = MBRecord(**result.json()["records"][0])
            self.download_pool.append(record)
            self.print(
                f"Successfully downloaded file [green]{record.file_name}[/]. "
                f"[[red]{self.current_download_size}/1[/]]."
            )

    async def upload(self, region: str, path: str):
        if os.path.isdir(path):
            file_list: list[str] = []
            for root, _, files in os.walk(path):
                file_list.extend(os.path.join(root, f) for f in files if f.endswith(".tar.gz"))
            self.upload_size = len(file_list)
            self.current_upload_size = 0
            async with anyio.create_task_group() as tg:
                for file in file_list:
                    tg.start_soon(self.upload, region, file)

            return

        if not path.endswith(".tar.gz"):
            return

        base_name = os.path.basename(path)
        async with self.semaphore:
            with open(path, "rb") as file:
                result = await self.client.post(
                    f"/{region}/upload?wait_for_result=false",
                    files={"archives": (base_name, file, "multipart/form-data")},
                    auth=self.auth,
                )
                if result.status_code != HTTPStatus.ACCEPTED:
                    raise RuntimeError("Failed to upload.")
            self.current_upload_size += 1
            self.print(
                f"Successfully uploaded file [green]{base_name}[/]. "
                f"[[red]{self.current_upload_size}/{self.upload_size}[/]]."
            )
            for task_id in result.json()["task_ids"]:
                self.tasks[task_id] = 0

    async def jackpot(self) -> MBRecord | None:
        result = await self.client.get("/waveform/jackpot")
        if result.status_code != HTTPStatus.OK:
            self.print("[red]Failed to get jackpot waveform.[/]")
            return None

        return MBRecord(**result.json())

    async def search(self, query: QueryConfig) -> list[MBRecord] | None:
        result = await self.client.post("/query", json=query.dict())
        if result.status_code != HTTPStatus.OK:
            self.print("[red]Failed to perform query.[/]")
            return None

        return [MBRecord(**r) for r in result.json()["records"]]

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
            for task_id in track(list(self.tasks.keys()), description="Checking status...", console=self.console):
                await self.task_status(task_id)
            await anyio.sleep(2)


async def main():
    async with MBClient("http://localhost:8000", "admin", "admin") as client:
        for _ in range(5):
            result = await client.jackpot()
            fig = result.plot_spectrum()
            fig.show()
        # await client.upload('jp', '/home/theodore/Downloads/ESR')
        # await client.status()
        # await anyio.sleep(10)
        # await client.status()
        # await client.download("fb0e7337-cd32-49ff-966d-1d43c3f1c635")
        # result = await client.search(QueryConfig())
        # for r in result:
        #     r.print()


if __name__ == "__main__":
    anyio.run(main)
