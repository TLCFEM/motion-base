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
from httpx_auth import OAuth2ResourceOwnerPasswordCredentials

from mb.record.record import Record


class MBClient:
    def __init__(self, host_url: str | None = None, username: str | None = None, password: str | None = None, **kwargs):
        self.host_url = host_url if host_url else 'http://localhost:8000'
        self.username = username
        self.password = password
        self.auth: OAuth2ResourceOwnerPasswordCredentials | None = None

        if self.username and self.password:
            self.client = httpx.AsyncClient(base_url=self.host_url, auth=(self.username, self.password), **kwargs)
        else:
            self.client = httpx.AsyncClient(base_url=self.host_url, **kwargs)

    async def __aenter__(self) -> MBClient:
        result = await self.client.get('/alive')
        if result.status_code != HTTPStatus.OK:
            raise RuntimeError('Server is not reachable.')

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def login(self):
        if not self.username or not self.password:
            return

        self.auth = OAuth2ResourceOwnerPasswordCredentials(
            f'{self.host_url}/token',
            username=self.username,
            password=self.password,
        )

    async def jackpot(self, region: str) -> Record:
        if region not in ('jp', 'nz'):
            raise ValueError('Region not supported.')

        result = await self.client.get(f'/{region}/waveform/jackpot')
        if result.status_code != HTTPStatus.OK:
            raise RuntimeError('Failed to get jackpot.')

        return result.json()

    async def upload(self, region: str, path: str):
        if not self.auth:
            await self.login()

        if path.endswith('.tar.gz'):
            with open(path, 'rb') as file:
                result = await self.client.post(
                    f'/{region}/upload?wait_for_result=false',
                    files={'archives': (os.path.basename(path), file, 'multipart/form-data')},
                    auth=self.auth)
                if result.status_code != HTTPStatus.ACCEPTED:
                    raise RuntimeError('Failed to upload.')

        return result.json()


async def main():
    async with MBClient('http://localhost:8000', 'admin', 'admin') as client:
        await client.login()
        await client.jackpot('jp')
        upload_result = await client.upload('jp', '/home/theodore/Downloads/20050816114600.knt.tar.gz')
        print(upload_result)


if __name__ == '__main__':
    anyio.run(main)
