from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
import logging

from app.dependencies import get_db, get_current_user, get_current_active_superadmin
from app.models.user import User
from app.models.polysomnographie import Polysomnographie
from app.schemas.polysomnographie import PolysomnographieOut
from app.utils.response import success_response, error_response

router = APIRouter()
logger = logging.getLogger("app.routers.polysomnographie")

@router.get("/list")
async def list_polysomnographies(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    patient_nom: str = Query(None),
    date_enregistrement: str = Query(None),
    severite: str = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Liste paginée des rapports de Polysomnographie avec filtres optionnels.
    """
    try:
        query = select(Polysomnographie)
        if patient_nom:
            query = query.filter(Polysomnographie.patient_nom.ilike(f"%{patient_nom}%"))
        if date_enregistrement:
            query = query.filter(Polysomnographie.date_enregistrement == date_enregistrement)
        if severite:
            query = query.filter(Polysomnographie.severite == severite)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # Paginate
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)
        results = await db.execute(query)
        items = results.scalars().all()

        items_out = [PolysomnographieOut.from_orm(item).dict() for item in items]
        
        return success_response(
            data={"items": items_out, "total": total, "page": page, "limit": limit},
            message="Liste récupérée",
            code=status.HTTP_200_OK
        )
    except Exception as e:
        logger.error(f"Error listing polysomnographies: {str(e)}", exc_info=True)
        return error_response(message=f"Erreur interne : {str(e)}", code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@router.get("/{id}")
async def get_polysomnographie(
    id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Détail complet d'un rapport de Polysomnographie.
    """
    try:
        item = await db.get(Polysomnographie, id)
        if not item:
            return error_response(message="Rapport introuvable", code=status.HTTP_404_NOT_FOUND)
        return success_response(
            data=PolysomnographieOut.from_orm(item).dict(),
            message="Rapport récupéré",
            code=status.HTTP_200_OK
        )
    except Exception as e:
        logger.error(f"Error getting polysomnographie {id}: {str(e)}", exc_info=True)
        return error_response(message=f"Erreur interne : {str(e)}", code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@router.delete("/{id}")
async def delete_polysomnographie(
    id: int,
    admin_user: User = Depends(get_current_active_superadmin),
    db: AsyncSession = Depends(get_db)
):
    """
    Supprime un rapport de Polysomnographie (superadmin uniquement).
    """
    try:
        item = await db.get(Polysomnographie, id)
        if not item:
            return error_response(message="Rapport introuvable", code=status.HTTP_404_NOT_FOUND)
        await db.delete(item)
        await db.commit()
        return success_response(data=None, message="Rapport supprimé avec succès", code=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error deleting polysomnographie {id}: {str(e)}", exc_info=True)
        return error_response(message=f"Erreur interne : {str(e)}", code=status.HTTP_500_INTERNAL_SERVER_ERROR)
