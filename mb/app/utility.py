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
import os
import re
from datetime import datetime, timedelta
from http import HTTPStatus
from uuid import NAMESPACE_OID, UUID, uuid4, uuid5

from beanie import Document
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
# noinspection PyPackageRequirements
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


class UploadTask(Document):
    id: UUID = Field(default_factory=uuid4)
    total_size: int = 0
    current_size: int = 0

    @property
    def progress(self) -> float:
        return self.current_size / max(1, self.total_size)


class Token(BaseModel):
    access_token: str
    token_type: str


class UserInformation(Document):
    username: str
    email: str
    last_name: str
    first_name: str
    can_upload: bool
    can_delete: bool


class User(UserInformation):
    id: UUID = Field(default=None)
    hashed_password: str
    disabled: bool

    def __init__(self, *args, **data):
        super().__init__(*args, **data)
        self.id = uuid5(NAMESPACE_OID, self.username)


crypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


async def create_superuser():
    await User(
        username=os.getenv('SUPERUSER_USERNAME'),
        email=os.getenv('SUPERUSER_EMAIL'),
        first_name=os.getenv('SUPERUSER_FIRST_NAME'),
        last_name=os.getenv('SUPERUSER_LAST_NAME'),
        hashed_password=crypt_context.hash(os.getenv('SUPERUSER_PASSWORD')),
        disabled=False,
        can_upload=True,
        can_delete=True
    ).save()


async def authenticate_user(username: str, password: str):
    user = await User.find_one(User.username == username)
    if not user or not crypt_context.verify(password, user.hashed_password):
        return False
    return user


OAUTH2 = OAuth2PasswordBearer(tokenUrl='token')

SECRET_KEY = os.getenv('SECRET_KEY')
ALGORITHM = os.getenv('ALGORITHM', 'HS256')
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '30'))


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


# noinspection PyUnusedLocal
async def send_notification(mail: dict):  # pylint: disable=W0613
    pass


async def create_task():
    task = UploadTask()
    await task.save()
    return task.id


def match_uuid(uuid_string: str):
    uuid_regex = re.compile(r'[a-zA-Z0-9]{8}-([a-zA-Z0-9]{4}-){3}[a-zA-Z0-9]{12}')
    return uuid_regex.match(uuid_string) is not None
