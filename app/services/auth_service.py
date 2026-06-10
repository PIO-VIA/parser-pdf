from datetime import datetime, timedelta
import uuid
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.utils.security import hash_password, verify_password, create_access_token, create_refresh_token
from app.services.email_service import send_reset_password_email
from app.config import settings

logger = logging.getLogger("app.services.auth_service")

async def register_user(db: AsyncSession, user_in: UserCreate) -> User:
    # Check if user already exists
    result = await db.execute(select(User).filter(User.email == user_in.email))
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Un utilisateur avec cet email existe déjà"
        )
    
    # Hash password
    hashed_pwd = hash_password(user_in.password)
    
    # Create user. First user can be superadmin if needed, or we just use default settings
    # For ease of testing, if there are no users, make the first user a superadmin.
    result_count = await db.execute(select(User))
    is_first = len(result_count.scalars().all()) == 0

    new_user = User(
        email=user_in.email,
        hashed_password=hashed_pwd,
        full_name=user_in.full_name,
        is_active=True,
        is_superadmin=is_first
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

async def authenticate_user(db: AsyncSession, email: str, password: str) -> User:
    result = await db.execute(select(User).filter(User.email == email))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect"
        )
    if not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Compte inactif"
        )
    return user

async def generate_user_tokens(user: User) -> dict:
    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(data={"sub": user.email})
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user
    }

async def initiate_password_reset(db: AsyncSession, email: str):
    result = await db.execute(select(User).filter(User.email == email))
    user = result.scalars().first()
    
    # Security note: Do not reveal if the email exists
    if not user:
        logger.warning(f"Password reset requested for non-existing email: {email}")
        return
        
    reset_token = str(uuid.uuid4())
    user.reset_token = reset_token
    user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
    await db.commit()
    
    reset_link = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
    await send_reset_password_email(user.email, reset_link)

async def perform_password_reset(db: AsyncSession, token: str, new_password: str):
    result = await db.execute(
        select(User).filter(
            User.reset_token == token,
            User.reset_token_expires > datetime.utcnow()
        )
    )
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token invalide ou expiré"
        )
        
    user.hashed_password = hash_password(new_password)
    user.reset_token = None
    user.reset_token_expires = None
    await db.commit()

async def update_user_profile(db: AsyncSession, user: User, update_in: UserUpdate) -> User:
    if update_in.full_name is not None:
        user.full_name = update_in.full_name
        
    if update_in.new_password is not None:
        if not update_in.old_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="L'ancien mot de passe est requis pour changer de mot de passe"
            )
        if not verify_password(update_in.old_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Ancien mot de passe incorrect"
            )
        user.hashed_password = hash_password(update_in.new_password)
        
    await db.commit()
    await db.refresh(user)
    return user
