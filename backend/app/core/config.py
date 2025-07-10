import os
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# --- Dify API Configuration ---
# IMPORTANT: The base URL has been updated as per the mission requirements.
DIFY_BASE_URL = os.getenv("DIFY_BASE_URL", "http://82.156.209.220/v1")

# It's recommended to load these from environment variables for production
DIFY_API_KEY_WORKFLOW = os.getenv("DIFY_API_KEY_WORKFLOW", "app-sYYYxIHMgLR68pRegzfg4Zel")
DIFY_API_KEY_AGENT = os.getenv("DIFY_API_KEY_AGENT", "app-EvqSJJJldKdMwVtzja9C4Gc2")
DIFY_API_KEY_SCHEMATIC = os.getenv("DIFY_API_KEY_SCHEMATIC", "app-deBVvv9f3gQAPWMrS0IZDNTS")


# --- OpenAI-Compatible API Configuration (for Deployment Guide) ---
OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-dd280b67097548a8ab1b1ccd9b767569")
OPENAI_MODEL_NAME = "deepseek-r1"

# --- Application Settings ---
PROJECT_NAME = "PCBTool Backend"
API_V1_STR = "/api/v1"

# --- Database Configuration ---
# Using SQLite for simplicity in this prototype
DATABASE_URL = "sqlite:///./pcbtool.db"

# --- User Settings ---
# A default user for the prototype to associate data with
DEFAULT_USER = "WPP_JKW"
