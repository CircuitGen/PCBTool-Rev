from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
import shutil
import os
import tempfile
import json

from app.db.database import get_db
from app.db import crud
from app.services import dify_service, component_service, guide_service
from app.models import schemas
from app.core.config import DEFAULT_USER

class AnalysisRequestBody(schemas.BaseModel):
    analysis_message_id: int

api_router = APIRouter()



def log_to_console(message: str):
    """A simple logger for development."""
    print(message)

from fastapi.responses import StreamingResponse
import asyncio

# ... (other imports)

# ... (AnalysisRequestBody class)

async def stream_initial_analysis(db: Session, user: schemas.User, image_id: str | None, text_input: str | None):
    """
    Async generator that streams Dify analysis, saves the final result, and yields events.
    """
    # Step 1: Stream from Dify and yield progress
    final_outputs = {}
    async for chunk in dify_service.run_initial_analysis_workflow_stream(user.username, image_id, text_input):
        yield f"data: {chunk}\n\n"
        
        # Accumulate final results from the 'workflow_finished' event
        try:
            data = json.loads(chunk)
            if data.get("event") == "workflow_finished":
                final_outputs = data.get("data", {}).get("outputs", {})
        except json.JSONDecodeError:
            continue # Ignore parsing errors for non-final events

    # Step 2: Once streaming is done, save to DB
    if not final_outputs:
        # Handle case where workflow fails
        error_event = {"event": "error", "message": "Workflow failed to produce final output."}
        yield f"data: {json.dumps(error_event)}\n\n"
        return

    conversation_title = text_input[:50] if text_input else "Image Analysis"
    conversation = crud.create_conversation(db, user_id=user.id, title=conversation_title)

    message_content = {"type": "initial_analysis", "data": final_outputs}
    crud.create_message(
        db,
        conversation_id=conversation.id,
        role="assistant",
        content=message_content
    )
    
    # Step 3: Yield a final custom event with the new conversation ID
    final_event = {
        "event": "conversation_created",
        "conversation_id": conversation.id,
        "message_content": message_content
    }
    yield f"data: {json.dumps(final_event)}\n\n"


@api_router.post("/conversations/stream")
async def stream_create_conversation_and_analyze(
    text_input: str = Form(None),
    image: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    if not text_input and not image:
        raise HTTPException(status_code=400, detail="Either text_input or an image must be provided.")

    user = crud.get_or_create_user(db, username=DEFAULT_USER)
    
    image_id = None
    temp_file_path = None
    temp_dir = tempfile.TemporaryDirectory()

    if image:
        temp_file_path = os.path.join(temp_dir.name, image.filename)
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        image_id = dify_service.upload_file_to_dify(temp_file_path, user.username)
        if not image_id:
            temp_dir.cleanup()
            raise HTTPException(status_code=500, detail="Failed to upload image to Dify.")

    prompt = text_input if text_input else "Analyze this image."
    
    # The generator function needs to be wrapped to clean up the temp dir
    async def generator_wrapper():
        try:
            async for chunk in stream_initial_analysis(db, user, image_id, prompt):
                yield chunk
        finally:
            temp_dir.cleanup()

    return StreamingResponse(generator_wrapper(), media_type="text/event-stream")


@api_router.post("/conversations/{conversation_id}/analyze-components", response_model=schemas.MessageResponse)
async def analyze_components(
    conversation_id: int,
    body: AnalysisRequestBody,
    db: Session = Depends(get_db)
):
    """
    Analyzes the BOM (Bill of Materials) from a previous message.
    """
    source_message = crud.get_message(db, message_id=body.analysis_message_id)
    if not source_message or source_message.conversation_id != conversation_id:
        raise HTTPException(status_code=404, detail="Source message not found in this conversation.")

    # Extract BOM text and ReqDoc from the source message
    try:
        content = json.loads(source_message.content)
        data = content.get("data", {})
        bom_text = data.get("BOM文件")
        req_doc = data.get("需求文档")
        if not bom_text or not req_doc:
            raise HTTPException(status_code=400, detail="BOM text or ReqDoc not found in the source message.")
    except (json.JSONDecodeError, KeyError):
        raise HTTPException(status_code=400, detail="Invalid source message format.")

    # 3. Use component_service to analyze
    status_msg, df = component_service.analyze_bom_data(bom_text)
    
    # 4. Save the result as a new message, including the original data for subsequent steps
    new_message_content = {
        "type": "component_analysis",
        "data": {
            "status": status_msg,
            "components": df.to_dict(orient="records"),
            # Carry forward the original data
            "BOM文件": bom_text,
            "需求文档": req_doc
        }
    }
    
    new_message = crud.create_message(
        db,
        conversation_id=conversation_id,
        role="assistant",
        content=new_message_content
    )

    return new_message.to_dict()

@api_router.post("/conversations/{conversation_id}/generate-deployment-guide/stream")
async def stream_generate_deployment_guide(
    conversation_id: int,
    body: AnalysisRequestBody,
    db: Session = Depends(get_db)
):
    """
    Streams the deployment guide generation process.
    """
    source_message = crud.get_message(db, message_id=body.analysis_message_id)
    if not source_message or source_message.conversation_id != conversation_id:
        raise HTTPException(status_code=404, detail="Source message not found.")

    try:
        content = json.loads(source_message.content)
        data = content.get("data", {})
        req_doc = data.get("需求文档")
        bom_text = data.get("BOM文件")
        if not req_doc or not bom_text:
            raise HTTPException(status_code=400, detail="ReqDoc or BOM not found in message.")
    except (json.JSONDecodeError, KeyError):
        raise HTTPException(status_code=400, detail="Invalid message format.")

    # This service is not streaming, so we generate the content first
    guide_text = guide_service.generate_guide_text(req_doc, bom_text)
    audio_path = guide_service.convert_text_to_speech(guide_text)
    audio_url = "/" + audio_path.replace("\\", "/") if audio_path else None

    message_content = {
        "type": "deployment_guide",
        "data": {"text": guide_text, "audio_url": audio_url}
    }
    crud.create_message(db, conversation_id=conversation_id, role="assistant", content=message_content)
    
    async def generator():
        final_event = {"event": "final_message", "content": message_content}
        yield f"data: {json.dumps(final_event)}\n\n"

    return StreamingResponse(generator(), media_type="text/event-stream")


@api_router.get("/conversations", response_model=list[schemas.Conversation])
async def get_conversation_history(db: Session = Depends(get_db)):
    """
    Retrieves the full conversation history for the default user.
    """
    user = crud.get_or_create_user(db, username=DEFAULT_USER)
    conversations = crud.get_conversations_by_user(db, user_id=user.id)
    return conversations

@api_router.delete("/conversations/{conversation_id}", status_code=204)
async def delete_conversation(conversation_id: int, db: Session = Depends(get_db)):
    """
    Deletes a specific conversation.
    """
    user = crud.get_or_create_user(db, username=DEFAULT_USER)
    db_conversation = crud.delete_conversation(db, conversation_id=conversation_id, user_id=user.id)
    
    if not db_conversation:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    
    return None # No content response

@api_router.post("/conversations/{conversation_id}/generate-code/stream")
async def stream_generate_code(
    conversation_id: int,
    body: AnalysisRequestBody,
    db: Session = Depends(get_db)
):
    """
    Streams the code generation process.
    """
    source_message = crud.get_message(db, message_id=body.analysis_message_id)
    if not source_message or source_message.conversation_id != conversation_id:
        raise HTTPException(status_code=404, detail="Source message not found.")

    try:
        content = json.loads(source_message.content)
        data = content.get("data", {})
        req_doc = data.get("需求文档")
        bom_text = data.get("BOM文件")
        if not req_doc or not bom_text:
            raise HTTPException(status_code=400, detail="ReqDoc or BOM not found in message.")
    except (json.JSONDecodeError, KeyError):
        raise HTTPException(status_code=400, detail="Invalid message format.")

    bom_csv = component_service.extract_csv_from_text(bom_text)
    if not bom_csv:
        raise HTTPException(status_code=400, detail="Could not extract CSV from BOM text.")
    
    user = crud.get_user_by_username(db, username=DEFAULT_USER)

    async def generator():
        full_response = ""
        async for chunk in dify_service.run_code_generation_stream(user.username, req_doc, bom_csv):
            yield f"data: {chunk}\n\n"
            try:
                event_data = json.loads(chunk)
                if event_data.get('event') in ['message', 'agent_message']:
                    full_response += event_data.get('answer', '')
            except:
                continue
        
        # Save final message
        message_content = {"type": "generated_code", "data": {"language": "python", "code": full_response}}
        crud.create_message(db, conversation_id=conversation_id, role="assistant", content=message_content)
        final_event = {"event": "final_message", "content": message_content}
        yield f"data: {json.dumps(final_event)}\n\n"

    return StreamingResponse(generator(), media_type="text/event-stream")


@api_router.post("/conversations/{conversation_id}/generate-schematic/stream")
async def stream_generate_schematic(
    conversation_id: int,
    body: AnalysisRequestBody,
    db: Session = Depends(get_db)
):
    """
    Streams the schematic generation process.
    """
    source_message = crud.get_message(db, message_id=body.analysis_message_id)
    if not source_message or source_message.conversation_id != conversation_id:
        raise HTTPException(status_code=404, detail="Source message not found.")

    try:
        content = json.loads(source_message.content)
        data = content.get("data", {})
        req_doc = data.get("需求文档")
        bom_text = data.get("BOM文件")
        if not req_doc or not bom_text:
            raise HTTPException(status_code=400, detail="ReqDoc or BOM not found in message.")
    except (json.JSONDecodeError, KeyError):
        raise HTTPException(status_code=400, detail="Invalid message format.")
    
    user = crud.get_user_by_username(db, username=DEFAULT_USER)

    async def generator():
        final_outputs = {}
        async for chunk in dify_service.run_schematic_generation_stream(user.username, req_doc, bom_text):
            yield f"data: {chunk}\n\n"
            try:
                data = json.loads(chunk)
                if data.get("event") == "workflow_finished":
                    final_outputs = data.get("data", {}).get("outputs", {})
            except:
                continue
        
        # Save final message
        schematic_code = final_outputs.get("picpic", "Schematic generation failed.")
        message_content = {"type": "schematic_code", "data": {"language": "python", "code": schematic_code}}
        crud.create_message(db, conversation_id=conversation_id, role="assistant", content=message_content)
        final_event = {"event": "final_message", "content": message_content}
        yield f"data: {json.dumps(final_event)}\n\n"

    return StreamingResponse(generator(), media_type="text/event-stream")

