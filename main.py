# main.py
"""
DocuReview Pro - Main FastAPI Application
Enterprise Document Version Management & Analysis System
"""
import os
import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pathlib import Path

# Import routers
from routers import documents, comparison, search, admin
from database import init_database
from config import Config

# Initialize FastAPI app
app = FastAPI(
    title=Config.APP_NAME,
    version=Config.APP_VERSION,
    description="Enterprise Document Version Management & Analysis System",
    docs_url="/api/docs" if Config.DEBUG else None,
    redoc_url="/api/redoc" if Config.DEBUG else None
)

# Configure CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(comparison.router, prefix="/api/comparison", tags=["Comparison"])
app.include_router(search.router, prefix="/api/search", tags=["Search"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])

# Serve static files
frontend_path = Path(__file__).parent / "frontend" / "dist"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path / "static")), name="static")

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    print(f"🚀 Starting {Config.APP_NAME} v{Config.APP_VERSION}")
    
    # Validate configuration
    Config.validate_config()
    
    # Initialize database
    init_database()
    
    # Ensure upload folder exists
    Config.ensure_upload_folder()
    
    print(f"✅ Application initialized successfully")
    print(f"📊 Database: {Config.get_database_path()}")
    print(f"📁 Upload folder: {Config.ensure_upload_folder()}")

@app.get("/")
async def root():
    """Serve React frontend"""
    if frontend_path.exists():
        return FileResponse(str(frontend_path / "index.html"))
    return {"message": f"Welcome to {Config.APP_NAME} API", "version": Config.APP_VERSION}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "app": Config.APP_NAME,
        "version": Config.APP_VERSION,
        "database": "connected" if Path(Config.DB_PATH).exists() else "not_found"
    }

# Catch-all route for React Router
@app.get("/{path:path}")
async def catch_all(path: str):
    """Serve React app for all routes (SPA support)"""
    if frontend_path.exists() and not path.startswith("api"):
        return FileResponse(str(frontend_path / "index.html"))
    return {"error": "Not found"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=Config.HOST,
        port=Config.PORT,
        reload=Config.DEBUG,
        log_level="info"
    )
