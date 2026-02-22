# import asyncio
# import json
# from typing import AsyncGenerator, Any
# from uuid import UUID

# class ChatAgentService:
#     """
#     Service to handle chat logic and streaming.
    
#     Currently a MOCK implementation to test the infrastructure.
#     """
#     async def stream_response(self, user_message: str) -> AsyncGenerator[str, None]:
#         """
#         Generates a stream of NDJSON events.
#         """
#         # PHASE 1: REASONING
#         # Simulate thinking
#         await asyncio.sleep(0.5)
#         await asyncio.sleep(2)

#         # Yield a JSON string. Frontend will parse this line
#         yield self._format_event("reasoning", {
#             "step_number": 1,
#             "content": "Analyzing the user's request..."
#         })

#         # Simulate tool call 
#         await asyncio.sleep(0.8)
#         await asyncio.sleep(2)
#         yield self._format_event("reasoning", {
#             "step_number": 2,
#             "content": f"Searching case files for keywords related to '{user_message[:20]}...'"
#         })

#         # Simulate tool result 
#         await asyncio.sleep(0.5)
#         await asyncio.sleep(2)
#         yield self._format_event("reasoning", {
#             "step_number": 3,
#             "content": "Found 3 relevant documents."
#         })

#         # PHASE 2: GENERATION ("Typing" phase)
#         # Stream the answer 
#         response_text = f"This is a simulated response to: '{user_message}'. I am streaming this text chunk by chunk to test the UI."
#         words = response_text.split(" ")
#         for word in words:
#             await asyncio.sleep(0.1)
#             await asyncio.sleep(1)
#             yield self._format_event("content", word + " ")


#     def _format_event(self, event_type: str, data: Any) -> str:
#         """
#         Helpder to format data as a single line of JSON (NDJSON).
#         Example output:
#         '{"type": "content", "data": "Hello"}\n'
#         """
#         return json.dumps({
#             "type": event_type,
#             "data": data
#         }) + "\n"


# chat_agent = ChatAgentService()        