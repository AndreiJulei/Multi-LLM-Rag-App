from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import models
from app.db.database import db
from app.core.auth import get_current_user
from app.services.llm_voting import voting_service
from app.services.rag_functionality import rag_service
from app import schema

router = APIRouter(
    prefix="/chat", tags=["Counsel Chat"]
)

@router.post("/query")
async def handle_counsel_query(
    request: schema.ChatRequest,
    current_user: models.User = Depends(get_current_user),
    session: Session = Depends(db.get_db),
):
    context = rag_service.query_collection(request.collection_id, request.query)

    # Route by type of answer
    if request.mode == "debate":
        responses = await voting_service.get_raw_answers(
            request.query, context, session
        )
    else:
        answer = await voting_service.get_single_response(
            request.mode, request.query, context, session
        )
        responses = {request.mode: answer}

    new_chat = models.ChatHistory(
        user_id=current_user.id,
        collection_id=request.collection_id,
        question=request.query,
        context=context,
        llm_responses=responses,
    )

    session.add(new_chat)
    session.commit()
    session.refresh(new_chat)

    return {
        "chat_id": new_chat.id,
        "responses": responses,
        "mode": request.mode,
    }


@router.post("/blind-vote")
async def blind_vote(
    request: schema.BlindVoteRequest,
    current_user: models.User = Depends(get_current_user),
    session: Session = Depends(db.get_db),
):

    chat = (
        session.query(models.ChatHistory).filter(
            models.ChatHistory.id == request.chat_id,
            models.ChatHistory.user_id == current_user.id,
        ).first()
    )

    if not chat:
        raise HTTPException(status_code=404, detail="Chat record not found")

    if not chat.llm_responses or len(chat.llm_responses) < 2:
        raise HTTPException(
            status_code=400,
            detail="Blind vote requires at least 2 model responses (use debate mode)",
        )

    result = await voting_service.run_blind_vote(
        chat.question,
        chat.context or "",
        chat.llm_responses,
        session,
    )

    chat.final_answer = result["final_text"]
    session.commit()

    votes = result["votes"]
    winning_model = max(votes, key=votes.get) if votes else None

    return {
        "winner_answer": result["final_text"],
        "winning_model": winning_model,
        "votes": votes,
    }

@router.get("/history/{collection_id}")
async def get_chat_history(
    collection_id: int, 
    current_user: models.User = Depends(get_current_user),
    session: Session = Depends(db.get_db),
):
    chats = (
        session.query(models.ChatHistory).filter(
            models.ChatHistory.user_id == current_user.id,
            models.ChatHistory.collection_id == collection_id,
        ).order_by(models.ChatHistory.timestamp).all()
    )
    return [
        {
            "id": c.id,
            "question": c.question,
            "llm_responses": c.llm_responses,
            "final_answer": c.final_answer,
            "timestamp": c.timestamp.isoformat() if c.timestamp else None,
        }
        for c in chats
    ]