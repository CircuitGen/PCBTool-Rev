from openai import OpenAI
from gtts import gTTS
import os
import time
from typing import Dict, Any

from app.core.config import OPENAI_API_BASE, OPENAI_API_KEY, OPENAI_MODEL_NAME

# Ensure a directory exists for saving audio files
AUDIO_DIR = "static/audio"
os.makedirs(AUDIO_DIR, exist_ok=True)

def generate_guide_text(requirement_doc: str, bom_data: str) -> str:
    """
    Generates a deployment guide using an OpenAI-compatible API.
    """
    client = OpenAI(
        base_url=OPENAI_API_BASE,
        api_key=OPENAI_API_KEY
    )
    
    prompt = f"""【Deployment Guide Generation】
Based on the following requirement document:
{requirement_doc}

And the following BOM data:
{bom_data}

Please generate a detailed deployment guide of about 500 words, explaining the deployment steps, environmental requirements, and precautions. Optimize the deployment plan and provide detailed tips.
"""
    
    try:
        completion = client.chat.completions.create(
            model=OPENAI_MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            top_p=0.7,
            stream=False # Using non-streaming for simplicity here
        )
        guide_text = completion.choices[0].message.content
        return guide_text.strip()
    except Exception as e:
        print(f"Error generating deployment guide: {e}")
        return "Failed to generate deployment guide."

def convert_text_to_speech(text: str) -> str | None:
    """
    Converts text to speech and saves it as an MP3 file.
    Returns the path to the audio file.
    """
    try:
        tts = gTTS(text=text, lang='zh-CN')
        timestamp = int(time.time())
        filename = f"guide_{timestamp}.mp3"
        filepath = os.path.join(AUDIO_DIR, filename)
        
        tts.save(filepath)
        
        # In a real app, you might want a better cleanup strategy
        # for old files, but this is fine for the prototype.
        
        return filepath
    except Exception as e:
        print(f"Error converting text to speech: {e}")
        return None
