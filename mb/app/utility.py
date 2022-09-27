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

from datetime import datetime, timedelta
from http import HTTPStatus
from typing import Dict
from uuid import NAMESPACE_OID, UUID, uuid4, uuid5

from beanie import Document
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field


class CredentialException(HTTPException):
    def __init__(self):
        super().__init__(
            HTTPStatus.UNAUTHORIZED,
            detail='Could not validate credentials',
            headers={'WWW-Authenticate': 'Bearer'},
        )


class UploadTask(BaseModel):
    task_id: UUID = uuid4()
    total_size: int = 0
    current_size: int = 0

    @property
    def progress(self) -> float:
        return self.current_size / max(1, self.total_size)


class Token(BaseModel):
    access_token: str
    token_type: str


class User(Document):
    id: UUID = Field(default=None)
    username: str
    email: str
    last_name: str
    first_name: str
    hashed_password: str
    disabled: bool
    can_upload: bool
    can_delete: bool

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.id = uuid5(NAMESPACE_OID, self.username)


class UserInformation(BaseModel):
    username: str
    email: str
    last_name: str
    first_name: str
    can_upload: bool
    can_delete: bool


async def create_superuser():
    await User(
        username='admin',
        email='admin@localhost',
        first_name='Admin',
        last_name='Admin',
        hashed_password=hash_password('admin'),
        disabled=False,
        can_upload=True,
        can_delete=True
    ).save()


async def authenticate_user(username: str, password: str):
    user = await User.find_one(User.username == username)
    if not user or not verify_password(password, user.hashed_password):
        return False
    return user


crypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


def verify_password(plain_password, hashed_password):
    return crypt_context.verify(plain_password, hashed_password)


def hash_password(password):
    return crypt_context.hash(password)


OAUTH2 = OAuth2PasswordBearer(tokenUrl='token')

SECRET_KEY = '09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7'
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 120


def create_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    to_encode.update({'exp': datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=15))})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def current_user(token: str = Depends(OAUTH2)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get('sub')
        if username is None:
            raise CredentialException()
    except JWTError as e:
        raise CredentialException() from e
    user = await User.find_one(User.username == username)
    if user is None:
        raise CredentialException()
    return user


async def is_active(user: User = Depends(current_user)):
    if user.disabled:
        raise HTTPException(HTTPStatus.BAD_REQUEST, detail='Inactive user')
    return user


async def send_notification(mail: dict):  # pylint: disable=W0613
    pass


background_tasks: Dict[UUID, UploadTask] = {}
