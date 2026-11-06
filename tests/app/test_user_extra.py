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

from datetime import UTC, datetime, timedelta
from http import HTTPStatus

from joserfc import jwt

from mb.app.utility import (
    MB_ALGORITHM,
    OCT_KEY,
    User,
    bcrypt_hash,
    bcrypt_verify,
    create_superuser,
)
from mb.record.utility import uuid5_str


async def _create_user(
    username: str,
    *,
    password: str = "Test!1234",
    email: str | None = None,
    disabled: bool = False,
    can_upload: bool = True,
    can_delete: bool = True,
) -> User:
    user = User(
        username=username,
        email=email or f"{username}@example.com",
        last_name="test",
        first_name="test",
        hashed_password=bcrypt_hash(password),
        disabled=disabled,
        can_upload=can_upload,
        can_delete=can_delete,
    )
    await user.save()
    return user


async def test_bcrypt_helpers():
    hashed = bcrypt_hash("Test!1234")

    assert bcrypt_verify("Test!1234", hashed)
    assert not bcrypt_verify("wrong", hashed)


async def test_login_and_whoami(mock_client, mongo_connection):
    await _create_user("alice")

    response = await mock_client.post(
        "/user/token", data={"username": "alice", "password": "Test!1234"}
    )
    assert response.status_code == HTTPStatus.OK
    token = response.json()["access_token"]

    response = await mock_client.get(
        "/user/whoami", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == HTTPStatus.OK
    assert response.json()["username"] == "alice"


async def test_login_failure(mock_client, mongo_connection):
    await _create_user("alice")

    response = await mock_client.post(
        "/user/token", data={"username": "alice", "password": "wrong"}
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


async def test_invalid_and_subless_tokens(mock_client, mongo_connection):
    response = await mock_client.get(
        "/user/whoami", headers={"Authorization": "Bearer invalid"}
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED

    token = jwt.encode(
        {"alg": MB_ALGORITHM},
        {"exp": datetime.now(UTC) + timedelta(minutes=5)},
        OCT_KEY,
    )
    response = await mock_client.get(
        "/user/whoami", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == HTTPStatus.UNAUTHORIZED


async def test_disabled_user(mock_client, mongo_connection):
    await _create_user("alice", disabled=True)

    response = await mock_client.post(
        "/user/token", data={"username": "alice", "password": "Test!1234"}
    )
    token = response.json()["access_token"]

    response = await mock_client.get(
        "/user/whoami", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST


async def test_non_admin_cannot_manage_users(mock_client, mongo_connection):
    await _create_user("alice", can_upload=False, can_delete=False)

    response = await mock_client.post(
        "/user/token", data={"username": "alice", "password": "Test!1234"}
    )
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    response = await mock_client.post(
        "/user/new",
        headers=headers,
        json={
            "username": "bob",
            "password": "Test!1234",
            "email": "bob@example.com",
            "last_name": "b",
            "first_name": "b",
        },
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST

    response = await mock_client.delete(
        f"/user/{uuid5_str('bob')}", headers=headers
    )
    assert response.status_code == HTTPStatus.BAD_REQUEST


async def test_check_user_availability(mock_client, mongo_connection):
    response = await mock_client.post(
        "/user/check",
        json={"username": "alice", "email": "alice@example.com"},
    )
    assert response.status_code == HTTPStatus.OK

    await _create_user("alice")

    response = await mock_client.post(
        "/user/check",
        json={"username": "alice", "email": "another@example.com"},
    )
    assert response.status_code == HTTPStatus.CONFLICT

    response = await mock_client.post(
        "/user/check",
        json={"username": "another", "email": "alice@example.com"},
    )
    assert response.status_code == HTTPStatus.CONFLICT


async def test_create_user_conflicts(mock_client_superuser, mongo_connection):
    await _create_user("alice")

    response = await mock_client_superuser.post(
        "/user/new",
        json={
            "username": "alice",
            "password": "Test!1234",
            "email": "another@example.com",
            "last_name": "a",
            "first_name": "a",
        },
    )
    assert response.status_code == HTTPStatus.CONFLICT

    response = await mock_client_superuser.post(
        "/user/new",
        json={
            "username": "another",
            "password": "Test!1234",
            "email": "alice@example.com",
            "last_name": "a",
            "first_name": "a",
        },
    )
    assert response.status_code == HTTPStatus.CONFLICT


async def test_delete_missing_user(mock_client_superuser):
    response = await mock_client_superuser.delete(f"/user/{uuid5_str('missing')}")

    assert response.status_code == HTTPStatus.OK


async def test_create_superuser(mongo_connection):
    await create_superuser()

    user = await User.find_one(User.username == "test")
    assert user is not None
    assert user.can_upload
    assert user.can_delete
