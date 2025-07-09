import requests
import json
import os
import mimetypes
from typing import Callable, Dict, Any

from app.core.config import (
    DIFY_BASE_URL,
    DIFY_API_KEY_WORKFLOW,
    DIFY_API_KEY_AGENT,
    DIFY_API_KEY_SCHEMATIC,
    DEFAULT_USER
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
        # In a real app, you'd use proper logging
        return None


def process_workflow_stream(response: requests.Response, log_callback: Callable[[str], None]) -> Dict[str, Any]:
    """
    Processes a streaming response from a Dify workflow.
    """
    outputs = {}
    log_callback("🔄 Dify workflow stream started.")
    try:
        for raw_line in response.iter_lines():
            if not raw_line or raw_line.startswith(b': ping'):
                continue
            
            decoded_line = raw_line.decode('utf-8').strip()
            if not decoded_line.startswith('data:'):
                continue

            json_str = decoded_line[5:].strip()
            if not json_str:
                continue
            
            try:
                event_data = json.loads(json_str)
                event = event_data.get("event")

                if event == "node_started":
                    log_callback(f"▷ Node started: {event_data.get('data', {}).get('title', 'Unknown')}")
                elif event == "node_finished":
                    status = event_data.get('data', {}).get('status', 'unknown')
                    icon = "✓" if status == "succeeded" else "✗"
                    log_callback(f"{icon} Node finished: {status}")
                elif event == "workflow_finished":
                    log_callback("��� Workflow finished.")
                    outputs = event_data.get("data", {}).get("outputs", {})
                    return {k: v or "" for k, v in outputs.items()}

            except json.JSONDecodeError:
                log_callback(f"⚠ JSON parsing failed for line: {json_str[:100]}...")
            except KeyError as e:
                log_callback(f"⚠ Data field missing: {str(e)}")

    except requests.exceptions.ChunkedEncodingError as e:
        log_callback(f"⚠ Network connection error: {str(e)}")
    except Exception as e:
        log_callback(f"⚠ An unexpected error occurred: {str(e)}")
    
    return outputs


def run_initial_analysis_workflow(user: str, log_callback: Callable[[str], None], image_id: str | None = None, text_input: str | None = None) -> Dict[str, Any]:
    """
    Runs the initial Dify workflow for image and/or text analysis.
    Dynamically builds the payload based on provided inputs.
    """
    headers = {
        "Authorization": f"Bearer {DIFY_API_KEY_WORKFLOW}",
        "Accept": "text/event-stream",
        "Content-Type": "application/json"
    }
    
    inputs = {}
    if image_id:
        inputs["image"] = {
            "transfer_method": "local_file",
            "upload_file_id": image_id,
            "type": "image"
        }
    if text_input:
        inputs["text_in"] = text_input

    payload = {
        "inputs": inputs,
        "response_mode": "streaming",
        "user": user
    }

    try:
        log_callback("🚀 Starting Dify workflow request...")
        with requests.post(WORKFLOW_URL, headers=headers, json=payload, stream=True, timeout=180) as resp:
            resp.raise_for_status()
            result = process_workflow_stream(resp, log_callback)
            return result
    except requests.exceptions.RequestException as e:
        log_callback(f"❌ Request to Dify workflow failed: {str(e)}")
        return {}

def generate_code_from_agent(req_doc: str, bom_csv: str, user: str, log_callback: Callable[[str], None]) -> str:
    """
    Calls the Dify chat agent to generate code.
    """
    headers = {
        "Authorization": f"Bearer {DIFY_API_KEY_AGENT}",
        "Content-Type": "application/json"
    }
    payload = {
        "inputs": {
            "requirement_document": req_doc,
            "bom_list": bom_csv
        },
        "query": "Please generate the corresponding code based on the requirement document and BOM list.",
        "response_mode": "streaming",
        "user": user,
    }

    full_response = ""
    log_callback("🚀 Calling Dify agent for code generation...")
    try:
        with requests.post(CHAT_URL, headers=headers, json=payload, stream=True, timeout=180) as response:
            response.raise_for_status()
            for line in response.iter_lines():
                if not line:
                    continue
                
                decoded_line = line.decode('utf-8')
                if not decoded_line.startswith('data:'):
                    continue

                json_str = decoded_line.split('data: ', 1)[1]
                try:
                    event_data = json.loads(json_str)
                    event_type = event_data.get('event')
                    
                    if event_type in ['message', 'agent_message']:
                        full_response += event_data.get('answer', '')
                    elif event_type == 'message_end':
                        log_callback("✅ Agent finished generating code.")
                        break
                    elif event_type == 'error':
                        raise Exception(f"API Error: {event_data.get('message')}")
                except json.JSONDecodeError:
                    log_callback(f"⚠ JSON parsing failed for line: {json_str[:100]}...")

    except requests.RequestException as e:
        log_callback(f"❌ Request to Dify agent failed: {e}")
        return "Error: Request to Dify agent failed."
    except Exception as e:
        log_callback(f"❌ An error occurred during code generation: {e}")
        return f"Error: {e}"
        
    return full_response

def generate_schematic_from_workflow(req_doc: str, bom_text: str, user: str, log_callback: Callable[[str], None]) -> str:
    """
    Runs the Dify workflow to generate schematic code.
    """
    headers = {
        "Authorization": f"Bearer {DIFY_API_KEY_SCHEMATIC}",
        "Accept": "text/event-stream",
        "Content-Type": "application/json"
    }
    payload = {
        "inputs": {
            "requirement": req_doc,
            "bom": bom_text
        },
        "response_mode": "streaming",
        "user": user
    }

    log_callback("🚀 Calling Dify workflow for schematic generation...")
    try:
        with requests.post(WORKFLOW_URL, headers=headers, json=payload, stream=True, timeout=180) as resp:
            resp.raise_for_status()
            # The process_workflow_stream function can be reused here
            result = process_workflow_stream(resp, log_callback)
            # The output key 'picpic' is based on the notebook
            return result.get("picpic", "Schematic generation failed: 'picpic' key not in output.")
    except requests.exceptions.RequestException as e:
        log_callback(f"❌ Request to Dify schematic workflow failed: {str(e)}")
        return "Error: Request to Dify schematic workflow failed."
