import os
import logging
from datetime import datetime
from app.database import SessionLocal
from app.models.pdf_file import PDFFile, PDFStatus, PDFType
from app.services.pdf_detector import detect_pdf_type
from app.services.parsers import (
    PolysomnographieParser, PolygraphiePPCParser,
    EFRStandardParser, EFRAvanceeParser
)

logger = logging.getLogger("app.services.pdf_service")

async def process_pdf(pdf_file_id: int, filepath: str):
    """
    Pipeline complet exécuté en arrière-plan :
    1. Récupérer l'enregistrement et passer au statut PROCESSING
    2. Détecter le type de PDF
    3. Parser et sauvegarder en base
    4. Passer au statut DONE et mettre à jour parsed_at et temp_path
    5. Supprimer le fichier temporaire (dans tous les cas)
    """
    async with SessionLocal() as db:
        pdf_record = None
        try:
            pdf_record = await db.get(PDFFile, pdf_file_id)
            if not pdf_record:
                logger.error(f"PDF record {pdf_file_id} not found in DB")
                return

            # Mettre à jour statut
            pdf_record.status = PDFStatus.PROCESSING
            await db.commit()

            # Détection
            pdf_type = detect_pdf_type(filepath)
            pdf_record.pdf_type = pdf_type
            await db.commit()

            if pdf_type == PDFType.UNKNOWN:
                raise ValueError("Type de PDF non reconnu")

            # Parser selection
            parser_map = {
                PDFType.POLYSOMNOGRAPHIE: PolysomnographieParser,
                PDFType.POLYGRAPHIE_PPC: PolygraphiePPCParser,
                PDFType.EFR_STANDARD: EFRStandardParser,
                PDFType.EFR_AVANCEE: EFRAvanceeParser,
            }

            parser_class = parser_map[pdf_type]
            parser = parser_class(filepath=filepath, pdf_file_id=pdf_file_id)
            
            # Parse and save inside parser
            await parser.parse(db)

            # Succès
            pdf_record.status = PDFStatus.DONE
            pdf_record.parsed_at = datetime.utcnow()
            pdf_record.temp_path = None
            await db.commit()
            logger.info(f"Successfully processed PDF record {pdf_file_id} of type {pdf_type}")

        except Exception as e:
            logger.error(f"Error processing PDF record {pdf_file_id}: {str(e)}", exc_info=True)
            if pdf_record:
                try:
                    # Refresh to avoid session state sync issues
                    await db.refresh(pdf_record)
                    pdf_record.status = PDFStatus.FAILED
                    pdf_record.error_message = str(e)
                    await db.commit()
                except Exception as db_err:
                    logger.error(f"Failed to update failed status in DB: {str(db_err)}")
            raise

        finally:
            # TOUJOURS supprimer le fichier temp, succès ou erreur
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
                    logger.info(f"Temporary file {filepath} removed")
            except Exception as file_err:
                logger.error(f"Failed to delete temporary file {filepath}: {str(file_err)}")
