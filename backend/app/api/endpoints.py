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

api_router = APIRouter()


def log_to_console(message: str):
    """A simple logger for development."""
    print(message)

@api_router.post("/conversations", response_model=schemas.InitialAnalysisResponse)
async def create_conversation_and_analyze(
    text_input: str = Form(None),
    image: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    """
    Starts a new conversation by analyzing an uploaded image, text prompt, or both.
    This endpoint is flexible and handles three scenarios:
    1. Text input only.
    2. Image upload only.
    3. Both text and image.
    """
    if not text_input and not image:
        raise HTTPException(status_code=400, detail="Either text_input or an image must be provided.")

    user = crud.get_or_create_user(db, username=DEFAULT_USER)
    
    image_id = None
    temp_dir_manager = None

    try:
        if image:
            log_to_console("Processing uploaded image...")
            # Use a context manager for the temporary directory
            temp_dir_manager = tempfile.TemporaryDirectory()
            temp_dir = temp_dir_manager.__enter__()
            temp_file_path = os.path.join(temp_dir, image.filename)
            
            with open(temp_file_path, "wb") as buffer:
                shutil.copyfileobj(image.file, buffer)

            log_to_console("⏫ Uploading image to Dify...")
            image_id = dify_service.upload_file_to_dify(temp_file_path, user.username)
            if not image_id:
                raise HTTPException(status_code=500, detail="Failed to upload image to Dify.")
            log_to_console(f"✅ Image uploaded. Dify file ID: {image_id}")

        # Use provided text or a default prompt if only an image is given
        prompt = text_input if text_input else "Analyze this image."
        
        log_to_console("🚀 Calling Dify analysis workflow...")
        analysis_result = dify_service.run_initial_analysis_workflow(
            user=user.username,
            log_callback=log_to_console,
            image_id=image_id, # Can be None
            text_input=prompt  # Use the potentially modified prompt
        )

        if not analysis_result:
            raise HTTPException(status_code=500, detail="Failed to get analysis from Dify workflow.")
        log_to_console("✅ Workflow finished.")

        # Create conversation and save the first message
        conversation_title = text_input[:50] if text_input else "Image Analysis"
        conversation = crud.create_conversation(db, user_id=user.id, title=conversation_title)

        message_content = {"type": "initial_analysis", "data": analysis_result}
        message = crud.create_message(
            db,
            conversation_id=conversation.id,
            role="assistant",
            content=message_content
        )

        return {
            "conversation_id": conversation.id,
            "message": message.to_dict()
        }
    finally:
        # Ensure the temporary directory is cleaned up
        if temp_dir_manager:
            temp_dir_manager.__exit__(None, None, None)


@api_router.post("/conversations/{conversation_id}/analyze-components", response_model=schemas.Message)
async def analyze_components(
    conversation_id: int,
    analysis_message_id: int = Form(...),
    db: Session = Depends(get_db)
):
    """
    Analyzes the BOM (Bill of Materials) from a previous message.
    1.  Fetches the specified message.
    2.  Extracts the BOM text from the message content.
    3.  Uses the component_service to parse the BOM into a structured format.
    4.  Saves the structured BOM data as a new message in the conversation.
    """
    # 1. Fetch the original message containing the BOM
    source_message = crud.get_message(db, message_id=analysis_message_id)
    if not source_message or source_message.conversation_id != conversation_id:
        raise HTTPException(status_code=404, detail="Source message not found in this conversation.")

    # 2. Extract BOM text
    try:
        content = json.loads(source_message.content)
        # The key 'BOM文件' is based on the notebook's output
        bom_text = content.get("data", {}).get("BOM文件")
        if not bom_text:
            raise HTTPException(status_code=400, detail="BOM text not found in the source message.")
    except (json.JSONDecodeError, KeyError):
        raise HTTPException(status_code=400, detail="Invalid source message format.")

    # 3. Use component_service to analyze
    status_msg, df = component_service.analyze_bom_data(bom_text)
    
    # 4. Save the result as a new message
    new_message_content = {
        "type": "component_analysis",
        "data": {
            "status": status_msg,
            "components": df.to_dict(orient="records")
        }
    }
    
    new_message = crud.create_message(
        db,
        conversation_id=conversation_id,
        role="assistant",
        content=new_message_content
    )

    return new_message.to_dict()

@api_router.post("/conversations/{conversation_id}/generate-deployment-guide", response_model=schemas.DeploymentGuideResponse)
async def generate_deployment_guide(
    conversation_id: int,
    analysis_message_id: int = Form(...), # The ID of the message with BOM and ReqDoc
    db: Session = Depends(get_db)
):
    """
    Generates a deployment guide based on the requirement document and BOM.
    1.  Fetches the message with the initial analysis.
    2.  Extracts the requirement document and BOM text.
    3.  Calls the guide_service to generate the guide text.
    4.  Calls the guide_service to convert the guide text to speech.
    5.  Saves the guide and audio URL as a new message.
    """
    # 1. Fetch the message with initial analysis
    source_message = crud.get_message(db, message_id=analysis_message_id)
    if not source_message or source_message.conversation_id != conversation_id:
        raise HTTPException(status_code=404, detail="Source message not found.")

    # 2. Extract requirement doc and BOM
    try:
        content = json.loads(source_message.content)
        data = content.get("data", {})
        req_doc = data.get("需求文档")
        bom_text = data.get("BOM文件")
        if not req_doc or not bom_text:
            raise HTTPException(status_code=400, detail="ReqDoc or BOM not found in message.")
    except (json.JSONDecodeError, KeyError):
        raise HTTPException(status_code=400, detail="Invalid message format.")

    # 3. Generate guide text
    guide_text = guide_service.generate_guide_text(req_doc, bom_text)

    # 4. Generate audio
    audio_path = guide_service.convert_text_to_speech(guide_text)
    # The URL will be relative, e.g., /static/audio/guide_123.mp3
    audio_url = "/" + audio_path.replace("\\", "/") if audio_path else None


    # 5. Save as new message
    message_content = {
        "type": "deployment_guide",
        "data": {
            "text": guide_text,
            "audio_url": audio_url
        }
    }
    new_message = crud.create_message(
        db,
        conversation_id=conversation_id,
        role="assistant",
        content=message_content
    )

    return {
        "message": new_message.to_dict(),
        "audio_url": audio_url
    }

@api_router.post("/conversations/{conversation_id}/generate-code", response_model=schemas.CodeGenerationResponse)
async def generate_code(
    conversation_id: int,
    analysis_message_id: int = Form(...), # The ID of the message with BOM and ReqDoc
    db: Session = Depends(get_db)
):
    """
    Generates code using the Dify agent.
    1.  Fetches the message with the initial analysis.
    2.  Extracts the requirement document and BOM text.
    3.  Calls the Dify service to generate code from the agent.
    4.  Saves the generated code as a new message.
    """
    # 1. Fetch the message with initial analysis
    source_message = crud.get_message(db, message_id=analysis_message_id)
    if not source_message or source_message.conversation_id != conversation_id:
        raise HTTPException(status_code=404, detail="Source message not found.")

    # 2. Extract requirement doc and BOM
    try:
        content = json.loads(source_message.content)
        data = content.get("data", {})
        req_doc = data.get("需求文档")
        bom_text = data.get("BOM文件") # This contains the CSV in markdown
        if not req_doc or not bom_text:
            raise HTTPException(status_code=400, detail="ReqDoc or BOM not found in message.")
    except (json.JSONDecodeError, KeyError):
        raise HTTPException(status_code=400, detail="Invalid message format.")

    # Extract just the CSV part for the agent
    bom_csv = component_service.extract_csv_from_text(bom_text)
    if not bom_csv:
        raise HTTPException(status_code=400, detail="Could not extract CSV from BOM text.")

    # 3. Generate code
    user = crud.get_user_by_username(db, username=DEFAULT_USER)
    generated_code = dify_service.generate_code_from_agent(
        req_doc=req_doc,
        bom_csv=bom_csv,
        user=user.username,
        log_callback=log_to_console
    )

    # 4. Save as new message
    message_content = {
        "type": "generated_code",
        "data": {
            "language": "python", # Assuming python from notebook context
            "code": generated_code
        }
    }
    new_message = crud.create_message(
        db,
        conversation_id=conversation_id,
        role="assistant",
        content=message_content
    )

    return {"message": new_message.to_dict()}

@api_router.post("/conversations/{conversation_id}/generate-schematic", response_model=schemas.SchematicResponse)
async def generate_schematic(
    conversation_id: int,
    analysis_message_id: int = Form(...), # The ID of the message with BOM and ReqDoc
    db: Session = Depends(get_db)
):
    """
    Generates schematic code using a Dify workflow.
    1.  Fetches the message with the initial analysis.
    2.  Extracts the requirement document and BOM text.
    3.  Calls the Dify service to generate the schematic code.
    4.  Saves the generated code as a new message.
    """
    # 1. Fetch the message with initial analysis
    source_message = crud.get_message(db, message_id=analysis_message_id)
    if not source_message or source_message.conversation_id != conversation_id:
        raise HTTPException(status_code=404, detail="Source message not found.")

    # 2. Extract requirement doc and BOM
    try:
        content = json.loads(source_message.content)
        data = content.get("data", {})
        req_doc = data.get("需求文档")
        bom_text = data.get("BOM文件")
        if not req_doc or not bom_text:
            raise HTTPException(status_code=400, detail="ReqDoc or BOM not found in message.")
    except (json.JSONDecodeError, KeyError):
        raise HTTPException(status_code=400, detail="Invalid message format.")

    # 3. Generate schematic
    user = crud.get_user_by_username(db, username=DEFAULT_USER)
    schematic_code = dify_service.generate_schematic_from_workflow(
        req_doc=req_doc,
        bom_text=bom_text,
        user=user.username,
        log_callback=log_to_console
    )

    # 4. Save as new message
    message_content = {
        "type": "schematic_code",
        "data": {
            "language": "python", # Assuming from notebook context
            "code": schematic_code
        }
    }
    new_message = crud.create_message(
        db,
        conversation_id=conversation_id,
        role="assistant",
        content=message_content
    )

    return {"message": new_message.to_dict()}
