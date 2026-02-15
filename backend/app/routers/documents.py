from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

from app.db.database import db
from app.db import models
from app.core.auth import get_current_user
from app.services.file_processing import file_handler
from app.services.rag_functionality import rag_service

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
)


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    collection_id: Optional[int] = None,
    session: Session = Depends(db.get_db),
    current_user: models.User = Depends(get_current_user),
):
    filename = file.filename
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    content = await file.read()

    try:
        extracted_text = file_handler.run(extension, content)

        new_doc = models.Document(
            filename=filename,
            file_type=extension,
            user_id=current_user.id,
            collection_id=collection_id,
            status="processed",
        )
        session.add(new_doc)
        session.commit()
        session.refresh(new_doc)

        rag_service.add_document_to_index(
            extracted_text, new_doc.id, collection_id=collection_id
        )
        return {"message": "File indexed and ready for chat!", "doc_id": new_doc.id}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal processing error: {e}")