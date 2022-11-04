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
        username=os.getenv('SUPERUSER_USERNAME'),
        email=os.getenv('SUPERUSER_EMAIL'),
        first_name=os.getenv('SUPERUSER_FIRST_NAME'),
        last_name=os.getenv('SUPERUSER_LAST_NAME'),
        hashed_password=hash_password(os.getenv('SUPERUSER_PASSWORD')),
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


class QueryConfig(BaseModel):
    region: str | None = None
    min_magnitude: float | None = None
    max_magnitude: float | None = None
    sub_category: str | None = None
    event_location: list | None = None
    station_location: list | None = None
    max_event_distance: float | None = None
    max_station_distance: float | None = None
    from_date: datetime | None = None
    to_date: datetime | None = None
    min_pga: float | None = None
    max_pga: float | None = None
    event_name: str | None = None
    direction: str | None = None
    page_size: int = 10
    page_number: int = 0

    def generate_query_string(self) -> dict:
        query_dict: dict = {'$and': []}

        magnitude: dict = {}
        if self.min_magnitude is not None:
            magnitude['$gte'] = self.min_magnitude
        if self.max_magnitude is not None:
            magnitude['$lte'] = self.max_magnitude
        if magnitude:
            query_dict['$and'].append({'magnitude': magnitude})

        if self.sub_category is not None:
            query_dict['$and'].append({'sub_category': self.sub_category.lower()})

        if self.event_location is not None:
            query_dict['event_location'] = {'$nearSphere': self.event_location}
            if self.max_event_distance is not None:
                query_dict['event_location']['$maxDistance'] = self.max_event_distance / 6371

        if self.station_location is not None:
            query_dict['station_location'] = {'$nearSphere': self.station_location}
            if self.max_station_distance is not None:
                query_dict['station_location']['$maxDistance'] = self.max_station_distance / 6371

        date_range: dict = {}
        if self.from_date is not None:
            date_range['$gte'] = self.from_date
        if self.to_date is not None:
            date_range['$lte'] = self.to_date
        if date_range:
            query_dict['$and'].append({'origin_time': date_range})

        pga: dict = {}
        if self.min_pga is not None:
            pga['$gte'] = self.min_pga
        if self.max_pga is not None:
            pga['$lte'] = self.max_pga
        if pga:
            query_dict['$and'].append({'maximum_acceleration': pga})

        if self.direction is not None:
            query_dict['$and'].append({'direction': {'$regex': self.direction, '$options': 'i'}})

        if self.event_name is not None:
            query_dict['$and'].append({'file_name': {'$regex': self.event_name, '$options': 'i'}})

        if not query_dict['$and']:
            del query_dict['$and']

        return query_dict
