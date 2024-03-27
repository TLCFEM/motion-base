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

from http import HTTPStatus

from fastapi import Depends, HTTPException, APIRouter
from fastapi.security import OAuth2PasswordRequestForm

from mb.app.utility import Token, authenticate_user, create_token, UserForm, User, UserInformation, is_active

router = APIRouter(tags=["account"])


@router.post("/token", status_code=HTTPStatus.OK, response_model=Token)
async def acquire_token(form_data: OAuth2PasswordRequestForm = Depends()):
    if not (user := await authenticate_user(form_data.username, form_data.password)):
        raise HTTPException(
            HTTPStatus.UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return create_token(user.username)


@router.post("/new", status_code=HTTPStatus.OK)
async def create_new_user(form_data: UserForm):
    if await User.find_one(User.username == form_data.username):
        raise HTTPException(HTTPStatus.CONFLICT, detail="Username already exists.")

    await form_data.create_user().save()

    return {"message": "User created."}


@router.get("/whoami", response_model=UserInformation)
async def retrieve_myself(user: User = Depends(is_active)):
    return UserInformation(**user.dict())
