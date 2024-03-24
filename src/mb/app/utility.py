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

import os
import re
from datetime import datetime, timedelta
from http import HTTPStatus
from uuid import NAMESPACE_OID, UUID, uuid4, uuid5

from beanie import Document
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt  # noqa
from passlib.context import CryptContext
from pydantic import BaseModel, Field


class CredentialException(HTTPException):
    def __init__(self):
        super().__init__(
            HTTPStatus.UNAUTHORIZED,
            detail="Could not validate credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )


class UploadTask(Document):
    id: UUID = Field(default_factory=uuid4)
    create_time: datetime = Field(default_factory=datetime.now)
    pid: int = 0
    total_size: int = 0
    current_size: int = 0

    @property
    def progress(self) -> float:
        return self.current_size / max(1, self.total_size)


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
        username=os.getenv("MB_SUPERUSER_USERNAME"),
        email=os.getenv("MB_SUPERUSER_EMAIL"),
        first_name=os.getenv("MB_SUPERUSER_FIRST_NAME"),
        last_name=os.getenv("MB_SUPERUSER_LAST_NAME"),
        hashed_password=crypt_context.hash(os.getenv("MB_SUPERUSER_PASSWORD")),
        disabled=False,
        can_upload=True,
        can_delete=True,
    ).save()


async def authenticate_user(username: str, password: str):
    user = await User.find_one(User.username == username)
    return user if user and crypt_context.verify(password, user.hashed_password) else False


OAUTH2 = OAuth2PasswordBearer(tokenUrl="token")

SECRET_KEY = os.getenv("MB_SECRET_KEY")
ALGORITHM = os.getenv("MB_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("MB_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# if SECRET_KEY is None:
#     raise ValueError("No secret key provided.")


def create_token(sub: str):
    return Token(
        access_token=jwt.encode(
            {"sub": sub, "exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)},
            SECRET_KEY,
            algorithm=ALGORITHM,
        ),
        token_type="bearer",
    )


async def current_user(token: str = Depends(OAUTH2)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
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


async def create_task():
    task = UploadTask()
    await task.save()
    return task.id


uuid_regex = re.compile(r"[a-zA-Z0-9]{8}-([a-zA-Z0-9]{4}-){3}[a-zA-Z0-9]{12}")


def match_uuid(uuid_string: str):
    return uuid_regex.match(uuid_string) is not None
