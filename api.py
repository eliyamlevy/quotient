#!/usr/bin/env python3
"""FastAPI web service for Quotient inventory management system."""

import os
import logging
from pathlib import Path
from typing import List, Optional
import tempfile
import shutil

# Add the project root to the path
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
    from fastapi.responses import JSONResponse
    from fastapi.middleware.cors import CORSMiddleware
    import uvicorn
except ImportError:
    print("FastAPI not installed. Please install with: pip install fastapi uvicorn[standard]")
    sys.exit(1)

from quotient.core.config import QuotientConfig
from quotient.core.pipeline import QuotientPipeline
from quotient.utils.data_models import InventoryItem

# Configure logging
logging.basicConfig(level=logging.INFO)
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

@app.on_event("startup")
async def startup_event():
    """Initialize the Quotient pipeline on startup."""
    global pipeline
    try:
        logger.info("Initializing Quotient pipeline...")
        config = QuotientConfig()
        pipeline = QuotientPipeline(config)
        logger.info("✅ Quotient pipeline initialized successfully")
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
        "endpoints": {
            "health": "/health",
            "process_file": "/process-file",
            "process_text": "/process-text",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "pipeline_ready": pipeline is not None,
        "timestamp": "2025-06-20T23:30:00Z"
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
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            shutil.copyfileobj(file.file, temp_file)
            temp_path = Path(temp_file.name)
        
        # Process the file
        logger.info(f"Processing file: {file.filename}")
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
        
        return {
            "success": True,
            "filename": file.filename,
            "items_extracted": len(serialized_items),
            "processing_time": "0.5s",  # TODO: Add actual timing
            "items": serialized_items
        }
        
    except Exception as e:
        logger.error(f"Error processing file {file.filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@app.post("/process-text")
async def process_text(text: str, max_items: Optional[int] = 50):
    """
    Process text content and extract inventory items.
    
    Args:
        text: Text content to process
        max_items: Maximum number of items to return (default: 50)
    
    Returns:
        JSON response with extracted inventory items
    """
    if not pipeline:
        raise HTTPException(status_code=503, detail="Pipeline not initialized")
    
    try:
        # Create temporary text file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
            temp_file.write(text)
            temp_path = Path(temp_file.name)
        
        # Process the text file
        result = pipeline.process_documents([temp_path])
        
        # Clean up
        os.unlink(temp_path)
        
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
        
        return {
            "success": True,
            "text_length": len(text),
            "items_extracted": len(serialized_items),
            "processing_time": "0.2s",  # TODO: Add actual timing
            "items": serialized_items
        }
        
    except Exception as e:
        logger.error(f"Error processing text: {str(e)}")
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