from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import PROJECT_NAME
from app.db import models
from app.db.database import engine
from app.api.endpoints import api_router

# Create all database tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title=PROJECT_NAME)

# Mount static files directory (only if directory exists)
import os
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

# Define allowed origins
# In production, replace "http://your_domain.com" with your actual frontend URL.
origins = [
    "http://localhost:5173",  # Local Vue dev server
    "http://120.27.135.185",  # Your production domain
    "https://pcbtoolfrontend.vercel.app",  # Vercel frontend domain
    "*",  # Allow all origins for development/testing
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": f"Welcome to {PROJECT_NAME}"}