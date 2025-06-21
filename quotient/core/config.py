"""Configuration management for Quotient (YAML-based)."""

import os
import logging
from typing import Optional, Any, Dict
from dataclasses import dataclass, field
import yaml


def _load_yaml_config(path: str) -> Dict[str, Any]:
    try:
        with open(path, 'r') as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        raise FileNotFoundError(f"Config file not found: {path}")
    except yaml.YAMLError as e:
        raise RuntimeError(f"Error parsing YAML config: {e}")


@dataclass
class QuotientConfig:
    """Configuration for Quotient system (YAML-based)."""
    # Hugging Face Configuration
    huggingface_token: Optional[str] = None
    # Local LLM Configuration
    llm_backend: str = "llama"  # "llama" only
    llama_model: str = "meta-llama/Llama-2-7b-chat-hf"
    # Hardware Optimization (CUDA focused)
    use_cuda: bool = True
    use_mps: bool = False
    max_memory_gb: int = 16
    # Processing Configuration
    max_file_size_mb: int = 100
    supported_formats: tuple = ("pdf", "xlsx", "csv", "jpg", "png")
    # Output Configuration
    output_format: str = "json"
    output_dir: str = "output"
    # Extra fields for extensibility
    extra: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_yaml(cls, path: str = "config.yaml") -> "QuotientConfig":
        data = _load_yaml_config(path)
        # Convert supported_formats to tuple if present
        if "supported_formats" in data and isinstance(data["supported_formats"], list):
            data["supported_formats"] = tuple(data["supported_formats"])
        # Separate extra fields
        known_fields = {f.name for f in cls.__dataclass_fields__.values()}
        extra = {k: v for k, v in data.items() if k not in known_fields}
        # Only pass known fields to the dataclass
        filtered = {k: v for k, v in data.items() if k in known_fields}
        return cls(**filtered, extra=extra)

    def get_hardware_config(self):
        return {
            "use_cuda": self.use_cuda,
            "use_mps": self.use_mps,
            "max_memory_gb": self.max_memory_gb,
        }

    def validate(self) -> bool:
        if self.llm_backend != "llama":
            print(f"Error: Only llama backend is supported: {self.llm_backend}")
            return False
        if self.llama_model.startswith("meta-llama/") and not self.huggingface_token:
            print("Warning: Hugging Face token may be required for Llama models")
            print("Get your token from: https://huggingface.co/settings/tokens")
        return True

    def is_ai_enabled(self) -> bool:
        return True

    def get_supported_formats(self) -> list:
        return list(self.supported_formats)

    def to_dict(self) -> dict:
        d = {
            "max_file_size_mb": self.max_file_size_mb,
            "supported_formats": self.supported_formats,
            "tesseract_path": self.extra.get("tesseract_path", ""),
            "batch_size": self.extra.get("batch_size", 10),
            "max_retries": self.extra.get("max_retries", 3),
            "log_level": self.extra.get("log_level", "INFO"),
            "enable_web_search": self.extra.get("enable_web_search", True),
            "database_url": self.extra.get("database_url", "sqlite:///quotient.db"),
            "vector_db_path": self.extra.get("vector_db_path", "./vector_db"),
            "llm_backend": self.llm_backend,
            "llama_model": self.llama_model,
            "use_cuda": self.use_cuda,
            "use_mps": self.use_mps,
            "max_memory_gb": self.max_memory_gb,
            "output_format": self.output_format,
            "output_dir": self.output_dir,
            "has_hf_token": bool(self.huggingface_token)
        }
        d.update(self.extra)
        return d 