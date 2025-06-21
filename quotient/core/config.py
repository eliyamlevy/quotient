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
    llama_model: str = "microsoft/DialoGPT-medium"  # Lightweight, no token required
    
    # Hardware Optimization (MPS/CPU focused)
    use_cuda: bool = False  # Disabled for slim branch
    use_mps: bool = True  # Enable for Apple Silicon
    max_memory_gb: int = 8  # Conservative for laptops
    
    # Processing Configuration
    max_file_size_mb: int = 50  # Smaller for laptops
    supported_formats: tuple = ("pdf", "xlsx", "csv", "jpg", "png")  # Essential formats only
    
    # Output Configuration
    output_format: str = "json"
    output_dir: str = "output"
    
    def __post_init__(self):
        """Initialize configuration from environment variables."""
        # Hugging Face Token (optional for lightweight models)
        if not self.huggingface_token:
            self.huggingface_token = os.getenv("HUGGINGFACE_TOKEN")
        
        # LLM Backend - force llama
        self.llm_backend = "llama"
        
        # Llama Model - prefer lightweight models
        llama_model = os.getenv("LLAMA_MODEL")
        if llama_model:
            self.llama_model = llama_model
        else:
            # Default to lightweight model
            self.llama_model = "microsoft/DialoGPT-medium"
        
        # Hardware settings - optimize for laptops
        self.use_cuda = False  # Disable CUDA for slim branch
        
        # Enable MPS for Apple Silicon
        mps_available = os.getenv("USE_MPS", "true").lower() == "true"
        self.use_mps = mps_available
        
        # Conservative memory settings for laptops
        max_memory = os.getenv("MAX_MEMORY_GB")
        if max_memory:
            self.max_memory_gb = int(max_memory)
        else:
            self.max_memory_gb = 8  # Default to 8GB for laptops
    
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
            print("Consider using a lightweight model like microsoft/DialoGPT-medium")
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
            "batch_size": 5,  # Smaller batch size for laptops
            "max_retries": 3,
            "log_level": "INFO",
            "enable_web_search": False,  # Disable for slim
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