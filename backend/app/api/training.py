
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import asyncio
import json

from ..llm.local_service import local_llm_service
from ..storage.local import local_storage_service

router = APIRouter()


class TrainingRequest(BaseModel):
    documents: Optional[List[str]] = None
    learning_rate: float = 5e-4
    num_epochs: int = 3
    batch_size: int = 4


class TrainingStatus(BaseModel):
    job_id: str
    status: str
    progress: float
    message: str
    error: Optional[str] = None


class ModelInfo(BaseModel):
    base_model: str
    model_path: str
    fine_tuned_available: bool
    model_loaded: bool
    model_parameters: Optional[int] = None
    trainable_parameters: Optional[int] = None


training_jobs: Dict[str, TrainingStatus] = {}


@router.post("/train")
async def start_training(
    request: TrainingRequest,
    background_tasks: BackgroundTasks
):
    try:
        import uuid
        job_id = str(uuid.uuid4())
        
        training_jobs[job_id] = TrainingStatus(
            job_id=job_id,
            status="pending",
            progress=0.0,
            message="Training job queued"
        )
        
        background_tasks.add_task(
            run_training_job,
            job_id,
            request
        )
        
        return {
            "job_id": job_id,
            "status": "pending",
            "message": "Model training started"
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/training/status/{job_id}")
async def get_training_status(job_id: str):
    if job_id not in training_jobs:
        raise HTTPException(status_code=404, detail="Training job not found")
    
    return training_jobs[job_id]


@router.get("/training/jobs")
async def list_training_jobs():
    return {
        "jobs": list(training_jobs.values()),
        "total": len(training_jobs)
    }


@router.get("/model/info", response_model=ModelInfo)
async def get_model_info():
    try:
        info = await local_llm_service.get_model_info()
        return ModelInfo(**info)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/model/load")
async def load_model(use_fine_tuned: bool = True):
    try:
        await local_llm_service.load_model(use_fine_tuned=use_fine_tuned)
        return {"message": "Model loaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/model/mock")
async def toggle_mock_mode(enabled: bool = True):
    local_llm_service.mock_mode = enabled
    return {
        "message": f"Mock mode {'enabled' if enabled else 'disabled'}",
        "mock_mode": local_llm_service.mock_mode
    }


@router.post("/model/generate")
async def generate_text(
    prompt: str,
    max_length: int = 512,
    temperature: float = 0.7
):
    try:
        response = await local_llm_service.generate_response(
            prompt=prompt,
            max_length=max_length,
            temperature=temperature
        )
        return {
            "prompt": prompt,
            "response": response,
            "parameters": {
                "max_length": max_length,
                "temperature": temperature
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def run_training_job(job_id: str, request: TrainingRequest):
    try:
        training_jobs[job_id].status = "training"
        training_jobs[job_id].message = "Loading training data..."
        training_jobs[job_id].progress = 0.1
        
        if request.documents:
            documents = []
            for doc_id in request.documents:
                doc = await local_storage_service.load_document(doc_id)
                if doc:
                    documents.append(doc)
        else:
            documents = await local_storage_service.list_documents()
        
        if not documents:
            raise ValueError("No documents available for training")
        
        training_jobs[job_id].progress = 0.3
        training_jobs[job_id].message = "Preparing training dataset..."
        
        training_dataset = await local_llm_service.prepare_training_data(documents)
        
        training_jobs[job_id].progress = 0.5
        training_jobs[job_id].message = "Starting model training..."
        
        await local_llm_service.fine_tune_model(
            training_dataset=training_dataset,
            learning_rate=request.learning_rate,
            num_epochs=request.num_epochs,
            batch_size=request.batch_size
        )
        
        training_jobs[job_id].status = "completed"
        training_jobs[job_id].progress = 1.0
        training_jobs[job_id].message = "Model training completed successfully"
        
    except Exception as e:
        training_jobs[job_id].status = "failed"
        training_jobs[job_id].error = str(e)
        training_jobs[job_id].message = f"Training failed: {str(e)}"