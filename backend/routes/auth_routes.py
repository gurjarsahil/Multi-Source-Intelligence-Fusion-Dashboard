"""
Authentication Routes — Register, Login, User Management.
"""

from fastapi import APIRouter, HTTPException, Depends
from backend.auth import hash_password, verify_password, create_access_token, get_current_user, require_role
from backend.models.schemas import UserRegister, UserLogin, TokenResponse, UserResponse
from backend.database import get_db

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse)
async def register(user: UserRegister):
    """Register a new user."""
    db = await get_db()
    try:
        # Check if email exists
        cursor = await db.execute("SELECT id FROM users WHERE email = ?", (user.email,))
        if await cursor.fetchone():
            raise HTTPException(status_code=400, detail="Email already registered")

        hashed = hash_password(user.password)
        cursor = await db.execute(
            "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
            (user.name, user.email, hashed, user.role)
        )
        await db.commit()
        user_id = cursor.lastrowid

        token = create_access_token({
            "sub": str(user_id),
            "email": user.email,
            "role": user.role,
        })

        return TokenResponse(access_token=token, role=user.role, name=user.name)
    finally:
        await db.close()


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    """Login with email and password."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT id, name, email, password, role FROM users WHERE email = ?",
            (credentials.email,)
        )
        user = await cursor.fetchone()

        if not user or not verify_password(credentials.password, user[3]):
            raise HTTPException(status_code=401, detail="Invalid email or password")

        token = create_access_token({
            "sub": str(user[0]),
            "email": user[2],
            "role": user[4],
        })

        return TokenResponse(access_token=token, role=user[4], name=user[1])
    finally:
        await db.close()


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user info."""
    db = await get_db()
    try:
        cursor = await db.execute(
            "SELECT id, name, email, role FROM users WHERE id = ?",
            (current_user["id"],)
        )
        user = await cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return UserResponse(id=user[0], name=user[1], email=user[2], role=user[3])
    finally:
        await db.close()


@router.get("/users")
async def list_users(current_user: dict = Depends(require_role("admin"))):
    """List all users (admin only)."""
    db = await get_db()
    try:
        cursor = await db.execute("SELECT id, name, email, role, created_at FROM users")
        users = await cursor.fetchall()
        return [{"id": u[0], "name": u[1], "email": u[2], "role": u[3], "created_at": u[4]} for u in users]
    finally:
        await db.close()
