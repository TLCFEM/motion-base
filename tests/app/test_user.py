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

from http import HTTPStatus


async def test_acquire_token(mock_client_superuser):
    response = await mock_client_superuser.post(
        "/user/token", data={"username": "test", "password": "test"}
    )
    assert response.status_code == HTTPStatus.OK


async def test_whoami(mock_client_superuser):
    response = await mock_client_superuser.get("/user/whoami")
    assert response.status_code == HTTPStatus.OK


async def test_user_new(mock_client):
    new_user = {
        "username": "tester1",
        "password": "test!e2zAr",
        "email": "a@b.c",
        "last_name": "a",
        "first_name": "a",
    }

    response = await mock_client.post("/user/new", json=new_user)
    assert response.status_code == HTTPStatus.OK

    response = await mock_client.delete("/user/delete", json=new_user)
    assert response.status_code == HTTPStatus.OK
