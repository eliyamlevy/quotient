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
    
    # OpenAI Configuration
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-3.5-turbo"
    
    # Local LLM Configuration
    llm_backend: str = "openai"  # "openai" or "llama"
    llama_model: str = "meta-llama/Meta-Llama-3-8B-Instruct"
    
    # Hardware Optimization
    use_cuda: bool = True
    use_mps: bool = True  # Apple Silicon
    max_memory_gb: int = 8
    
    # Processing Configuration
    max_file_size_mb: int = 100
    supported_formats: tuple = ("pdf", "docx", "xlsx", "csv", "txt", "jpg", "png", "eml")
    
    # Output Configuration
    output_format: str = "json"
    output_dir: str = "output"
    
    def __post_init__(self):
        """Initialize configuration from environment variables."""
        # OpenAI
        if not self.openai_api_key:
            self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        # LLM Backend
        llm_backend = os.getenv("LLM_BACKEND")
        if llm_backend:
            self.llm_backend = llm_backend
        
        # Llama Model
        llama_model = os.getenv("LLAMA_MODEL")
        if llama_model:
            self.llama_model = llama_model
        
        # Hardware settings
        cuda_available = os.getenv("USE_CUDA", "true").lower() == "true"
        self.use_cuda = cuda_available
        
        mps_available = os.getenv("USE_MPS", "true").lower() == "true"
        self.use_mps = mps_available
        
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
        if self.llm_backend == "openai" and not self.openai_api_key:
            print("Warning: OpenAI backend selected but no API key provided")
            return False
        
        if self.llm_backend not in ["openai", "llama"]:
            print(f"Error: Unsupported LLM backend: {self.llm_backend}")
            return False
        
        return True
    
    def get_openai_config(self) -> dict:
        """Get OpenAI configuration dictionary."""
        return {
            "api_key": self.openai_api_key,
            "model": self.openai_model
        }
    
    def is_ai_enabled(self) -> bool:
        """Check if AI features are enabled."""
        return bool(self.openai_api_key)
    
    def get_supported_formats(self) -> list:
        """Get list of supported file formats."""
        return list(self.supported_formats)
    
    def to_dict(self) -> dict:
        """Convert configuration to dictionary."""
        return {
            "openai_api_key": "***" if self.openai_api_key else "",
            "openai_model": self.openai_model,
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
            "output_dir": self.output_dir
        } 