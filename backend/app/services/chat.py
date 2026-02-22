"""
Chat Service.

Handles business logic for managing chat sessions.
"""

from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, delete
from sqlalchemy.orm import joinedload, selectinload

from app.models.chat import ChatSession, ChatMessage
from app.models.case import Case
from app.schemas.chat import ChatSessionCreate



class ChatService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_available_cases(self) -> List[Case]:
        """
        List all cases that are ready for chatting.
        """
        query = select(Case).where(Case.status == 'ready').order_by(Case.case_id)
        result = await self.db.execute(query)
        return result.scalars().all()  # ??? need to look this up further

    async def create_session(self, user_id: UUID, data: ChatSessionCreate) -> ChatSession:
        """
        Create a new chat session for a user and a case.
        """
        # 1. Fetch the case to get its name (for the default title)
        case_query = select(Case).where(Case.case_id == data.case_id)
        case_result = await self.db.execute(case_query)
        case = case_result.scalar_one_or_none()

        if not case:
            raise ValueError(f"Case {data.case_id} not found")

        # 2. Create the session object
        # Default title is the case name
        new_session = ChatSession(
            user_id=user_id,
            case_id=data.case_id,
            session_title=case.case_name[:255]
        )

        self.db.add(new_session)
        await self.db.commit()
        await self.db.refresh(new_session)

        # Manually attach case_name for the response schema
        new_session.case_name = case.case_name

        return new_session

    async def get_user_sessions(self, user_id: UUID) -> List[ChatSession]:
        """
        Get all chat sessions for a specific user, ordered by most recent.
        """
        # We join with Case to get the case name efficiently
        query = (
            select(ChatSession).
            options(joinedload(ChatSession.case))
            .where(ChatSession.user_id == user_id)
            .order_by(desc(ChatSession.updated_at))
        )
        result = await self.db.execute(query)
        sessions = result.scalars().all()

        # Helper to flatten case_name for the schema
        for session in sessions:
            if session.case:
                session.case_name = session.case.case_name
        return sessions


    async def get_session(self, session_id: UUID, user_id: Optional[UUID] = None) -> Optional[ChatSession]:
        """
        Get a specific session.
        
        If user_id is provided, verifies ownership.
        If user_id is None, returns session for public viewing.
        """
        query = (
            select(ChatSession)
            .options(
                joinedload(ChatSession.case),
                selectinload(ChatSession.messages).selectinload(ChatMessage.reasoning_steps)
            )
            .where(ChatSession.session_id == session_id)
        )
        
        # Only filter by user_id if provided (for ownership verification)
        if user_id is not None:
            query = query.where(ChatSession.user_id == user_id)
        
        result = await self.db.execute(query)
        session = result.scalar_one_or_none()

        if session and session.case:
            session.case_name = session.case.case_name

        return session


    async def delete_session(self, session_id: UUID, user_id: UUID) -> bool:
        """
        Delete a session if it belongs to the user.
        """
        # Check existence and ownership first
        session = await self.get_session(session_id, user_id)
        if not session:
            return False
        
        await self.db.delete(session)
        await self.db.commit()
        return True
    
    async def rename_session(
        self, 
        session_id: UUID, 
        user_id: UUID, 
        new_title: str
    ) -> Optional[ChatSession]:
        """
        Rename a session if it belongs to the user.
        """
        # Check existence and ownership
        query = (
            select(ChatSession)
            .options(joinedload(ChatSession.case))
            .where(
                ChatSession.session_id == session_id,
                ChatSession.user_id == user_id
            )
        )
        result = await self.db.execute(query)
        session = result.scalar_one_or_none()
        
        if not session:
            return None
        
        # Update title
        session.session_title = new_title[:255]  # Truncate to max length
        await self.db.commit()
        await self.db.refresh(session)
        
        # Attach case_name for response
        if session.case:
            session.case_name = session.case.case_name
        
        return session    