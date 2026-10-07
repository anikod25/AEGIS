"""FastAPI dependencies for authentication and authorisation.

SECURITY CONTRACT
-----------------
- User identity is ALWAYS derived from the validated JWT in the Authorization
  header. No route may accept a user_id or role from the request body,
  query parameters, or any other client-controlled source.
- `get_current_user` is the single source of truth for the authenticated user.
- `require_admin` delegates to `get_current_user` first, then checks the role
  stored in the database row — never a role claim from the token payload.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core.security import decode_access_token
from backend.app.models.user import User, UserRole

_bearer = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    """Extract and validate the JWT; return the authenticated User.

    Raises HTTP 401 for any of:
    - missing token (HTTPBearer handles this)
    - malformed token
    - invalid signature
    - expired token
    - missing 'sub' claim
    - user record no longer exists in the database

    Uses 401 (not 404) even for a deleted user, so the token's validity
    cannot be inferred from the response code.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(credentials.credentials)
        user_id: str | None = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        # Validate that sub is a positive integer (user IDs are always > 0)
        uid = int(user_id)
        if uid <= 0:
            raise credentials_exception
    except (JWTError, ValueError):
        raise credentials_exception

    user = db.get(User, uid)
    if user is None:
        # Return 401, not 404 — do not confirm token was valid for a deleted user
        raise credentials_exception
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Raise HTTP 403 if the current user is not an administrator.

    Role is read from the database row, NOT from the JWT payload.
    This prevents a forged token claim from granting admin access.
    """
    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required.",
        )
    return current_user
