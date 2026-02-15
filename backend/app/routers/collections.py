from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db import models
from app.db.database import db
from app.core.auth import get_current_user
from app import schema
from app.services.rag_functionality import rag_service

router = APIRouter(
    prefix="/collections",
    tags=["collections"],
)


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_collection(
    collection_data: schema.CollectionCreate,
    current_user: models.User = Depends(get_current_user),
    session: Session = Depends(db.get_db),
):
    collection = models.Collection(
        name=collection_data.name,
        user_id=current_user.id,
    )
    session.add(collection)
    session.commit()
    session.refresh(collection)

    return {
        "id": collection.id,
        "name": collection.name,
        "message": "Collection created successfully!",
    }


@router.get("/")
def get_collections(
    current_user: models.User = Depends(get_current_user),
    session: Session = Depends(db.get_db),
):
    collections = (
        session.query(models.Collection).filter(models.Collection.user_id == current_user.id).all()
    )
    return [
        {"id": c.id, "name": c.name, "created_at": c.created_at}
        for c in collections
    ]


@router.get("/{collection_id}")
def get_collection(
    collection_id: int,
    current_user: models.User = Depends(get_current_user),
    session: Session = Depends(db.get_db),
):
    collection = (
        session.query(models.Collection).filter(
            models.Collection.user_id == current_user.id,
            models.Collection.id == collection_id,
        ).first()
    )
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    documents = (
        session.query(models.Document).filter(models.Document.collection_id == collection_id).all()
    )

    return {
        "id": collection.id,
        "name": collection.name,
        "created_at": collection.created_at,
        "documents": [
            {"id": d.id, "filename": d.filename, "file_type": d.file_type}
            for d in documents
        ],
    }


@router.delete("/{collection_id}")
def remove_collection(
    collection_id: int,
    current_user: models.User = Depends(get_current_user),
    session: Session = Depends(db.get_db),
):
    collection = (
        session.query(models.Collection).filter(
            models.Collection.id == collection_id,
            models.Collection.user_id == current_user.id,
        ).first()
    )
    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    try:
        rag_service.delete_collection_vectors(collection_id)
    except Exception as e:
        print(f"Warning: Could not clear vectors for collection {collection_id}: {e}")

    session.delete(collection)
    session.commit()

    return {"message": f"Collection '{collection.name}' and all associated data deleted successfully"}