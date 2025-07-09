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

# Mount static files directory
app.mount("/static", StaticFiles(directory="static"), name="static")


# Set up CORS
# In a production environment, you should restrict the origins.
# For this prototype, we'll allow all origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": f"Welcome to {PROJECT_NAME}"}

