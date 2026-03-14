from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .api.routes import router
from .config.settings import settings
from .db.database import init_db, close_db
from .services.storage import init_storage
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


app = FastAPI(
    title="Auto Cut Picture API",
    description="API for image cropping and composition",
    version="1.0.0"
)


@app.on_event("startup")
async def startup_event():
    """Initialize database and storage on startup."""
    logger.info("Initializing database...")
    await init_db(settings.STORAGE_PATH)
    logger.info(f"Database initialized at: {settings.database_path}")

    # Initialize storage
    init_storage()
    logger.info("Storage initialized")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    from .services.composition_api import composition_api
    await composition_api.close()
    await close_db()
    logger.info("Application shutdown complete")


# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for serving uploaded images
storage_path = settings.STORAGE_PATH
uploads_path = settings.uploads_path
processed_path = settings.processed_path
thumbnails_path = settings.thumbnails_path

logger.info(f"Storage path: {storage_path}")
logger.info(f"Qwen API Key: {'***' + settings.QWEN_API_KEY[-4:] if settings.QWEN_API_KEY else 'Not set'}")
logger.info(f"Qwen Model: {settings.QWEN_MODEL}")

# Create directories if they don't exist
os.makedirs(uploads_path, exist_ok=True)
os.makedirs(processed_path, exist_ok=True)
os.makedirs(thumbnails_path, exist_ok=True)
logger.info(f"Directories ready: uploads={uploads_path}, processed={processed_path}, thumbnails={thumbnails_path}")

app.mount("/uploads", StaticFiles(directory=uploads_path), name="uploads")
app.mount("/processed", StaticFiles(directory=processed_path), name="processed")
app.mount("/thumbnails", StaticFiles(directory=thumbnails_path), name="thumbnails")

# Include API routes
app.include_router(router, prefix="/api")


@app.get("/")
async def root():
    return {
        "message": "Auto Cut Picture API",
        "docs": "/docs",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    )
