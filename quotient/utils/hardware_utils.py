"""Hardware detection and optimization utilities."""

import logging
import os
from typing import Dict, Any, Optional
import torch

logger = logging.getLogger(__name__)


class HardwareDetector:
    """Detect and configure hardware for optimal performance."""
    
    def __init__(self):
        """Initialize hardware detector."""
        self.device = self._detect_device()
        self.config = self._get_optimization_config()
    
    def _detect_device(self) -> torch.device:
        """Detect the best available device."""
        if torch.backends.mps.is_available():
            device = torch.device("mps")
            logger.info("Apple Silicon MPS detected")
        else:
            device = torch.device("cpu")
            logger.info("Using CPU for inference")
        
        return device
    
    def _get_optimization_config(self) -> Dict[str, Any]:
        """Get hardware-specific optimization configuration."""
        if self.device.type == "mps":
            config = {
                "torch_dtype": torch.float32,  # MPS doesn't support float16 well
                "device_map": None,
                "load_in_8bit": True,
                "load_in_4bit": False,
                "max_memory": None
            }
            logger.info("MPS optimization config applied")
            
        else:  # CPU
            config = {
                "torch_dtype": torch.float32,
                "device_map": None,
                "load_in_8bit": True,
                "load_in_4bit": True,
                "max_memory": None
            }
            logger.info("CPU optimization config applied")
        
        return config
    
    def get_device(self) -> torch.device:
        """Get the detected device."""
        return self.device
    
    def get_config(self) -> Dict[str, Any]:
        """Get the optimization configuration."""
        return self.config.copy()
    
    def get_model_config(self, model_size_gb: float = 1.0) -> Dict[str, Any]:
        """Get model-specific configuration based on model size.
        
        Args:
            model_size_gb: Size of the model in GB
            
        Returns:
            Model configuration dictionary
        """
        config = self.config.copy()
        
        # For slim branch, always use conservative settings
        if model_size_gb > 2.0:
            # Large model, use aggressive quantization
            config["load_in_4bit"] = True
            config["load_in_8bit"] = False
            logger.info(f"Large model detected ({model_size_gb}GB), using 4-bit quantization")
        elif model_size_gb > 1.0:
            # Medium model, use 8-bit quantization
            config["load_in_8bit"] = True
            config["load_in_4bit"] = False
            logger.info(f"Medium model detected ({model_size_gb}GB), using 8-bit quantization")
        else:
            # Small model, no quantization needed
            config["load_in_8bit"] = False
            config["load_in_4bit"] = False
            logger.info(f"Small model detected ({model_size_gb}GB), no quantization needed")
        
        return config
    
    def get_available_memory(self) -> float:
        """Get available memory in GB."""
        # For slim branch, assume conservative memory
        return 8.0  # Assume 8GB system memory
    
    def is_cuda_available(self) -> bool:
        """Check if CUDA is available."""
        return False  # Disabled for slim branch
    
    def is_mps_available(self) -> bool:
        """Check if MPS is available."""
        return self.device.type == "mps"
    
    def get_device_info(self) -> Dict[str, Any]:
        """Get detailed device information."""
        info = {
            "device_type": self.device.type,
            "device_index": self.device.index if self.device.index is not None else 0,
            "available_memory_gb": self.get_available_memory(),
            "optimization_config": self.config
        }
        
        return info


def get_optimal_device() -> torch.device:
    """Get the optimal device for inference."""
    detector = HardwareDetector()
    return detector.get_device()


def get_model_config(model_size_gb: float = 1.0) -> Dict[str, Any]:
    """Get optimal model configuration for the current hardware.
    
    Args:
        model_size_gb: Size of the model in GB
        
    Returns:
        Model configuration dictionary
    """
    detector = HardwareDetector()
    return detector.get_model_config(model_size_gb)


def print_hardware_info():
    """Print detailed hardware information."""
    detector = HardwareDetector()
    info = detector.get_device_info()
    
    print("\n=== Hardware Information (Slim Branch) ===")
    print(f"Device Type: {info['device_type']}")
    print(f"Available Memory: {info['available_memory_gb']:.1f}GB")
    print(f"CUDA Available: {detector.is_cuda_available()}")
    print(f"MPS Available: {detector.is_mps_available()}")
    print(f"Optimization Config: {info['optimization_config']}")
    print("=" * 50) 