from datetime import datetime, timedelta
from typing import Optional

from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from starlette import status

from src.models.user import schemas
from src.models.user.models import User
from passlib.context import CryptContext

bycrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
SECRET_KEY = ']%>w3KcCL=oNgkyduW^8Q35*^TrPT*W!3K}'
ALGORITHM = 'HS256'
invalid_tokens = set()


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        id: int = payload.get("id")
        role: str = payload.get("role")
        if username is None or id is None:
            raise get_authentication_exception()

        return {"username": username, "id": id, "role": role}
    except JWTError:
        raise get_authentication_exception()


def create_access_token(username: str, user_id: int, role: str, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = {"sub": username, "id": user_id, "role": role}
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def authenticate_user(username: str, password: str, db):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return False
    if not verify_password(password, user.hash_password):
        return False
    return user


def verify_password(plain_password, hashed_password):
    return bycrypt_context.verify(plain_password, hashed_password)


def get_password_hash(password) -> str:
    return bycrypt_context.hash(password)


def get_authentication_exception():
    authentication_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    return authentication_exception


def get_current_token(token: str = Depends(oauth2_scheme)) -> str:
    if token in invalid_tokens:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    return token


async def is_admin(current_user: dict = Depends(get_current_user)) -> bool:
    if current_user.get('role') != schemas.Role.admin:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")
    return True



