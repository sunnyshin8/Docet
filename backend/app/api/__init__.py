
from fastapi import APIRouter
from .ingestion import router as ingestion_router
from .chat import router as chat_router
from .training import router as training_router

router = APIRouter()

router.include_router(
    ingestion_router, 
    prefix="/ingestion", 
    tags=["Document Ingestion"]
)

router.include_router(
    chat_router, 
    prefix="/chat", 
    tags=["Chat Interface"]
)

router.include_router(
    training_router, 
    prefix="/training", 
    tags=["Model Training"]
)

@router.get("/")
async def api_root():
    return {
        "message": "Docet API v1",
        "endpoints": {
            "ingestion": "/api/v1/ingestion/",
            "chat": "/api/v1/chat/"
        }
    }