#!/usr/bin/env python3
"""FastAPI web service for Quotient inventory management system."""

import os
import logging
import time
import psutil
import platform
from pathlib import Path
from typing import List, Optional, Dict, Any
import tempfile
import shutil
from datetime import datetime, timedelta
from collections import defaultdict

# Add the project root to the path
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
    from fastapi.responses import JSONResponse
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    import uvicorn
except ImportError:
    print("FastAPI not installed. Please install with: pip install fastapi uvicorn[standard]")
    sys.exit(1)

from quotient.core.config import QuotientConfig
from quotient.core.pipeline import QuotientPipeline
from quotient.utils.data_models import InventoryItem
from quotient.utils.hardware_utils import HardwareDetector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Quotient API",
    description="AI-powered inventory management system API",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global pipeline instance
pipeline = None

# Statistics tracking
class APIMetrics:
    def __init__(self):
        self.start_time = datetime.now()
        self.request_count = 0
        self.file_processing_count = 0
        self.text_processing_count = 0
        self.total_processing_time = 0.0
        self.error_count = 0
        self.file_type_counts = defaultdict(int)
        self.processing_times = []
        self.model_info = {}
        
    def record_request(self, endpoint: str, processing_time: float, success: bool = True):
        """Record a request and its metrics."""
        self.request_count += 1
        self.total_processing_time += processing_time
        self.processing_times.append(processing_time)
        
        if not success:
            self.error_count += 1
            
        if endpoint == "file":
            self.file_processing_count += 1
        elif endpoint == "text":
            self.text_processing_count += 1
    
    def record_file_type(self, file_type: str):
        """Record file type usage."""
        self.file_type_counts[file_type] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics."""
        uptime = datetime.now() - self.start_time
        avg_processing_time = self.total_processing_time / max(self.request_count, 1)
        
        return {
            "uptime_seconds": uptime.total_seconds(),
            "uptime_formatted": str(uptime).split('.')[0],
            "total_requests": self.request_count,
            "file_processing_requests": self.file_processing_count,
            "text_processing_requests": self.text_processing_count,
            "error_count": self.error_count,
            "success_rate": ((self.request_count - self.error_count) / max(self.request_count, 1)) * 100,
            "average_processing_time": round(avg_processing_time, 3),
            "total_processing_time": round(self.total_processing_time, 3),
            "file_type_distribution": dict(self.file_type_counts),
            "recent_processing_times": self.processing_times[-10:] if self.processing_times else []
        }

# Global metrics instance
metrics = APIMetrics()

# Pydantic model for text processing request
class TextProcessingRequest(BaseModel):
    text: str
    max_items: Optional[int] = 50

@app.on_event("startup")
async def startup_event():
    """Initialize the Quotient pipeline on startup."""
    global pipeline, metrics
    
    try:
        logger.info("🚀 Initializing Quotient API Server...")
        logger.info("=" * 60)
        
        # System information
        logger.info("📊 System Information:")
        logger.info(f"  Platform: {platform.system()} {platform.release()}")
        logger.info(f"  Python: {platform.python_version()}")
        logger.info(f"  CPU Cores: {psutil.cpu_count()}")
        logger.info(f"  Memory: {psutil.virtual_memory().total / (1024**3):.1f} GB")
        
        # Hardware detection
        logger.info("🔧 Hardware Detection:")
        hardware_detector = HardwareDetector()
        hardware_info = hardware_detector.get_device_info()
        for key, value in hardware_info.items():
            logger.info(f"  {key}: {value}")
        
        # Configuration
        logger.info("⚙️  Configuration:")
        config = QuotientConfig()
        logger.info(f"  LLM Backend: {config.llm_backend}")
        logger.info(f"  Model: {config.llama_model}")
        logger.info(f"  Use CUDA: {config.use_cuda}")
        logger.info(f"  Use MPS: {config.use_mps}")
        logger.info(f"  Max Memory: {config.max_memory_gb} GB")
        
        # Initialize pipeline
        logger.info("🤖 Initializing AI Pipeline...")
        pipeline = QuotientPipeline(config)
        
        # Model information
        if hasattr(pipeline, 'entity_extractor') and hasattr(pipeline.entity_extractor, 'model'):
            model = pipeline.entity_extractor.model
            metrics.model_info = {
                "model_name": getattr(model, 'name_or_path', 'Unknown'),
                "model_type": type(model).__name__,
                "device": str(getattr(model, 'device', 'Unknown')),
                "dtype": str(getattr(model, 'dtype', 'Unknown')),
                "parameters": getattr(model, 'num_parameters', lambda: 'Unknown')(),
            }
            logger.info("📋 Model Information:")
            for key, value in metrics.model_info.items():
                logger.info(f"  {key}: {value}")
        
        logger.info("✅ Quotient pipeline initialized successfully!")
        logger.info("🌐 API Server ready on http://0.0.0.0:8000")
        logger.info("📚 Interactive docs available at http://0.0.0.0:8000/docs")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize pipeline: {str(e)}")
        raise

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Quotient API - AI-powered inventory management system",
        "version": "1.0.0",
        "status": "running",
        "server_start_time": metrics.start_time.isoformat(),
        "endpoints": {
            "health": "/health",
            "process_file": "/process-file",
            "process_text": "/process-text",
            "docs": "/docs",
            "stats": "/stats",
            "system_info": "/system-info"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint with detailed status."""
    memory = psutil.virtual_memory()
    cpu_percent = psutil.cpu_percent(interval=1)
    
    return {
        "status": "healthy",
        "pipeline_ready": pipeline is not None,
        "timestamp": datetime.now().isoformat(),
        "system_health": {
            "cpu_usage_percent": cpu_percent,
            "memory_usage_percent": memory.percent,
            "memory_available_gb": round(memory.available / (1024**3), 2),
            "disk_usage_percent": psutil.disk_usage('/').percent
        },
        "uptime_seconds": (datetime.now() - metrics.start_time).total_seconds()
    }

@app.get("/stats")
async def get_statistics():
    """Get detailed API usage statistics."""
    return {
        "api_metrics": metrics.get_stats(),
        "model_info": metrics.model_info,
        "current_time": datetime.now().isoformat()
    }

@app.get("/system-info")
async def get_system_info():
    """Get detailed system information."""
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Get hardware info
    hardware_detector = HardwareDetector()
    hardware_info = hardware_detector.get_device_info()
    
    return {
        "system": {
            "platform": platform.system(),
            "platform_version": platform.release(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(),
            "cpu_count_logical": psutil.cpu_count(logical=True)
        },
        "hardware": hardware_info,
        "resources": {
            "memory_total_gb": round(memory.total / (1024**3), 2),
            "memory_available_gb": round(memory.available / (1024**3), 2),
            "memory_used_percent": memory.percent,
            "disk_total_gb": round(disk.total / (1024**3), 2),
            "disk_free_gb": round(disk.free / (1024**3), 2),
            "disk_used_percent": disk.percent
        },
        "process": {
            "pid": os.getpid(),
            "memory_usage_mb": round(psutil.Process().memory_info().rss / (1024**2), 2),
            "cpu_percent": psutil.Process().cpu_percent()
        }
    }

@app.post("/process-file")
async def process_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    max_items: Optional[int] = 50
):
    """
    Process an uploaded file and extract inventory items.
    
    Args:
        file: Uploaded file (PDF, Excel, CSV, image)
        max_items: Maximum number of items to return (default: 50)
    
    Returns:
        JSON response with extracted inventory items
    """
    start_time = time.time()
    
    if not pipeline:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")
    
    # Validate file type
    allowed_extensions = {'.pdf', '.xlsx', '.csv', '.jpg', '.jpeg', '.png'}
    file_extension = Path(file.filename).suffix.lower()
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    try:
        logger.info(f"📁 Processing file: {file.filename} ({file.size} bytes)")
        
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            shutil.copyfileobj(file.file, temp_file)
            temp_path = Path(temp_file.name)
        
        # Process the file
        logger.info(f"🤖 Running AI extraction on {file.filename}...")
        result = pipeline.process_documents([temp_path])
        
        # Clean up temporary file
        background_tasks.add_task(os.unlink, temp_path)
        
        # Extract inventory items
        items = []
        if hasattr(result, 'items') and result.items:
            items = result.items[:max_items]
        
        # Convert to JSON-serializable format
        serialized_items = []
        for item in items:
            serialized_items.append({
                "item_name": item.item_name,
                "quantity": item.quantity,
                "unit_price": float(item.unit_price) if item.unit_price else 0.0,
                "category": item.category,
                "vendor_name": item.vendor_name,
                "part_number": item.part_number,
                "status": item.status.value if item.status else "unknown",
                "description": item.description
            })
        
        processing_time = time.time() - start_time
        
        # Record metrics
        metrics.record_request("file", processing_time, success=True)
        metrics.record_file_type(file_extension)
        
        logger.info(f"✅ Successfully processed {file.filename}")
        logger.info(f"   📊 Extracted {len(serialized_items)} items")
        logger.info(f"   ⏱️  Processing time: {processing_time:.3f}s")
        
        return {
            "success": True,
            "filename": file.filename,
            "file_size_bytes": file.size,
            "file_type": file_extension,
            "items_extracted": len(serialized_items),
            "processing_time_seconds": round(processing_time, 3),
            "max_items_requested": max_items,
            "items": serialized_items
        }
        
    except Exception as e:
        processing_time = time.time() - start_time
        metrics.record_request("file", processing_time, success=False)
        
        logger.error(f"❌ Error processing file {file.filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@app.post("/process-text")
async def process_text(request: TextProcessingRequest):
    """
    Process text content and extract inventory items.
    
    Args:
        request: TextProcessingRequest containing text and max_items
    
    Returns:
        JSON response with extracted inventory items
    """
    start_time = time.time()
    
    if not pipeline:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")
    
    try:
        logger.info(f"📝 Processing text input ({len(request.text)} characters)")
        
        # Create temporary text file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
            temp_file.write(request.text)
            temp_path = Path(temp_file.name)
        
        # Process the text file
        logger.info("🤖 Running AI extraction on text...")
        result = pipeline.process_documents([temp_path])
        
        # Clean up
        os.unlink(temp_path)
        
        # Extract inventory items
        items = []
        if hasattr(result, 'items') and result.items:
            items = result.items[:request.max_items]
        
        # Convert to JSON-serializable format
        serialized_items = []
        for item in items:
            serialized_items.append({
                "item_name": item.item_name,
                "quantity": item.quantity,
                "unit_price": float(item.unit_price) if item.unit_price else 0.0,
                "category": item.category,
                "vendor_name": item.vendor_name,
                "part_number": item.part_number,
                "status": item.status.value if item.status else "unknown",
                "description": item.description
            })
        
        processing_time = time.time() - start_time
        
        # Record metrics
        metrics.record_request("text", processing_time, success=True)
        
        logger.info(f"✅ Successfully processed text input")
        logger.info(f"   📊 Extracted {len(serialized_items)} items")
        logger.info(f"   ⏱️  Processing time: {processing_time:.3f}s")
        
        return {
            "success": True,
            "text_length": len(request.text),
            "items_extracted": len(serialized_items),
            "processing_time_seconds": round(processing_time, 3),
            "max_items_requested": request.max_items,
            "items": serialized_items
        }
        
    except Exception as e:
        processing_time = time.time() - start_time
        metrics.record_request("text", processing_time, success=False)
        
        logger.error(f"❌ Error processing text: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@app.get("/supported-formats")
async def get_supported_formats():
    """Get list of supported file formats."""
    return {
        "supported_formats": [
            {"extension": ".pdf", "type": "PDF Document"},
            {"extension": ".xlsx", "type": "Excel Spreadsheet"},
            {"extension": ".csv", "type": "CSV File"},
            {"extension": ".jpg", "type": "JPEG Image"},
            {"extension": ".jpeg", "type": "JPEG Image"},
            {"extension": ".png", "type": "PNG Image"}
        ]
    }

if __name__ == "__main__":
    # Run the API server
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 