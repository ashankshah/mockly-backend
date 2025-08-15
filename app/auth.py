"""
Authentication configuration for Mockly application
Handles FastAPI Users setup, OAuth providers, and user management
"""

import os
from typing import Optional
import uuid
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin, exceptions
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users.db import SQLAlchemyUserDatabase
from httpx_oauth.clients.google import GoogleOAuth2
from httpx_oauth.clients.linkedin import LinkedInOAuth2

from app.models import User
from app.database import get_async_session

# OAuth2 clients configuration
google_oauth_client = GoogleOAuth2(
    client_id=os.getenv("GOOGLE_OAUTH_CLIENT_ID", "your-google-client-id"),
    client_secret=os.getenv("GOOGLE_OAUTH_CLIENT_SECRET", "your-google-client-secret"),
    scopes=["openid", "email", "profile"]
)

linkedin_oauth_client = LinkedInOAuth2(
    client_id=os.getenv("LINKEDIN_OAUTH_CLIENT_ID", "your-linkedin-client-id"),
    client_secret=os.getenv("LINKEDIN_OAUTH_CLIENT_SECRET", "your-linkedin-client-secret"),
)

# JWT Secret - CHANGE THIS IN PRODUCTION
SECRET = os.getenv("SECRET_KEY", "SECRET_KEY_CHANGE_IN_PRODUCTION")

class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        print(f"User {user.id} has registered.")

    async def on_after_forgot_password(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        print(f"User {user.id} has forgot their password. Reset token: {token}")

    async def on_after_request_verify(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        print(f"Verification requested for user {user.id}. Verification token: {token}")

    async def oauth_callback(
        self,
        oauth_name: str,
        access_token: str,
        account_id: str,
        account_email: str,
        expires_at: Optional[int] = None,
        refresh_token: Optional[str] = None,
        request: Optional[Request] = None,
        *,
        associate_by_email: bool = False,
        is_verified_by_default: bool = False,
    ) -> User:
        """
        Handle OAuth callback with account linking support.
        If a user already exists with the same email, link the OAuth account.
        """
        try:
            print(f"🔍 OAuth callback started: {oauth_name}, email: {account_email}, account_id: {account_id}")
            
            # Check if user already exists with this email
            try:
                existing_user = await self.get_by_email(account_email)
                print(f"🔍 Found existing user: {existing_user.email}")
            except exceptions.UserNotExists:
                existing_user = None
                print(f"🔍 No existing user found, will create new user")
            
            if existing_user:
                # Link OAuth account to existing user
                print(f"🔗 Linking {oauth_name} account to existing user {existing_user.email}")
                
                # Prepare update dictionary
                update_dict = {}
                
                # Update the OAuth ID field
                if oauth_name == "google":
                    update_dict["google_id"] = account_id
                    print(f"🔗 Set google_id: {account_id}")
                elif oauth_name == "linkedin":
                    update_dict["linkedin_id"] = account_id
                    print(f"🔗 Set linkedin_id: {account_id}")
                
                # Update user info if not already set
                if not existing_user.is_verified and is_verified_by_default:
                    update_dict["is_verified"] = True
                    print("🔗 Set user as verified")
                    
                print("🔍 Updating user in database...")
                updated_user = await self.user_db.update(existing_user, update_dict)
                print("✅ User updated successfully")
                return updated_user
            
            # Call the parent method to create a new user
            print("🆕 Creating new user...")
            return await super().oauth_callback(
                oauth_name,
                access_token,
                account_id,
                account_email,
                expires_at,
                refresh_token,
                request,
                associate_by_email=associate_by_email,
                is_verified_by_default=is_verified_by_default,
            )
        except Exception as e:
            print(f"❌ Error in oauth_callback: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            raise

async def get_user_db(session = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)

async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    yield UserManager(user_db)

# Bearer transport for JWT tokens
bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")

# JWT strategy function
def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=SECRET, lifetime_seconds=3600 * 24 * 7)

# JWT authentication backend
auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

# FastAPI Users instance
fastapi_users = FastAPIUsers[User, uuid.UUID](get_user_manager, [auth_backend])

# Current user dependencies
current_active_user = fastapi_users.current_user(active=True)
current_active_user_optional = fastapi_users.current_user(active=True, optional=True)
current_superuser = fastapi_users.current_user(active=True, superuser=True) 