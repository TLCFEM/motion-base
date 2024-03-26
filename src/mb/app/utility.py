#  Copyright (C) 2022-2024 Theodore Chang
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

import re
from datetime import datetime, timedelta
from http import HTTPStatus
from uuid import NAMESPACE_OID, UUID, uuid5

from beanie import Document
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt  # noqa
from passlib.context import CryptContext
from pydantic import BaseModel, Field

from mb.utility.env import (
    MB_ACCESS_TOKEN_EXPIRE_MINUTES,
    MB_ALGORITHM,
    MB_SECRET_KEY,
    MB_SUPERUSER_EMAIL,
    MB_SUPERUSER_FIRST_NAME,
    MB_SUPERUSER_LAST_NAME,
    MB_SUPERUSER_PASSWORD,
    MB_SUPERUSER_USERNAME,
)


class CredentialException(HTTPException):
    def __init__(self):
        super().__init__(
            HTTPStatus.UNAUTHORIZED,
            detail="Could not validate credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )


class Token(BaseModel):
    access_token: str
    token_type: str


class UserInformation(Document):
    id: UUID = Field(default=None)
    username: str
    email: str
    last_name: str
    first_name: str
    can_upload: bool
    can_delete: bool

    def __init__(self, *args, **data):
        super().__init__(*args, **data)
        self.id = uuid5(NAMESPACE_OID, self.username)


class User(UserInformation):
    hashed_password: str
    disabled: bool


crypt_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")


async def create_superuser():
    await User(
        username=MB_SUPERUSER_USERNAME,
        email=MB_SUPERUSER_EMAIL,
        first_name=MB_SUPERUSER_FIRST_NAME,
        last_name=MB_SUPERUSER_LAST_NAME,
        hashed_password=crypt_context.hash(MB_SUPERUSER_PASSWORD),
        disabled=False,
        can_upload=True,
        can_delete=True,
    ).save()


async def authenticate_user(username: str, password: str):
    user = await User.find_one(User.username == username)
    return user if user and crypt_context.verify(password, user.hashed_password) else False


OAUTH2 = OAuth2PasswordBearer(tokenUrl="token")


def create_token(sub: str):
    return Token(
        access_token=jwt.encode(
            {"sub": sub, "exp": datetime.utcnow() + timedelta(minutes=MB_ACCESS_TOKEN_EXPIRE_MINUTES)},
            MB_SECRET_KEY,
            algorithm=MB_ALGORITHM,
        ),
        token_type="bearer",
    )


async def current_user(token: str = Depends(OAUTH2)):
    try:
        payload = jwt.decode(token, MB_SECRET_KEY, algorithms=[MB_ALGORITHM])
        if (username := payload.get("sub")) is None:
            raise CredentialException()
    except JWTError as e:
        raise CredentialException() from e
    if (user := await User.find_one(User.username == username)) is None:
        raise CredentialException()
    return user


async def is_active(user: User = Depends(current_user)):
    if user.disabled:
        raise HTTPException(HTTPStatus.BAD_REQUEST, detail="Inactive user.")
    return user


# noinspection PyUnusedLocal
async def send_notification(mail: dict):  # pylint: disable=W0613
    pass


uuid_regex = re.compile(r"[a-zA-Z0-9]{8}-([a-zA-Z0-9]{4}-){3}[a-zA-Z0-9]{12}")


def match_uuid(uuid_string: str):
    return uuid_regex.match(uuid_string) is not None
