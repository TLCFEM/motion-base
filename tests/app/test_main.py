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
import os
from http import HTTPStatus

import pytest


async def test_alive(mock_client):
    response = await mock_client.get('/alive')
    assert response.status_code == 200
    assert response.json() == {'message': 'I\'m alive!'}


@pytest.mark.parametrize('file_name,status', [
    pytest.param('jp_test.knt.tar.gz', HTTPStatus.ACCEPTED, id='correct-name'),
    pytest.param('wrong_name', HTTPStatus.ACCEPTED, id='wrong-name')
])
@pytest.mark.parametrize('if_wait', [
    pytest.param('true', id='wait-for-result'),
    pytest.param('false', id='no-wait')
])
async def test_upload_jp(mock_client_superuser, mock_header, pwd, file_name, status, if_wait):
    with open(os.path.join(pwd, 'data/jp_test.knt.tar.gz'), 'rb') as file:
        files = {'archives': (file_name, file, "multipart/form-data")}
        response = await mock_client_superuser.post(
            f'/jp/upload?wait_for_result={if_wait}', files=files, headers=mock_header)
        assert response.status_code == status


@pytest.mark.parametrize('file_name,status', [
    pytest.param('nz_test.tar.gz', HTTPStatus.ACCEPTED, id='correct-name'),
    pytest.param('wrong_name', HTTPStatus.ACCEPTED, id='wrong-name')
])
@pytest.mark.parametrize('if_wait', [
    pytest.param('true', id='wait-for-result'),
    pytest.param('false', id='no-wait')
])
async def test_upload_nz(mock_client_superuser, mock_header, pwd, file_name, status, if_wait):
    with open(os.path.join(pwd, 'data/nz_test.tar.gz'), 'rb') as file:
        files = {'archives': (file_name, file, "multipart/form-data")}
        response = await mock_client_superuser.post(
            f'/nz/upload?wait_for_result={if_wait}', files=files, headers=mock_header)
        assert response.status_code == status


@pytest.mark.parametrize('data_type', [
    pytest.param('raw', id='raw'),
    pytest.param('waveform', id='waveform'),
    pytest.param('spectrum', id='spectrum')
])
async def test_jackpot(mock_client, data_type):
    response = await mock_client.get(f'/{data_type}/jackpot')
    assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize('collection_type', [
    pytest.param('', id='all')
])
async def test_download_nz(mock_client, collection_type):
    target_url = f'/{collection_type}/query' if collection_type != '' else '/query'
    response = await mock_client.post(target_url)
    assert response.status_code == HTTPStatus.OK
