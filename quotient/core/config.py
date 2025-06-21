"""Configuration management for Quotient."""

import os
import logging
from typing import Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class QuotientConfig:
    """Configuration for Quotient system."""
    
    # Hugging Face Configuration
    huggingface_token: Optional[str] = None
    
    # Local LLM Configuration
    llm_backend: str = "llama"  # "llama" only
    llama_model: str = "meta-llama/Llama-2-7b-chat-hf"  # Good balance for CUDA
    
    # Hardware Optimization (CUDA focused)
    use_cuda: bool = True
    use_mps: bool = False  # Not needed on Linux server
    max_memory_gb: int = 16  # Adjust based on your GPU
    
    # Processing Configuration
    max_file_size_mb: int = 100
    supported_formats: tuple = ("pdf", "xlsx", "csv", "jpg", "png")  # Removed docx, eml
    
    # Output Configuration
    output_format: str = "json"
    output_dir: str = "output"
    
    def __post_init__(self):
        """Initialize configuration from environment variables."""
        # Hugging Face Token
        if not self.huggingface_token:
            self.huggingface_token = os.getenv("HUGGINGFACE_TOKEN")
        
        # LLM Backend - force llama
        self.llm_backend = "llama"
        
        # Llama Model
        llama_model = os.getenv("LLAMA_MODEL")
        if llama_model:
            self.llama_model = llama_model
        
        # Hardware settings
        cuda_available = os.getenv("USE_CUDA", "true").lower() == "true"
        self.use_cuda = cuda_available
        
        # MPS not needed on Linux server
        self.use_mps = False
        
        max_memory = os.getenv("MAX_MEMORY_GB")
        if max_memory:
            self.max_memory_gb = int(max_memory)
    
    def get_hardware_config(self):
        """Get hardware-specific configuration."""
        return {
            "use_cuda": self.use_cuda,
            "use_mps": self.use_mps,
            "max_memory_gb": self.max_memory_gb,
        }
    
    def validate(self) -> bool:
        """Validate configuration."""
        if self.llm_backend != "llama":
            print(f"Error: Only llama backend is supported: {self.llm_backend}")
            return False
        
        # Check if we need Hugging Face token for gated models
        if self.llama_model.startswith("meta-llama/") and not self.huggingface_token:
            print("Warning: Hugging Face token may be required for Llama models")
            print("Get your token from: https://huggingface.co/settings/tokens")
        
        return True
    
    def is_ai_enabled(self) -> bool:
        """Check if AI features are enabled."""
        return True  # Always enabled with local LLM
    
    def get_supported_formats(self) -> list:
        """Get list of supported file formats."""
        return list(self.supported_formats)
    
    def to_dict(self) -> dict:
        """Convert configuration to dictionary."""
        return {
            "max_file_size_mb": self.max_file_size_mb,
            "supported_formats": self.supported_formats,
            "tesseract_path": "",
            "batch_size": 10,
            "max_retries": 3,
            "log_level": "INFO",
            "enable_web_search": True,
            "database_url": "sqlite:///quotient.db",
            "vector_db_path": "./vector_db",
            "llm_backend": self.llm_backend,
            "llama_model": self.llama_model,
            "use_cuda": self.use_cuda,
            "use_mps": self.use_mps,
            "max_memory_gb": self.max_memory_gb,
            "output_format": self.output_format,
            "output_dir": self.output_dir,
            "has_hf_token": bool(self.huggingface_token)
        } 