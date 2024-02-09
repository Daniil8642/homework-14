from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Body
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from fastapi.openapi.models import OAuthFlowAuthorizationCode
from fastapi.openapi.models import OAuthFlows
from fastapi.openapi.models import OAuthFlowPassword
from fastapi.openapi.models import OAuthFlowRefreshToken
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.orm import Session
from database import get_db
from models import User, Token
from utils import send_reset_password_email, create_access_token
from datetime import datetime, timedelta

router = APIRouter()


@router.post("/token/", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Кінцева точка для входу користувача та генерації токену доступу."""
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not contacts.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невірні облікові дані",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=contacts.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/reset-password/")
def reset_password(email: str, db: Session = Depends(get_db)):
    """Кінцева точка для скидання паролю."""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Користувач не знайдений")

    reset_token = contacts.create_reset_token(data={"sub": user.email})
    send_reset_password_email(email, reset_token)

    return {"message": "Інструкції для скидання паролю відправлені на вашу електронну пошту"}


@router.post("/reset-password/{token}")
def reset_password_confirm(token: str, new_password: str = Body(..., embed=True), db: Session = Depends(get_db)):
    """Кінцева точка для підтвердження скидання паролю."""
    email = contacts.verify_reset_token(token)
    if email is None:
        raise HTTPException(status_code=400, detail="Невірний токен скидання паролю")

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Користувач не знайдений")

    hashed_password = contacts.hash_password(new_password)
    user.hashed_password = hashed_password
    db.commit()

    return {"message": "Пароль успішно змінено"}
