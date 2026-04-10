import os
import uuid
import logging

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, status
from sqlalchemy import select

from src.core.rate_limit import limiter

log = logging.getLogger("horarios.auth")
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.core.deps import get_current_user
from src.core.security import create_access_token, create_refresh_token, decode_refresh_token, verify_password
from src.models.user import User
from src.schemas.auth import LoginRequest, RefreshRequest, TokenResponse, UserResponse

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads", "avatars")

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(request: Request, body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales incorrectas")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuario desactivado")

    log.info("Login successful: user_id=%d email=%s", user.id, user.email)
    return TokenResponse(access_token=create_access_token(user.id), refresh_token=create_refresh_token(user.id))


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("20/minute")
async def refresh(request: Request, body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    user_id = decode_refresh_token(body.refresh_token)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token invalido o expirado")
    result = await db.execute(select(User).where(User.id == user_id, User.is_active.is_(True)))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no encontrado")
    log.info("Token refreshed: user_id=%d", user.id)
    return TokenResponse(access_token=create_access_token(user.id), refresh_token=create_refresh_token(user.id))


@router.get("/me", response_model=UserResponse)
async def me(user: User = Depends(get_current_user)):
    return UserResponse(id=user.id, email=user.email, display_name=user.display_name, avatar_url=user.avatar_url, is_active=user.is_active)


@router.post("/avatar", response_model=UserResponse)
@limiter.limit("10/minute")
async def upload_avatar(
    request: Request,
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Solo se permiten imagenes")

    if file.size and file.size > 2 * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Maximo 2MB")

    os.makedirs(UPLOAD_DIR, exist_ok=True)

    ext = file.filename.rsplit(".", 1)[-1] if file.filename and "." in file.filename else "jpg"
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    # Delete old avatar file if exists
    if user.avatar_url:
        old_path = os.path.join(UPLOAD_DIR, os.path.basename(user.avatar_url))
        if os.path.exists(old_path):
            os.remove(old_path)

    user.avatar_url = f"/uploads/avatars/{filename}"
    await db.commit()
    await db.refresh(user)

    return UserResponse(id=user.id, email=user.email, display_name=user.display_name, avatar_url=user.avatar_url, is_active=user.is_active)
