#  Copyright (C) 2022 Theodore Chang
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
from http import HTTPStatus

import anyio
import httpx
import matplotlib.pyplot as plt
import numpy as np
from httpx_auth import OAuth2ResourceOwnerPasswordCredentials
from rich.console import Console

from mb.app.response import SequenceSpectrumResponse


class MBRecord(SequenceSpectrumResponse):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if 'waveform' in self.endpoint:
            self.time_interval = kwargs.get('interval', None)
            self.waveform = kwargs.get('data', None)
        elif 'spectrum' in self.endpoint:
            self.frequency_interval = kwargs.get('interval', None)
            self.spectrum = kwargs.get('data', None)

    def plot_waveform(self):
        fig = plt.figure()
        plt.plot(
            np.arange(0, self.time_interval * len(self.waveform), self.time_interval),
            self.waveform)
        plt.xlabel('Time (s)')
        plt.ylabel('Acceleration (Gal)')
        plt.title(self.file_name)
        fig.tight_layout()
        return fig

    def plot_spectrum(self):
        fig = plt.figure()
        plt.plot(
            np.arange(0, self.frequency_interval * len(self.spectrum), self.frequency_interval),
            self.spectrum)
        plt.xlabel('Frequency (Hz)')
        plt.ylabel('Acceleration Magnitude (Gal)')
        plt.title(self.file_name)
        fig.tight_layout()
        return fig


class MBClient:
    def __init__(self, host_url: str | None = None, username: str | None = None, password: str | None = None, **kwargs):
        self.host_url = host_url if host_url else 'http://localhost:8000'
        self.username = username
        self.password = password
        self.auth: OAuth2ResourceOwnerPasswordCredentials | None = OAuth2ResourceOwnerPasswordCredentials(
            f'{self.host_url}/token',
            username=self.username,
            password=self.password,
        ) if self.username and self.password else None

        self.console = Console()

        kwargs['base_url'] = self.host_url
        kwargs['timeout'] = 60

        self.client = httpx.AsyncClient(**kwargs)
        self.semaphore = anyio.Semaphore(10)
        self.tasks: list[str] = []

    async def __aenter__(self) -> MBClient:
        result = await self.client.get('/alive')
        if result.status_code != HTTPStatus.OK:
            raise RuntimeError('Server is not reachable.')

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    def print(self, *args, **kwargs):
        self.console.print(*args, **kwargs)

    async def jackpot(self, region: str) -> MBRecord:
        if region not in ('jp', 'nz'):
            raise ValueError('Region not supported.')

        result = await self.client.get(f'/{region}/waveform/jackpot')
        if result.status_code != HTTPStatus.OK:
            raise RuntimeError('Failed to get jackpot.')

        return MBRecord(**result.json())

    async def upload(self, region: str, path: str):
        if os.path.isdir(path):
            file_list: list[str] = []
            for root, _, files in os.walk(path):
                file_list.extend(os.path.join(root, file) for file in files if file.endswith('.tar.gz'))

            async with anyio.create_task_group() as tg:
                for file in file_list:
                    tg.start_soon(self.upload, region, file)

            return

        if not path.endswith('.tar.gz'):
            return

        async with self.semaphore:
            with open(path, 'rb') as file:
                result = await self.client.post(
                    f'/{region}/upload?wait_for_result=false',
                    files={'archives': (os.path.basename(path), file, 'multipart/form-data')},
                    auth=self.auth)
                if result.status_code != HTTPStatus.ACCEPTED:
                    raise RuntimeError('Failed to upload.')

            self.print(f'Successfully uploaded file {path}.')
            self.tasks.extend(result.json()['task_id'])

    async def task_status(self, task_id: str):
        result = await self.client.get(f'/task/status/{task_id}')
        if result.status_code != HTTPStatus.OK:
            return

        response = result.json()
        self.print(f'{task_id}: {response["current_size"]}/{response["total_size"]}')

    async def status(self):
        async with anyio.create_task_group() as tg:
            for task_id in self.tasks:
                tg.start_soon(self.task_status, task_id)


async def main():
    async with MBClient('http://localhost:8000', 'admin', 'admin') as client:
        result = await client.jackpot('jp')
        fig = result.plot_waveform()
        fig.show()
        # await client.upload('jp', '/home/theodore/Downloads/ESR')
        # await client.status()
        # await anyio.sleep(10)
        # await client.status()


if __name__ == '__main__':
    anyio.run(main)
