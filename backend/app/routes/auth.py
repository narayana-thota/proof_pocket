
from fastapi import APIRouter, HTTPException, status, Depends

from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    RefreshRequest,
    LogoutRequest
)

from app.services.auth_service import (
    register_user,
    authenticate_user,
    create_user_session,
    get_user_by_id,
    validate_user_session,
    revoke_user_session
)

from app.services.token_service import (
    create_access_token,
    create_refresh_token,
    decode_token
)


from app.dependencies import get_current_user



# Create authentication router
router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"]
)


# User registration endpoint
@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest):

    result = register_user(
        full_name=request.full_name,
        email=request.email,
        password=request.password
    )

    if not result["success"]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=result["message"]
        )

    return {
        "message": result["message"],
        "user": result["user"]
    }



# User login endpoint
@router.post("/login")
def login(request: LoginRequest):

    # Verify user credentials
    user = authenticate_user(
        email=request.email,
        password=request.password
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    # Create a new database session
    session_id = create_user_session(user["user_id"])

    # Generate JWT tokens
    access_token = create_access_token(
        user["user_id"]
    )

    refresh_token = create_refresh_token(
        user["user_id"],
        session_id
    )

    return {
        "message": "Login successful.",
        "token_type": "bearer",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": user
    }

# Get currently authenticated user
@router.get("/me")
def get_me(current_user=Depends(get_current_user)):

    user = get_user_by_id(current_user["user_id"])

    if not user:
        raise HTTPException(
            status_code=401,
            detail="User account is unavailable."
        )

    return {
        "message": "User retrieved successfully.",
        "user": user
    }


# Refresh access token
@router.post("/refresh")
def refresh_access_token(request: RefreshRequest):

    payload = decode_token(request.refresh_token)

    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired refresh token."
        )

    user_id = int(payload["sub"])
    session_id = payload.get("jti")

    if not session_id or not validate_user_session(session_id, user_id):
        raise HTTPException(
            status_code=401,
            detail="Session expired or revoked."
        )

    new_access_token = create_access_token(user_id)

    return {
        "message": "Access token refreshed successfully.",
        "token_type": "bearer",
        "access_token": new_access_token
    }


# Logout current session
@router.post("/logout")
def logout(
    request: LogoutRequest,
    current_user=Depends(get_current_user)
):

    payload = decode_token(request.refresh_token)

    if (
        not payload
        or payload.get("type") != "refresh"
        or payload.get("sub") != str(current_user["user_id"])
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid refresh token."
        )

    session_id = payload.get("jti")

    if not session_id or not revoke_user_session(
        session_id,
        current_user["user_id"]
    ):
        raise HTTPException(
            status_code=401,
            detail="Session is already revoked or unavailable."
        )

    return {
        "message": "Logout successful."
    }


