import os
import uuid
import logging
from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func

from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.pdf_file import PDFFile, PDFStatus, PDFType
from app.services.pdf_service import process_pdf
from app.utils.response import success_response, error_response
from app.utils.validators import is_pdf
from app.config import settings

router = APIRouter()
logger = logging.getLogger("app.routers.pdf")

@router.post("/upload", status_code=status.HTTP_202_ACCEPTED)
async def upload_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Reçoit un fichier PDF, valide son type et sa taille, l'enregistre temporairement,
    crée une entrée de suivi en base et lance le traitement en tâche de fond.
    """
    try:
        # Lire les premiers octets pour la validation
        file_content = await file.read()
        await file.seek(0) # Rembobiner après lecture
        
        # Validation du type
        if not is_pdf(file_content, file.content_type):
            return error_response(message="Fichier non valide. Seuls les fichiers PDF sont acceptés.", code=status.HTTP_400_BAD_REQUEST)
            
        # Validation de la taille
        max_size_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
        if len(file_content) > max_size_bytes:
            return error_response(message=f"Le fichier dépasse la taille maximale autorisée de {settings.MAX_FILE_SIZE_MB} Mo.", code=status.HTTP_400_BAD_REQUEST)

        # Créer le dossier upload si inexistant
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

        # Générer un nom unique
        unique_filename = f"{uuid.uuid4()}_{file.filename}"
        filepath = os.path.join(settings.UPLOAD_DIR, unique_filename)

        # Sauvegarder sur le disque
        with open(filepath, "wb") as f:
            f.write(file_content)

        # Créer l'entrée dans la base de données
        pdf_file = PDFFile(
            original_filename=file.filename,
            temp_path=filepath,
            pdf_type=PDFType.UNKNOWN,
            status=PDFStatus.PENDING,
            uploaded_by=current_user.id
        )
        db.add(pdf_file)
        await db.commit()
        await db.refresh(pdf_file)

        # Ajouter le traitement en tâche de fond
        background_tasks.add_task(process_pdf, pdf_file.id, filepath)

        return success_response(
            data={"pdf_file_id": pdf_file.id, "status": PDFStatus.PENDING.value},
            message="PDF reçu, traitement en cours",
            code=status.HTTP_202_ACCEPTED
        )
    except Exception as e:
        logger.error(f"Error during PDF upload: {str(e)}", exc_info=True)
        return error_response(message=f"Erreur interne : {str(e)}", code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@router.get("/status/{pdf_file_id}")
async def get_pdf_status(pdf_file_id: int, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    """
    Récupère le statut de traitement d'un fichier PDF.
    """
    try:
        pdf_file = await db.get(PDFFile, pdf_file_id)
        if not pdf_file:
            return error_response(message="PDF introuvable", code=status.HTTP_404_NOT_FOUND)
            
        data = {
            "pdf_file_id": pdf_file.id,
            "pdf_type": pdf_file.pdf_type.value,
            "status": pdf_file.status.value,
            "error_message": pdf_file.error_message,
            "parsed_at": pdf_file.parsed_at.isoformat() if pdf_file.parsed_at else None
        }
        return success_response(data=data, message="Statut récupéré", code=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error checking PDF status: {str(e)}", exc_info=True)
        return error_response(message=f"Erreur interne : {str(e)}", code=status.HTTP_500_INTERNAL_SERVER_ERROR)

@router.get("/list")
async def list_pdfs(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    pdf_type: PDFType = Query(None),
    status_filter: PDFStatus = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Liste paginée des PDFs uploadés avec filtres optionnels.
    """
    try:
        # Construction de la requête
        query = select(PDFFile)
        
        # Filtres
        if pdf_type:
            query = query.filter(PDFFile.pdf_type == pdf_type)
        if status_filter:
            query = query.filter(PDFFile.status == status_filter)
            
        # Total count query
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # Pagination & Execution
        offset = (page - 1) * limit
        query = query.order_by(PDFFile.created_at.desc()).offset(offset).limit(limit)
        results = await db.execute(query)
        items = results.scalars().all()

        # Construction du payload
        items_out = []
        for item in items:
            items_out.append({
                "id": item.id,
                "original_filename": item.original_filename,
                "pdf_type": item.pdf_type.value,
                "status": item.status.value,
                "error_message": item.error_message,
                "uploaded_by": item.uploaded_by,
                "created_at": item.created_at.isoformat() if item.created_at else None,
                "parsed_at": item.parsed_at.isoformat() if item.parsed_at else None
            })

        data = {
            "items": items_out,
            "total": total,
            "page": page,
            "limit": limit
        }
        return success_response(data=data, message="Liste récupérée", code=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error listing PDFs: {str(e)}", exc_info=True)
        return error_response(message=f"Erreur interne : {str(e)}", code=status.HTTP_500_INTERNAL_SERVER_ERROR)
