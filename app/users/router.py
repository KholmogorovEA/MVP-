from fastapi import APIRouter, HTTPException, Request, Response, status, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, EmailStr
from app.users.dependencies import get_current_user
from app.users.models import Users
from app.users.schemas import SUserRegister 
from app.users.dao import UsersDAO
from app.users.auth import get_password_hash, authenticate_user, create_access_token
from typing import List



TEMPLATES_FOLDER = "app/templates"
templates = Jinja2Templates(directory=TEMPLATES_FOLDER)


router = APIRouter(
    prefix="/auth",
    tags=["Регистрация пользователей"],
)



# Маршрут для страницы регистрации
@router.get("/register", response_class=HTMLResponse)
async def registration_page(request: Request):
    return templates.TemplateResponse("auth.html", {"request": request})



# Сделать валидацию проверки корректности номера телефона
class UserResponse(BaseModel):
    email: EmailStr
    password: str
    name: str
    mobile: str



@router.post("/register", response_model=List[UserResponse])
async def register_user(user_data: SUserRegister, request: Request):
    existing_user = await UsersDAO.find_by_one_or_none(email=user_data.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists") 
    hashed_password = get_password_hash(user_data.password)
    await UsersDAO.add(email=user_data.email, hashed_password=hashed_password, name=user_data.name, mobile=user_data.mobile)
    return [
        UserResponse(
            email=user_data.email,
            password=user_data.password,  
            name=user_data.name,
            mobile=user_data.mobile,
        ),
    ]
    


class UserLogin(BaseModel):
    email: str
    password: str


@router.post("/login")
async def login_user(response: Response, user_data: UserLogin) -> str:
    user = await authenticate_user(user_data.email, user_data.password)  # если юзер есть в базе то создаем токен жвт и отправляем ему в куки
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    access_token = create_access_token({"sub": str(user.id)})  # type: ignore
    response.set_cookie("access_token", access_token, httponly=True)  # отправляем токен в куки для дальнейшего использования"booking_access_token", value=access_token, httponly=True)  # отправляем токен в куки для дальнейшего использования
    return access_token



@router.post("/logout")
async def logout_user(response: Response) -> dict[str, str]:
    response.delete_cookie("access_token")  # удаляем токен из куки
    return {"detail": "Logged out"}



@router.get("/me")
async def read_user_me(current_user: Users = Depends(get_current_user)):
    return current_user

