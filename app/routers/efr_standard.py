from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
import logging

from app.dependencies import get_db, get_current_user, get_current_active_superadmin
from app.models.user import User
from app.models.efr_standard import EFRStandard
from app.schemas.efr_standard import EFRStandardOut
from app.utils.response import success_response, error_response

router = APIRouter()
logger = logging.getLogger("app.routers.efr_standard")

@router.get("/list")
async def list_efr_standards(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    patient_nom: str = Query(None),
    date_examen: str = Query(None),
    medecin: str = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Liste paginée des examens EFR Standard avec filtres optionnels.
    """
    try:
        query = select(EFRStandard)
        if patient_nom:
            query = query.filter(EFRStandard.patient_nom.ilike(f"%{patient_nom}%"))
        if date_examen:
            query = query.filter(EFRStandard.date_examen == date_examen)
        if medecin:
            query = query.filter(EFRStandard.medecin.ilike(f"%{medecin}%"))

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # Paginate
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)
        results = await db.execute(query)
        items = results.scalars().all()

        items_out = [EFRStandardOut.model_validate(item).model_dump() for item in items]
        
        return success_response(
            data={"items": items_out, "total": total, "page": page, "limit": limit},
            message="Liste récupérée",
            code=status.HTTP_200_OK
        )
    except Exception as e:
        logger.error(f"Error listing efr standards: {str(e)}", exc_info=True)
        return error_response(message=f"Erreur interne : {str(e)}", code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@router.get("/{id}")
async def get_efr_standard(
    id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Détail complet d'un examen EFR Standard.
    """
    try:
        item = await db.get(EFRStandard, id)
        if not item:
            return error_response(message="Rapport introuvable", code=status.HTTP_404_NOT_FOUND)
        return success_response(
            data=EFRStandardOut.model_validate(item).model_dump(),
            message="Rapport récupéré",
            code=status.HTTP_200_OK
        )
    except Exception as e:
        logger.error(f"Error getting efr standard {id}: {str(e)}", exc_info=True)
        return error_response(message=f"Erreur interne : {str(e)}", code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@router.delete("/{id}")
async def delete_efr_standard(
    id: int,
    admin_user: User = Depends(get_current_active_superadmin),
    db: AsyncSession = Depends(get_db)
):
    """
    Supprime un examen EFR Standard (superadmin uniquement).
    """
    try:
        item = await db.get(EFRStandard, id)
        if not item:
            return error_response(message="Rapport introuvable", code=status.HTTP_404_NOT_FOUND)
        await db.delete(item)
        await db.commit()
        return success_response(data=None, message="Rapport supprimé avec succès", code=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error deleting efr standard {id}: {str(e)}", exc_info=True)
        return error_response(message=f"Erreur interne : {str(e)}", code=status.HTTP_500_INTERNAL_SERVER_ERROR)
