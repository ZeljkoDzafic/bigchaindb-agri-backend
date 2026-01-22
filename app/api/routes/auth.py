"""Authentication routes."""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr

from app.config import get_settings

settings = get_settings()
router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# In-memory user store (replace with database in production)
fake_users_db: dict = {}


class UserCreate(BaseModel):
    """Schema for user registration."""

    email: EmailStr
    password: str
    full_name: Optional[str] = None


class User(BaseModel):
    """User model."""

    email: EmailStr
    full_name: Optional[str] = None
    public_key: Optional[str] = None
    disabled: bool = False


class UserInDB(User):
    """User model with hashed password."""

    hashed_password: str


class Token(BaseModel):
    """Token response model."""

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token data model."""

    email: Optional[str] = None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Get the current authenticated user from token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = fake_users_db.get(email)
    if user is None:
        raise credentials_exception
    return User(**user)


@router.post("/register", response_model=User)
async def register(user_data: UserCreate):
    """Register a new user."""
    if user_data.email in fake_users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    from app.services.bigchaindb_service import BigchainDBService

    bdb_service = BigchainDBService()
    public_key, _ = bdb_service.generate_keypair()

    user_dict = {
        "email": user_data.email,
        "full_name": user_data.full_name,
        "public_key": public_key,
        "hashed_password": get_password_hash(user_data.password),
        "disabled": False,
    }
    fake_users_db[user_data.email] = user_dict

    return User(**user_dict)


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Authenticate user and return access token."""
    user = fake_users_db.get(form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": user["email"]},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )
    return Token(access_token=access_token)


@router.post("/refresh", response_model=Token)
async def refresh_token(current_user: User = Depends(get_current_user)):
    """Refresh the access token."""
    access_token = create_access_token(
        data={"sub": current_user.email},
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )
    return Token(access_token=access_token)


@router.get("/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return current_user
