import json
import asyncio
import logging
from typing import List, Dict, Any, AsyncGenerator
from groq import Groq
from app.core.config import settings
from app.core.exceptions import LLMError

# --- Constants & Prompts ---

SYSTEM_PROMPT_QA = """You are a precise and concise AI assistant. 
Your task is to answer the user's question using ONLY the provided context.

RULES:
1. Cite sources inline like this: [Page 3] or [0:42].
2. If the context is insufficient, say: "I don't have enough context." Do not hallucinate.
3. Be direct. No filler phrases like "Based on the text" or "According to the context".
4. Use a professional, neutral tone.
"""

SYSTEM_PROMPT_SUMMARY = """Summarize the provided document content. 
Structure your response as a JSON object with:
- "summary": A concise paragraph (max 150 words).
- "key_topics": An array of 3-5 major themes or entities.
- "word_count": Integer count of words in the summary.
"""

SYSTEM_PROMPT_CHAPTERS = """Identify logical chapters or segments in this transcript.
Structure your response as a JSON array of objects, each with:
- "title": Descriptive chapter name.
- "start_time": Seconds from start (float).
- "end_time": Seconds from start (float).
"""

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model_id = "llama-3.3-70b-versatile"

    async def get_chat_response_stream(
        self, messages: List[Dict[str, str]], context_chunks: List[Dict[str, Any]]
    ) -> AsyncGenerator[str, None]:
        """
        Streams Groq response as SSE tokens and metadata.
        """
        # 1. Build context string
        context_str = ""
        for i, chunk in enumerate(context_chunks):
            source = f"Source {i+1}"
            if chunk.get("page_number"):
                source = f"Page {chunk['page_number']}"
            elif chunk.get("start_time") is not None:
                source = f"{int(chunk['start_time'])}s"

            context_str += f"\n[{source}]: {chunk['text_preview']}\n"

        # 2. Build Groq messages
        groq_messages = [
            {
                "role": "system",
                "content": f"{SYSTEM_PROMPT_QA}\n\nCONTEXT:\n{context_str}",
            }
        ]
        groq_messages.extend(messages)

        try:
            # 3. Stream tokens (blocking SDK call wrapped in aio)
            # Groq doesn't have an async client in the basic SDK yet, but we can use threading
            def groq_stream():
                return self.client.chat.completions.create(
                    model=self.model_id,
                    messages=groq_messages,
                    temperature=0.2,
                    max_tokens=1024,
                    stream=True,
                )

            completion = await asyncio.to_thread(groq_stream)

            for chunk in completion:
                token = chunk.choices[0].delta.content
                if token:
                    yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
                    await asyncio.sleep(0)

            # 4. Final metadata event
            sources = []
            for c in context_chunks:
                sources.append(
                    {
                        "page_number": c.get("page_number"),
                        "start_time": c.get("start_time"),
                        "end_time": c.get("end_time"),
                    }
                )
            yield f"data: {json.dumps({'type': 'metadata', 'sources': sources})}\n\n"

        except Exception as e:
            logger.error(f"Groq Chat Error: {str(e)}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    async def get_summary(self, chunk_texts: List[str]) -> Dict[str, Any]:
        """
        Generates a summary using Groq.
        """
        full_text = "\n".join(chunk_texts)[
            :15000
        ]  # Groq has smaller window than Gemini
        prompt = f"{SYSTEM_PROMPT_SUMMARY}\n\nDOCUMENT CONTENT:\n{full_text}"

        try:

            def groq_call():
                return self.client.chat.completions.create(
                    model=self.model_id,
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"},
                    temperature=0.2,
                    max_tokens=1000,
                    stream=False,
                )

            response = await asyncio.to_thread(groq_call)
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"Groq Summary Error: {str(e)}")
            raise LLMError(f"Failed to generate summary: {str(e)}")

    async def generate_chapter_markers(self, transcript: str) -> List[Dict[str, Any]]:
        """
        Segments a transcript into logical chapters using Groq.
        """
        prompt = f"{SYSTEM_PROMPT_CHAPTERS}\n\nTRANSCRIPT:\n{transcript[:15000]}"

        try:

            def groq_call():
                return self.client.chat.completions.create(
                    model=self.model_id,
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"},
                    temperature=0.2,
                    max_tokens=1000,
                    stream=False,
                )

            response = await asyncio.to_thread(groq_call)
            data = json.loads(response.choices[0].message.content)
            # If Groq returns a nested object, extract the list
            if isinstance(data, dict):
                for key in data:
                    if isinstance(data[key], list):
                        return data[key]
            return data if isinstance(data, list) else []
        except Exception as e:
            logger.error(f"Groq Chapters Error: {str(e)}")
            raise LLMError(f"Failed to generate chapters: {str(e)}")


llm_service = LLMService()
