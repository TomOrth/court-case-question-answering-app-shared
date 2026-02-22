"""
Chat API endpoints.
"""
import uuid
from typing import List, Dict, Any
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.auth import get_current_user
from app.schemas.chat import ChatSessionCreate, ChatSessionResponse, CaseInfo
from app.services.chat import ChatService

# for the @router.post on /sessions/{session_id}/messages
from fastapi.responses import StreamingResponse
from app.schemas.chat import SendMessageRequest, ChatMessage as ChatMessageSchema
from app.models.chat import ChatMessage, MessageRole, ReasoningStep, ChatSession
# from app.services.chat_agent import chat_agent  # Mock chat agent for testing only
import json
from sqlalchemy import select

# for GET on/sessions/{session_id}
from app.schemas.chat import (
    SendMessageRequest,
    ChatMessage as ChatMessagesSchema,
    ChatSessionDetail,
    ChatSessionResponse,
    RenameSessionRequest,
)

router = APIRouter(prefix="/api/chat", tags=["chat"])

# We need the DB session and the current user for almost every request
async def get_chat_service(db: AsyncSession = Depends(get_db)) -> ChatService:
    return ChatService(db)


# Endpoints
@router.get("/cases", response_model=List[CaseInfo])
async def get_available_cases(
    service: ChatService = Depends(get_chat_service),
    # current_user = Depends(get_current_user)
):
    return await service.get_available_cases()


@router.get("/sessions", response_model=List[ChatSessionResponse])
async def get_my_sessions(
    service: ChatService = Depends(get_chat_service),
    current_user = Depends(get_current_user)
):
    """
    List all chat sessions for the current user.
    """
    return await service.get_user_sessions(current_user.id)


@router.post("/sessions", response_model=ChatSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    data: ChatSessionCreate,
    service: ChatService = Depends(get_chat_service),
    current_user = Depends(get_current_user)
):
    """
    Start a new chat session for a specific case.
    """
    try:
        return await service.create_session(current_user.id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/sessions/{session_id}", response_model=ChatSessionDetail)
async def get_session_details(
    session_id: UUID,
    service: ChatService = Depends(get_chat_service),
    # current_user = Depends(get_current_user)  # Removed - allow public viewing
):
    """
    Get details of a specific session.
    
    Public endpoint - allows viewing shared sessions without authentication.
    """
    session = await service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session



@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)    
async def delete_session(
    session_id: UUID,
    service: ChatService = Depends(get_chat_service),
    current_user = Depends(get_current_user)
):
    success = await service.delete_session(session_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return None


@router.patch("/sessions/{session_id}", response_model=ChatSessionResponse)
async def rename_session(
    session_id: UUID,
    request: RenameSessionRequest,
    service: ChatService = Depends(get_chat_service),
    current_user = Depends(get_current_user)
):
    """
    Rename a chat session.
    """
    session = await service.rename_session(
        session_id, 
        current_user.id, 
        request.session_title
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session



@router.post("/sessions/{session_id}/messages")
async def send_message(
    session_id: UUID,
    request: SendMessageRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Send a message to a session and get a streamed response
    """
    # --- STEP 1: VALIDATION
    # Verify session exists and belongs to user
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.session_id == session_id,
            ChatSession.user_id == current_user.id
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # --- STEP 2: SAVE USER MESSAGE
    # We save what the user said to the database immediately
    user_msg = ChatMessage(
        session_id=session_id,
        role=MessageRole.USER,
        content=request.content
    )
    db.add(user_msg)
    await db.commit()

    # --- STEP 3: PREPARE ASSISTANT MESSAGE
    # We create a placeholder row for the assistant's reply.
    # It starts empty. We will fill it in later (in a future iteration).
    assistant_msg = ChatMessage(
        session_id=session_id,
        role=MessageRole.ASSISTANT,
        content=""  # Empty initially
    )
    db.add(assistant_msg)
    await db.commit()
    await db.refresh(assistant_msg)

    # --- STEP 4: GET CASE_ID FROM SESSION
    # The planner needs to know which case to search
    case_id = session.case_id
    if not case_id:
        raise HTTPException(status_code=400, detail="Session has no associated case")
    
    # --- STEP 5: INITIALIZE PLANNER
    from app.services.planner_agent import PlannerAgentService
    planner = PlannerAgentService(db)

    # --- STEP 6: THE STREAM WRAPPER
    # This function sits between the Planner and the User.
    # It allows us to "spy" on the stream as it passes through
    async def stream_wrapper():
        full_content = []
        reasoning_steps_data = []

        # Loop through every "yield" from the planner
        async for line in planner.process_question(
            question=request.content,
            case_id=case_id,
            session_id=str(session_id),
            parent_message_id=str(assistant_msg.message_id)
        ):
            try:
                event = json.loads(line)
                event_type = event["type"]
                event_data = event.get("data", {})

                # Track full content for saving later
                if event["type"] == "content": 
                    full_content.append(event["data"])

                # Track reasoning steps for database
                elif event_type == "gathered_context":
                    reasoning_steps_data.append({
                        "step_order": event_data.get("step_number", 0),
                        "step_type": "gathered_context",
                        "step_id": event_data.get("id"),
                        "step_data": {
                            "step_number": event_data.get("step_number", 0),
                            "content": event_data.get("content", "")
                        }
                    })

                elif event_type == "reasoning":
                    reasoning_steps_data.append({
                        "step_order": event_data.get("step_number", 0),
                        "step_type": "reasoning",
                        "step_id": event_data.get("id"),
                        "step_data": {
                            "step_number": event_data.get("step_number", 0),
                            "content": event_data.get("content", "")
                        }
                    })

                elif event_type == "tool_call":
                    reasoning_steps_data.append({
                        "step_order": event_data.get("step_number", 0),
                        "step_type": "tool_call",
                        "step_id": event_data.get("id"),
                        "step_data": {
                            "step_number": event_data.get("step_number", 0),
                            "tool": event_data.get("tool"),
                            "parameters": event_data.get("parameters")
                        }
                    })

                elif event_type == "tool_result":
                    reasoning_steps_data.append({
                        "step_order": event_data.get("step_number", 0),
                        "step_type": "tool_result",
                        "step_data": {
                            "step_number": event_data.get("step_number", 0),
                            "tool": event_data.get("tool"),
                            "result": event_data.get("result", ""),
                            "parent_id": event_data.get("id"),
                        }
                    })

            except json.decoder.JSONDecodeError:
                pass
                # TODO: must handle this error

            # Yield the line to the FastAPI response so it gets sent to the user's browser
            yield line

        await _save_reasoning_to_db(
            assistant_msg,
            full_content,
            reasoning_steps_data,
            db
        )

    # --- STEP 7: RETURN THE STREAM
    return StreamingResponse(
        stream_wrapper(),
        media_type="application/x-ndjson"
    )

async def _save_reasoning_to_db(
    assistant_msg: ChatMessage,
    full_content: List[str],
    reasoning_steps_data: List[Dict[str, Any]],
    db: AsyncSession   
) -> None:
    """
    Save the final answer and reasoning steps to database.
    
    Args:
        assistant_msg: The assistant's ChatMessage object (already in DB)
        full_content: List of content chunks to join into final answer
        reasoning_steps_data: List of reasoning step dicts to save
        db: Datbase session
    """
    # STEP 1: Update the assistant message with final content
    final_answer = "".join(full_content)
    assistant_msg.content = final_answer
    db.add(assistant_msg)

    # STEP 2: Create ReasoningStep entries
    for step_data in reasoning_steps_data:
        step_id = step_data.get("step_id")
        reasoning_step = ReasoningStep(
            step_id=uuid.UUID(step_id) if step_id else None,
            message_id = assistant_msg.message_id,
            step_order=step_data["step_order"],
            step_type=step_data["step_type"],
            step_data=step_data["step_data"],
        )
        db.add(reasoning_step)
    
    try:
        await db.commit()
        print(f"✅ Saved {len(reasoning_steps_data)} reasoning steps to database")
    except Exception as e:
        print(f"❌ Failed to save reasoning to database: {e}")
        await db.rollback()