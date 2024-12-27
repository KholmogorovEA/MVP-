
from fastapi import Request, HTTPException, Depends, status
from jose import jwt, JWTError
from app.config import settings
from datetime import datetime
from app.users.dao import UsersDAO
from app.users.models import Users


def get_token(request: Request) -> str:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Token is missing")
    return token


async def get_current_user(token: str = Depends(get_token)):
    # декодируем жвт токен чтобы достать экспирацию и id юзера
    try:

        payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        settings.ALGORITHM 
        )

    except JWTError:
        raise HTTPException(status_code=400)
    
    expire: str = payload.get("exp") # type: ignore
    if (not expire) or (int(expire) < datetime.utcnow().timestamp()):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    user_id: str = payload.get("sub") # type: ignore
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    
    user = await UsersDAO.find_by_id(int(user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    
    return user


