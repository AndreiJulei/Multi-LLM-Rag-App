import os
import asyncio
from typing import Dict, List, Optional

from sqlalchemy.orm import Session
from dotenv import load_dotenv

from app.db import models
from app.core.model_registry import (
    PROVIDERS,
    AVAILABLE_MODELS,
    DEFAULT_ACTIVE_MODELS,
    get_provider_for_model,
    get_env_var_for_model,
)

load_dotenv()


class VotingService:
    # LLM handling
    @staticmethod
    def _build_llm(model_id: str, api_key: str):
        provider = get_provider_for_model(model_id)

        if provider == "google":
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(model=model_id, google_api_key=api_key)

        if provider == "openai":
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(model=model_id, openai_api_key=api_key)

        if provider == "groq":
            from langchain_groq import ChatGroq
            return ChatGroq(model_name=model_id, groq_api_key=api_key)

        if provider == "anthropic":
            from langchain_anthropic import ChatAnthropic
            return ChatAnthropic(model=model_id, anthropic_api_key=api_key)

        # add models here
        return None

    # Resole api key
    @staticmethod
    def _resolve_key(provider: str, settings: Optional[models.SystemSettings]) -> Optional[str]:
        if settings and settings.api_keys:
            db_key = settings.api_keys.get(provider)
            if db_key:
                return db_key
        env_var = PROVIDERS.get(provider)
        if env_var:
            return os.getenv(env_var)
        return None

    def get_active_models(self, session: Session) -> Dict[str, object]:
        settings = session.query(models.SystemSettings).first()
        active_list = (settings.active_models if settings else None) or DEFAULT_ACTIVE_MODELS

        instances: Dict[str, object] = {}
        for model_id in active_list:
            provider = get_provider_for_model(model_id)
            if not provider:
                continue
            key = self._resolve_key(provider, settings)
            if not key:
                print(f"⚠ Skipping {model_id}: no API key for provider '{provider}'")
                continue
            llm = self._build_llm(model_id, key)
            if llm:
                instances[model_id] = llm
        return instances

    def get_single_model(self, model_id: str, session: Session):
        settings = session.query(models.SystemSettings).first()
        provider = get_provider_for_model(model_id)
        if not provider:
            raise ValueError(f"Unknown model: {model_id}")
        key = self._resolve_key(provider, settings)
        if not key:
            raise ValueError(f"No API key configured for provider '{provider}'")
        llm = self._build_llm(model_id, key)
        if not llm:
            raise ValueError(f"Could not build LLM for {model_id}")
        return llm

    # Multiple answers for voting logic
    async def get_raw_answers(
        self, question: str, context: str, session: Session
    ) -> Dict[str, str]:
        active = self.get_active_models(session)
        if not active:
            raise ValueError("No models are currently active in System Settings.")

        prompt = (
            f"Using the following context, answer the question.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {question}\n\nAnswer:"
        )

        tasks = {name: llm.ainvoke(prompt) for name, llm in active.items()}
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)

        answers: Dict[str, str] = {}
        for name, res in zip(tasks.keys(), results):
            if isinstance(res, Exception):
                answers[name] = f"[Error: {res}]"
            else:
                answers[name] = res.content
        return answers

    async def get_single_response(
        self, model_id: str, question: str, context: str, session: Session
    ) -> str:
        llm = self.get_single_model(model_id, session)
        prompt = (
            f"Using the following context, answer the question.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {question}\n\nAnswer:"
        )
        res = await llm.ainvoke(prompt)
        return res.content

    # VOting logic 
    async def run_blind_vote(
        self,
        question: str,
        context: str,
        raw_answers: Dict[str, str],
        session: Session,
    ) -> Dict:
        active = self.get_active_models(session)
        candidates = list(raw_answers.items())
        votes = {name: 0 for name in raw_answers}

        candidate_text = "\n\n".join(
            f"Candidate {chr(65 + i)}: {ans}" for i, (_, ans) in enumerate(candidates)
        )
        vote_prompt = (
            f"Given the question and context below, judge these candidate answers. "
            f"Reply with ONLY the letter of the best answer.\n\n"
            f"Question: {question}\nContext: {context}\n\n{candidate_text}"
        )

        vote_tasks = [llm.ainvoke(vote_prompt) for llm in active.values()]
        vote_results = await asyncio.gather(*vote_tasks, return_exceptions=True)

        for res in vote_results:
            if isinstance(res, Exception):
                continue
            letter = res.content.strip().upper()
            for i in range(len(candidates)):
                if chr(65 + i) in letter:
                    votes[candidates[i][0]] += 1

        max_votes = max(votes.values()) if votes else 0
        winners = [n for n, c in votes.items() if c == max_votes]
        final_text = raw_answers[winners[0]] if len(winners) == 1 else "TIE"

        return {"final_text": final_text, "votes": votes}


voting_service = VotingService()