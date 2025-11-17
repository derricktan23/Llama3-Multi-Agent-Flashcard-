from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Optional
import uuid
import logging
from datetime import datetime
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from multi_agent_system import generate_anki_cards

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Multi-Agent Flashcard API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

jobs: Dict[str, Dict] = {}

class FlashcardRequest(BaseModel):
    text: str
    user_id: Optional[str] = None

class FlashcardResponse(BaseModel):
    job_id: str
    status: str
    message: str

class JobStatus(BaseModel):
    job_id: str
    status: str
    progress: Optional[str] = None
    result: Optional[Dict] = None
    error_message: Optional[str] = None

class FlashcardResult(BaseModel):
    job_id: str
    flashcards: Dict
    processing_time: Optional[float] = None

@app.get("/")
async def root():
    return {"message": "Multi-Agent Flashcard API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/generate-flashcards", response_model=FlashcardResponse)
async def create_flashcard_job(request: FlashcardRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    
    jobs[job_id] = {
        "status": "pending",
        "progress": "Job created",
        "result": None,
        "error_message": None,
        "created_at": datetime.now().isoformat(),
        "completed_at": None,
    }
    
    background_tasks.add_task(process_flashcard_job, job_id, request.text)
    
    return FlashcardResponse(
        job_id=job_id,
        status="pending",
        message="Flashcard generation job created"
    )

@app.get("/job-status/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    return JobStatus(
        job_id=job_id,
        status=job["status"],
        progress=job.get("progress"),
        result=job.get("result"),
        error_message=job.get("error_message")
    )

@app.get("/job-result/{job_id}", response_model=FlashcardResult)
async def get_job_result(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job not completed yet")
    
    if not job["result"]:
        raise HTTPException(status_code=404, detail="No result found")
    
    return FlashcardResult(
        job_id=job_id,
        flashcards=job["result"],
        processing_time=job.get("processing_time")
    )

async def process_flashcard_job(job_id: str, text: str):
    try:
        jobs[job_id]["status"] = "processing"
        jobs[job_id]["progress"] = "Starting multi-agent processing..."
        
        start_time = datetime.now()
        result = await generate_anki_cards(text)
        
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["progress"] = "Processing completed"
        jobs[job_id]["result"] = result
        jobs[job_id]["completed_at"] = datetime.now().isoformat()
        jobs[job_id]["processing_time"] = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"✅ Completed job {job_id}")
        
    except Exception as e:
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error_message"] = str(e)
        jobs[job_id]["completed_at"] = datetime.now().isoformat()
        logger.error(f"❌ Job {job_id} failed: {e}")


@app.post("/generate-flashcards-sync")
async def generate_flashcards_sync(request: FlashcardRequest):
    """Synchronous endpoint that directly returns flashcards without job polling"""
    try:
        logger.info(f"🔄 Direct flashcard generation for text: {request.text[:100]}...")
        
        # Start processing
        start_time = datetime.now()
        
        # Call your multi-agent system directly
        result = await generate_anki_cards(request.text)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        logger.info(f"✅ Direct generation completed in {processing_time:.2f} seconds")
        
        # Return the result directly in the expected format
        return {
            "flashcards": result,
            "processing_time": processing_time,
            "success": True
        }
        
    except Exception as e:
        logger.error(f"❌ Direct generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Flashcard generation failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)