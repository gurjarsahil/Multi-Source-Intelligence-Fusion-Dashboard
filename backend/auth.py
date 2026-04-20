"""
Authentication module — JWT-based auth with RBAC.
Handles password hashing, token creation/validation, and role-based access control.
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.hash import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# ─── Configuration ─────────────────────────────────────
SECRET_KEY = "intel-dashboard-super-secret-key-change-in-production-2024"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 hours

security = HTTPBearer()

# ─── Role Hierarchy ───────────────────────────────────
ROLE_HIERARCHY = {
    "admin": 3,
    "analyst": 2,
    "viewer": 1,
}


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.verify(plain, hashed)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """FastAPI dependency to extract current user from JWT token."""
    payload = decode_token(credentials.credentials)
    user_id = payload.get("sub")
    role = payload.get("role", "viewer")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    return {"id": int(user_id), "role": role, "email": payload.get("email", "")}


def require_role(minimum_role: str):
    """
    Dependency factory for role-based access control.
    Usage: Depends(require_role("analyst"))
    """
    async def role_checker(user: dict = Depends(get_current_user)):
        user_level = ROLE_HIERARCHY.get(user["role"], 0)
        required_level = ROLE_HIERARCHY.get(minimum_role, 0)
        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {minimum_role}, Current: {user['role']}"
            )
        return user
    return role_checker
