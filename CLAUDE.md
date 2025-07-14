# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PCBTool-Rev is an AI-powered circuit analysis and generation tool with a Vue.js frontend and FastAPI backend. It transformed from a Gradio notebook into a production web application with multi-user support, JWT authentication, and real-time AI processing through Dify platform integration.

## Development Commands

### Frontend (Vue.js + Vite)
```bash
cd frontend
npm install                # Install dependencies
npm run dev               # Start development server (http://localhost:5173)
npm run build            # Build for production
npm run preview          # Preview production build
```

### Backend (FastAPI)
```bash
cd backend
pip install -r requirements.txt --upgrade  # Install dependencies
python -m uvicorn app.main:app --reload   # Start development server (http://localhost:8000)
```

### Load Testing
```bash
python locustfile.py     # Run concurrent user simulation
```

## Architecture

### Backend Structure
- **API Layer**: `/backend/app/api/endpoints.py` - All endpoints with `/api/v1` prefix
- **Services**: Business logic in `/backend/app/services/` (dify_service, security_service, etc.)
- **Database**: SQLAlchemy models in `/backend/app/db/` with SQLite (User → Conversations → Messages)
- **Authentication**: JWT-based with 30-minute expiry, BCrypt password hashing

### Frontend Structure  
- **State Management**: Pinia stores (`auth.js`, `chat.js`) with localStorage persistence
- **Routing**: Protected routes with authentication guards
- **Components**: Modular Vue 3 Composition API components
- **Real-time**: Streaming response handling for AI generation

### Key Integrations
- **Dify AI Platform**: Multiple workflows for circuit analysis, code generation, schematics
- **Streaming Architecture**: Server-Sent Events for real-time AI responses
- **Multi-modal Input**: Text and image processing capabilities

## Important Patterns

### API Patterns
- RESTful design with streaming endpoints for real-time processing
- Dependency injection for database sessions and authentication
- Consistent error handling with proper HTTP status codes

### Database Patterns
- User data isolation with user_id-based access control
- JSON message content for flexibility
- Cascade deletion for data integrity

### Frontend Patterns
- Event-driven parent-child component communication
- Reactive state with computed properties
- Centralized API service layer with Axios interceptors

## Environment Setup

### Backend
1. Copy `.env.example` to `.env` and configure
2. Delete `pcbtool.db` if exists (for fresh schema)
3. Requires Dify API keys for AI functionality

### Frontend
1. Configured for CORS with backend
2. NVIDIA-themed UI styling
3. Auto-redirects to login if unauthenticated

## Development Workflow

1. Start backend: `python -m uvicorn app.main:app --reload`
2. Start frontend: `npm run dev` 
3. Access at `http://localhost:5173`
4. Backend API docs at `http://localhost:8000/docs`

## Key Files

- `backend/app/main.py` - FastAPI application entry
- `backend/app/api/endpoints.py` - All API endpoints
- `frontend/src/App.vue` - Main application component  
- `frontend/src/stores/` - Pinia state management
- `difyDSL/` - AI workflow YAML configurations