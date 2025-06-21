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
        if torch.cuda.is_available():
            device = torch.device("cuda")
            gpu_name = torch.cuda.get_device_name()
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1e9
            logger.info(f"CUDA GPU detected: {gpu_name} ({gpu_memory:.1f}GB)")
        elif torch.backends.mps.is_available():
            device = torch.device("mps")
            logger.info("Apple Silicon MPS detected")
        else:
            device = torch.device("cpu")
            logger.info("Using CPU for inference")
        
        return device
    
    def _get_optimization_config(self) -> Dict[str, Any]:
        """Get hardware-specific optimization configuration."""
        if self.device.type == "cuda":
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1e9
            
            # Determine optimal settings based on GPU memory
            if gpu_memory >= 24:  # High-end GPU (RTX 4090, A100, etc.)
                config = {
                    "torch_dtype": torch.float16,
                    "device_map": "auto",
                    "load_in_8bit": False,
                    "load_in_4bit": False,
                    "max_memory": None,
                    "attn_implementation": "flash_attention_2"
                }
            elif gpu_memory >= 16:  # Mid-range GPU (RTX 4080, etc.)
                config = {
                    "torch_dtype": torch.float16,
                    "device_map": "auto",
                    "load_in_8bit": False,
                    "load_in_4bit": False,
                    "max_memory": {0: f"{int(gpu_memory * 0.8)}GB"}
                }
            elif gpu_memory >= 8:  # Entry-level GPU (RTX 3070, etc.)
                config = {
                    "torch_dtype": torch.float16,
                    "device_map": "auto",
                    "load_in_8bit": True,
                    "load_in_4bit": False,
                    "max_memory": {0: f"{int(gpu_memory * 0.7)}GB"}
                }
            else:  # Low-end GPU
                config = {
                    "torch_dtype": torch.float16,
                    "device_map": "auto",
                    "load_in_8bit": True,
                    "load_in_4bit": True,
                    "max_memory": {0: f"{int(gpu_memory * 0.6)}GB"}
                }
            
            logger.info(f"CUDA optimization config: {config}")
            
        elif self.device.type == "mps":
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
    
    def get_model_config(self, model_size_gb: float = 8.0) -> Dict[str, Any]:
        """Get model-specific configuration based on model size.
        
        Args:
            model_size_gb: Size of the model in GB
            
        Returns:
            Model configuration dictionary
        """
        config = self.config.copy()
        
        if self.device.type == "cuda":
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1e9
            
            # Adjust configuration based on model size vs available memory
            if model_size_gb > gpu_memory * 0.8:
                # Model is too large, need aggressive quantization
                config["load_in_4bit"] = True
                config["load_in_8bit"] = False
                config["torch_dtype"] = torch.float16
                logger.warning(f"Model size ({model_size_gb}GB) exceeds 80% of GPU memory ({gpu_memory}GB), using 4-bit quantization")
            
            elif model_size_gb > gpu_memory * 0.5:
                # Model is large, use 8-bit quantization
                config["load_in_8bit"] = True
                config["load_in_4bit"] = False
                logger.info(f"Model size ({model_size_gb}GB) is large relative to GPU memory ({gpu_memory}GB), using 8-bit quantization")
        
        return config
    
    def get_available_memory(self) -> float:
        """Get available memory in GB."""
        if self.device.type == "cuda":
            return torch.cuda.get_device_properties(0).total_memory / 1e9
        else:
            # For CPU/MPS, return a reasonable default
            return 16.0  # Assume 16GB system memory
    
    def is_cuda_available(self) -> bool:
        """Check if CUDA is available."""
        return self.device.type == "cuda"
    
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
        
        if self.device.type == "cuda":
            info.update({
                "gpu_name": torch.cuda.get_device_name(),
                "cuda_version": torch.version.cuda,
                "gpu_memory_gb": torch.cuda.get_device_properties(0).total_memory / 1e9,
                "gpu_compute_capability": torch.cuda.get_device_capability()
            })
        
        return info


def get_optimal_device() -> torch.device:
    """Get the optimal device for inference."""
    detector = HardwareDetector()
    return detector.get_device()


def get_model_config(model_size_gb: float = 8.0) -> Dict[str, Any]:
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
    
    print("\n=== Hardware Information ===")
    print(f"Device Type: {info['device_type']}")
    print(f"Available Memory: {info['available_memory_gb']:.1f}GB")
    
    if info['device_type'] == 'cuda':
        print(f"GPU: {info['gpu_name']}")
        print(f"CUDA Version: {info['cuda_version']}")
        print(f"Compute Capability: {info['gpu_compute_capability']}")
    
    print(f"Optimization Config: {info['optimization_config']}")
    print("============================\n") 