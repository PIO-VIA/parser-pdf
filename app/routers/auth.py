from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.user import UserCreate, UserOut, UserUpdate
from app.schemas.auth import LoginRequest, ForgotPasswordRequest, ResetPasswordRequest
from app.services import auth_service
from app.utils.response import success_response, error_response
from app.utils.security import decode_token, create_access_token

router = APIRouter()

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Enregistre un nouvel utilisateur.
    """
    try:
        user = await auth_service.register_user(db, user_in)
        user_out = UserOut.from_orm(user)
        return success_response(
            data={"user": user_out.dict()},
            message="Compte créé avec succès",
            code=status.HTTP_201_CREATED
        )
    except HTTPException as he:
        return error_response(message=he.detail, code=he.status_code)
    except Exception as e:
        return error_response(message=f"Erreur interne : {str(e)}", code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@router.post("/login")
async def login(credentials: LoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Connexion utilisateur (JSON body).
    """
    try:
        user = await auth_service.authenticate_user(db, credentials.email, credentials.password)
        token_data = await auth_service.generate_user_tokens(user)
        # Convert user to schema
        token_data["user"] = UserOut.from_orm(user).dict()
        return success_response(
            data=token_data,
            message="Connexion réussie",
            code=status.HTTP_200_OK
        )
    except HTTPException as he:
        return error_response(message=he.detail, code=he.status_code)
    except Exception as e:
        return error_response(message=f"Erreur interne : {str(e)}", code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@router.post("/refresh")
async def refresh(authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    """
    Rafraîchit l'access token à partir du refresh token (Bearer).
    """
    if not authorization or not authorization.startswith("Bearer "):
        return error_response(message="Refresh token manquant ou invalide", code=status.HTTP_401_UNAUTHORIZED)
    
    refresh_token = authorization.split(" ")[1]
    try:
        payload = decode_token(refresh_token)
        email = payload.get("sub")
        token_type = payload.get("type")
        if email is None or token_type != "refresh":
            return error_response(message="Token invalide", code=status.HTTP_401_UNAUTHORIZED)
            
        result = await db.execute(select(User).filter(User.email == email))
        user = result.scalars().first()
        if not user or not user.is_active:
            return error_response(message="Utilisateur introuvable ou inactif", code=status.HTTP_401_UNAUTHORIZED)
            
        new_access_token = create_access_token(data={"sub": user.email})
        return success_response(
            data={"access_token": new_access_token, "token_type": "bearer"},
            message="Token rafraîchi",
            code=status.HTTP_200_OK
        )
    except Exception as e:
        return error_response(message=f"Token expiré ou invalide : {str(e)}", code=status.HTTP_401_UNAUTHORIZED)

@router.post("/forgot-password")
async def forgot_password(req: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    """
    Demande de réinitialisation du mot de passe (génère un lien envoyé par email).
    """
    try:
        await auth_service.initiate_password_reset(db, req.email)
        return success_response(
            data=None,
            message="Email de réinitialisation envoyé si ce compte existe",
            code=status.HTTP_200_OK
        )
    except Exception as e:
        return error_response(message=f"Erreur interne : {str(e)}", code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@router.post("/reset-password")
async def reset_password(req: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    """
    Réinitialise le mot de passe à l'aide du token envoyé par email.
    """
    try:
        await auth_service.perform_password_reset(db, req.token, req.new_password)
        return success_response(
            data=None,
            message="Mot de passe réinitialisé avec succès",
            code=status.HTTP_200_OK
        )
    except HTTPException as he:
        return error_response(message=he.detail, code=he.status_code)
    except Exception as e:
        return error_response(message=f"Erreur interne : {str(e)}", code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Récupère le profil de l'utilisateur connecté.
    """
    user_out = UserOut.from_orm(current_user)
    return success_response(
        data={"user": user_out.dict()},
        message="Profil récupéré",
        code=status.HTTP_200_OK
    )

@router.put("/me")
async def update_me(update_in: UserUpdate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """
    Met à jour le profil (nom ou mot de passe).
    """
    try:
        user = await auth_service.update_user_profile(db, current_user, update_in)
        user_out = UserOut.from_orm(user)
        return success_response(
            data={"user": user_out.dict()},
            message="Profil mis à jour",
            code=status.HTTP_200_OK
        )
    except HTTPException as he:
        return error_response(message=he.detail, code=he.status_code)
    except Exception as e:
        return error_response(message=f"Erreur interne : {str(e)}", code=status.HTTP_500_INTERNAL_SERVER_ERROR)
