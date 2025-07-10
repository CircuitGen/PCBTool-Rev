import requests
import json
import os
import mimetypes
from typing import Callable, Dict, Any, AsyncGenerator
import httpx

from app.core.config import (
    DIFY_BASE_URL,
    DIFY_API_KEY_WORKFLOW,
    DIFY_API_KEY_AGENT,
    DIFY_API_KEY_SCHEMATIC,
)

UPLOAD_URL = f"{DIFY_BASE_URL}/files/upload"
WORKFLOW_URL = f"{DIFY_BASE_URL}/workflows/run"
CHAT_URL = f"{DIFY_BASE_URL}/chat-messages"


def upload_file_to_dify(file_path: str, user: str) -> str | None:
    """
    Uploads a file to Dify and returns the file ID.
    """
    try:
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            mime_type = "application/octet-stream"

        with open(file_path, "rb") as f:
            files = {"file": (os.path.basename(file_path), f, mime_type)}
            data = {"user": user}
            headers = {"Authorization": f"Bearer {DIFY_API_KEY_WORKFLOW}"}
            
            response = requests.post(UPLOAD_URL, headers=headers, files=files, data=data)
            response.raise_for_status()
            return response.json().get("id")
    except Exception as e:
        print(f"❌ File upload failed: {str(e)}")
        return None


async def _stream_dify_request(url: str, payload: Dict[str, Any], api_key: str) -> AsyncGenerator[str, None]:
    """
    A generic async generator to stream responses from a Dify endpoint (Workflow or Chat).
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "text/event-stream",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            async with client.stream("POST", url, headers=headers, json=payload, timeout=180) as response:
                response.raise_for_status()
                async for raw_line in response.aiter_lines():
                    if not raw_line or raw_line.startswith(': ping'):
                        continue
                    
                    if raw_line.startswith('data:'):
                        json_str = raw_line[5:].strip()
                        if json_str:
                            yield json_str
        except httpx.HTTPStatusError as e:
            print(f"❌ Dify stream request failed: {e.response.text}")
            yield json.dumps({"event": "error", "message": "Dify request failed."})
        except Exception as e:
            print(f"❌ An unexpected error occurred during streaming: {str(e)}")
            yield json.dumps({"event": "error", "message": "An unexpected error occurred."})


async def run_initial_analysis_workflow_stream(user: str, image_id: str | None = None, text_input: str | None = None) -> AsyncGenerator[str, None]:
    """
    Streams the initial Dify workflow for image and/or text analysis.
    """
    inputs = {}
    if image_id:
        inputs["image"] = {"transfer_method": "local_file", "upload_file_id": image_id, "type": "image"}
    if text_input:
        inputs["text_in"] = text_input

    payload = {"inputs": inputs, "response_mode": "streaming", "user": user}
    async for chunk in _stream_dify_request(WORKFLOW_URL, payload, DIFY_API_KEY_WORKFLOW):
        yield chunk


async def run_code_generation_stream(user: str, req_doc: str, bom_csv: str) -> AsyncGenerator[str, None]:
    """
    Streams the Dify chat agent for code generation.
    """
    payload = {
        "inputs": {"requirement_document": req_doc, "bom_list": bom_csv},
        "query": "Please generate the corresponding code based on the requirement document and BOM list.",
        "response_mode": "streaming",
        "user": user,
    }
    async for chunk in _stream_dify_request(CHAT_URL, payload, DIFY_API_KEY_AGENT):
        yield chunk


async def run_schematic_generation_stream(user: str, req_doc: str, bom_text: str) -> AsyncGenerator[str, None]:
    """
    Streams the Dify workflow for schematic generation.
    """
    payload = {
        "inputs": {"requirement": req_doc, "bom": bom_text},
        "response_mode": "streaming",
        "user": user
    }
    async for chunk in _stream_dify_request(WORKFLOW_URL, payload, DIFY_API_KEY_SCHEMATIC):
        yield chunk
