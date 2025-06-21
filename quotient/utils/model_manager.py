"""Model management utilities for local and remote model handling."""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import requests
from tqdm import tqdm

logger = logging.getLogger(__name__)


class ModelManager:
    """Manages model loading with local file priority and remote fallback."""
    
    def __init__(self, config):
        """Initialize the model manager.
        
        Args:
            config: QuotientConfig instance
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def ensure_model_available(self) -> bool:
        """Ensure a model is available, prioritizing local files.
        
        Returns:
            True if model is available, False otherwise
        """
        # Check for local GGUF model first
        if self.config.gguf_model_path:
            if self._check_local_model():
                self.logger.info(f"✅ Using local GGUF model: {self.config.gguf_model_path}")
                return True
            else:
                self.logger.warning(f"⚠️  Local GGUF model not found: {self.config.gguf_model_path}")
        
        # Check for HuggingFace model configuration
        if self.config.llm_id:
            self.logger.info(f"✅ Using HuggingFace model: {self.config.llm_id}")
            return True
        
        # No model configuration found
        self.logger.error("❌ No model configuration found")
        self.logger.error("Please configure either:")
        self.logger.error("  - gguf_model_path: path to local .gguf file")
        self.logger.error("  - llm_id: HuggingFace model ID")
        return False
    
    def _check_local_model(self) -> bool:
        """Check if local GGUF model file exists and is valid.
        
        Returns:
            True if model file exists and is valid
        """
        if not self.config.gguf_model_path:
            return False
        
        model_path = Path(self.config.gguf_model_path)
        
        # Check if file exists
        if not model_path.exists():
            self.logger.warning(f"Model file not found: {model_path}")
            return False
        
        # Check if it's a .gguf file
        if not model_path.suffix.lower() == '.gguf':
            self.logger.warning(f"File is not a .gguf file: {model_path}")
            return False
        
        # Check file size (basic validation)
        file_size = model_path.stat().st_size
        if file_size < 1024 * 1024:  # Less than 1MB
            self.logger.warning(f"Model file seems too small: {file_size} bytes")
            return False
        
        self.logger.info(f"Local model validated: {model_path} ({file_size / (1024**3):.2f} GB)")
        return True
    
    def download_model_if_needed(self, model_id: str, output_dir: str = "models") -> Optional[str]:
        """Download a model if it's not available locally.
        
        Args:
            model_id: HuggingFace model ID
            output_dir: Directory to save downloaded model
            
        Returns:
            Path to downloaded model file, or None if failed
        """
        # TODO: Implement remote model downloading
        # This is skeleton code for future implementation
        
        self.logger.info(f"🔄 Remote model downloading not yet implemented")
        self.logger.info(f"   Model ID: {model_id}")
        self.logger.info(f"   Output directory: {output_dir}")
        
        # Skeleton implementation - would include:
        # 1. Check if model already exists locally
        # 2. Query HuggingFace API for available GGUF files
        # 3. Download the model with progress bar
        # 4. Validate downloaded file
        # 5. Update config with local path
        
        return None
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model configuration.
        
        Returns:
            Dictionary with model information
        """
        info = {
            "backend": self.config.llm_backend,
            "local_model": None,
            "remote_model": None,
            "status": "unknown"
        }
        
        if self.config.gguf_model_path:
            info["local_model"] = {
                "path": self.config.gguf_model_path,
                "exists": self._check_local_model()
            }
            info["status"] = "local" if info["local_model"]["exists"] else "local_missing"
        
        if self.config.llm_id:
            info["remote_model"] = {
                "id": self.config.llm_id,
                "token_configured": bool(self.config.huggingface_token)
            }
            if not info["local_model"]:
                info["status"] = "remote"
        
        return info


def validate_model_config(config) -> bool:
    """Validate model configuration and provide helpful feedback.
    
    Args:
        config: QuotientConfig instance
        
    Returns:
        True if configuration is valid
    """
    manager = ModelManager(config)
    model_info = manager.get_model_info()
    
    logger.info("🔍 Model Configuration Validation:")
    logger.info(f"  Backend: {model_info['backend']}")
    logger.info(f"  Status: {model_info['status']}")
    
    if model_info['local_model']:
        logger.info(f"  Local Model: {model_info['local_model']['path']}")
        logger.info(f"  Local Model Exists: {model_info['local_model']['exists']}")
    
    if model_info['remote_model']:
        logger.info(f"  Remote Model: {model_info['remote_model']['id']}")
        logger.info(f"  Token Configured: {model_info['remote_model']['token_configured']}")
    
    # Provide specific guidance based on status
    if model_info['status'] == 'local_missing':
        logger.error("❌ Local model file not found!")
        logger.error("Please ensure the GGUF file exists at the configured path.")
        return False
    
    elif model_info['status'] == 'unknown':
        logger.error("❌ No model configuration found!")
        logger.error("Please configure either:")
        logger.error("  - gguf_model_path: path to local .gguf file")
        logger.error("  - llm_id: HuggingFace model ID")
        return False
    
    elif model_info['status'] == 'remote' and not model_info['remote_model']['token_configured']:
        logger.warning("⚠️  Remote model configured but no HuggingFace token provided")
        logger.warning("Some models may require authentication")
    
    logger.info("✅ Model configuration validation complete")
    return True 