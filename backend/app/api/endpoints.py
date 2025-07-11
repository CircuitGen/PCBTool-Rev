from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import shutil
import os
import tempfile
import json
from typing import List
from datetime import timedelta

from app.db.database import get_db
from app.db import crud
from app.services import dify_service, component_service, guide_service, security_service
from app.models import schemas
from app.core.config import ACCESS_TOKEN_EXPIRE_MINUTES
from fastapi.responses import StreamingResponse
import asyncio

class AnalysisRequestBody(schemas.BaseModel):
    analysis_message_id: int

api_router = APIRouter()

# --- Authentication Endpoints ---

@api_router.post("/token", response_model=schemas.Token, tags=["Authentication"])
async def login_for_access_token(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    user = crud.authenticate_user(db, username=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security_service.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@api_router.post("/users/register", response_model=schemas.User, tags=["Authentication"])
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return crud.create_user(db=db, user=user)

# --- Conversation Endpoints ---

async def stream_initial_analysis(db: Session, user: schemas.User, image_id: str | None, text_input: str | None):
    final_outputs = {}
    async for chunk in dify_service.run_initial_analysis_workflow_stream(user.username, image_id, text_input):
        yield f"data: {chunk}\n\n"
        try:
            data = json.loads(chunk)
            if data.get("event") == "workflow_finished":
                final_outputs = data.get("data", {}).get("outputs", {})
        except json.JSONDecodeError:
            continue
    if not final_outputs:
        error_event = {"event": "error", "message": "Workflow failed to produce final output."}
        yield f"data: {json.dumps(error_event)}\n\n"
        return
    conversation_title = text_input[:50] if text_input else "Image Analysis"
    conversation = crud.create_conversation(db, user_id=user.id, title=conversation_title)
    message_content = {"type": "initial_analysis", "data": final_outputs}
    new_message = crud.create_message(db, conversation_id=conversation.id, role="assistant", content=message_content)
    final_event = {"event": "conversation_created", "conversation_id": conversation.id, "message_content": message_content, "message_id": new_message.id}
    yield f"data: {json.dumps(final_event)}\n\n"

@api_router.post("/conversations/stream", tags=["Conversations"])
async def stream_create_conversation_and_analyze(
    text_input: str = Form(None),
    image: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(security_service.get_current_user)
):
    if not text_input and not image:
        raise HTTPException(status_code=400, detail="Either text_input or an image must be provided.")
    
    image_id = None
    temp_dir = tempfile.TemporaryDirectory()
    if image:
        temp_file_path = os.path.join(temp_dir.name, image.filename)
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        image_id = dify_service.upload_file_to_dify(temp_file_path, current_user.username)
        if not image_id:
            temp_dir.cleanup()
            raise HTTPException(status_code=500, detail="Failed to upload image to Dify.")

    prompt = text_input if text_input else "Analyze this image."
    
    async def generator_wrapper():
        try:
            async for chunk in stream_initial_analysis(db, current_user, image_id, prompt):
                yield chunk
        finally:
            temp_dir.cleanup()

    return StreamingResponse(generator_wrapper(), media_type="text/event-stream")

@api_router.get("/conversations", response_model=List[schemas.Conversation], tags=["Conversations"])
async def get_conversation_history(
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(security_service.get_current_user)
):
    return crud.get_conversations_by_user(db, user_id=current_user.id)

@api_router.delete("/conversations/{conversation_id}", status_code=204, tags=["Conversations"])
async def delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(security_service.get_current_user)
):
    db_conversation = crud.delete_conversation(db, conversation_id=conversation_id, user_id=current_user.id)
    if not db_conversation:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return None

@api_router.post("/conversations/{conversation_id}/analyze-components", response_model=schemas.MessageResponse, tags=["Conversations"])
async def analyze_components(
    conversation_id: int,
    body: AnalysisRequestBody,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(security_service.get_current_user)
):
    source_message = crud.get_message(db, message_id=body.analysis_message_id)
    if not source_message or source_message.conversation.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Source message not found.")
    
    try:
        content = json.loads(source_message.content)
        data = content.get("data", {})
        bom_text = data.get("BOM文件")
        req_doc = data.get("需求文档")
        if not bom_text or not req_doc:
            raise HTTPException(status_code=400, detail="BOM text or ReqDoc not found in the source message.")
    except (json.JSONDecodeError, KeyError):
        raise HTTPException(status_code=400, detail="Invalid source message format.")

    status_msg, df = component_service.analyze_bom_data(bom_text)
    
    new_message_content = {
        "type": "component_analysis",
        "data": {
            "status": status_msg,
            "components": df.to_dict(orient="records"),
            "BOM文件": bom_text,
            "需求文档": req_doc
        }
    }
    
    new_message = crud.create_message(db, conversation_id=conversation_id, role="assistant", content=new_message_content)
    return new_message.to_dict()
    
@api_router.post("/conversations/{conversation_id}/generate-code/stream", tags=["Conversations"])
async def stream_generate_code(
    conversation_id: int,
    body: AnalysisRequestBody,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(security_service.get_current_user)
):
    source_message = crud.get_message(db, message_id=body.analysis_message_id)
    if not source_message or source_message.conversation.user_id != current_user.id:
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

    async def generator():
        full_response = ""
        async for chunk in dify_service.run_code_generation_stream(current_user.username, req_doc, bom_csv):
            yield f"data: {chunk}\n\n"
            try:
                event_data = json.loads(chunk)
                if event_data.get('event') in ['message', 'agent_message']:
                    full_response += event_data.get('answer', '')
            except:
                continue
        
        message_content = {"type": "generated_code", "data": {"language": "python", "code": full_response}}
        crud.create_message(db, conversation_id=conversation_id, role="assistant", content=message_content)
        final_event = {"event": "final_message", "content": message_content}
        yield f"data: {json.dumps(final_event)}\n\n"

    return StreamingResponse(generator(), media_type="text/event-stream")

@api_router.post("/conversations/{conversation_id}/generate-deployment-guide/stream", tags=["Conversations"])
async def stream_generate_deployment_guide(
    conversation_id: int,
    body: AnalysisRequestBody,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(security_service.get_current_user)
):
    source_message = crud.get_message(db, message_id=body.analysis_message_id)
    if not source_message or source_message.conversation.user_id != current_user.id:
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

    guide_text = guide_service.generate_guide_text(req_doc, bom_text)
    audio_path = guide_service.convert_text_to_speech(guide_text)
    audio_url = "/" + audio_path.replace("\\", "/") if audio_path else None

    message_content = {"type": "deployment_guide", "data": {"text": guide_text, "audio_url": audio_url}}
    crud.create_message(db, conversation_id=conversation_id, role="assistant", content=message_content)
    
    async def generator():
        final_event = {"event": "final_message", "content": message_content}
        yield f"data: {json.dumps(final_event)}\n\n"

    return StreamingResponse(generator(), media_type="text/event-stream")

@api_router.post("/conversations/{conversation_id}/generate-schematic/stream", tags=["Conversations"])
async def stream_generate_schematic(
    conversation_id: int,
    body: AnalysisRequestBody,
    db: Session = Depends(get_db),
    current_user: schemas.User = Depends(security_service.get_current_user)
):
    source_message = crud.get_message(db, message_id=body.analysis_message_id)
    if not source_message or source_message.conversation.user_id != current_user.id:
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

    async def generator():
        final_outputs = {}
        async for chunk in dify_service.run_schematic_generation_stream(current_user.username, req_doc, bom_text):
            yield f"data: {chunk}\n\n"
            try:
                data = json.loads(chunk)
                if data.get("event") == "workflow_finished":
                    final_outputs = data.get("data", {}).get("outputs", {})
            except:
                continue
        
        schematic_code = final_outputs.get("picpic", "Schematic generation failed.")
        message_content = {"type": "schematic_code", "data": {"language": "python", "code": schematic_code}}
        crud.create_message(db, conversation_id=conversation_id, role="assistant", content=message_content)
        final_event = {"event": "final_message", "content": message_content}
        yield f"data: {json.dumps(final_event)}\n\n"

    return StreamingResponse(generator(), media_type="text/event-stream")