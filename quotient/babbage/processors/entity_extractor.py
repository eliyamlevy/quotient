"""AI-powered entity extraction from text content."""

import logging
from typing import List, Dict, Any, Optional
import json
import re

# Optional imports for AI/ML functionality
try:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
    TORCH_AVAILABLE = True
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    TRANSFORMERS_AVAILABLE = False

# Optional imports for GGUF models
try:
    from llama_cpp import Llama
    LLAMA_CPP_AVAILABLE = True
except ImportError:
    LLAMA_CPP_AVAILABLE = False

from ...core.config import QuotientConfig
from ...utils.data_models import InventoryItem, ItemStatus
from ...utils.hardware_utils import HardwareDetector, get_optimal_device, get_model_config


class EntityExtractor:
    """Extract inventory-related entities from text using AI."""
    
    def __init__(self, config: QuotientConfig):
        """Initialize the entity extractor.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize LLM backend
        self.llm_backend = "llama"  # Only llama supported
        self.device = None
        self.llm_pipeline = None
        self.gguf_model = None
        
        # Check for GGUF model first
        if self.config.gguf_model_path:
            if LLAMA_CPP_AVAILABLE:
                self._initialize_gguf()
            else:
                self.logger.error("llama-cpp-python not available for GGUF models")
                raise RuntimeError("llama-cpp-python required for GGUF models")
        # Fall back to HuggingFace model
        elif TORCH_AVAILABLE and TRANSFORMERS_AVAILABLE:
            self.device = get_optimal_device()
            self._initialize_llama()
        else:
            self.logger.error("No AI backend available - PyTorch/Transformers or llama-cpp-python required")
            raise RuntimeError("No AI backend available")
    
    def _initialize_llama(self):
        """Initialize Llama model for local inference."""
        if not TORCH_AVAILABLE or not TRANSFORMERS_AVAILABLE:
            raise RuntimeError("PyTorch or Transformers not available for LLM model")
            
        try:
            # Get the configured model ID - fail if not configured
            if not hasattr(self.config, 'llm_id') or not self.config.llm_id:
                raise ValueError("llm_id not configured in config.yaml")
            
            model_id = self.config.llm_id
            self.logger.info(f"Loading local LLM model: {model_id}")
            
            # Get hardware-optimized config for CUDA
            config = get_model_config(model_size_gb=7.0)  # 7B model
            
            # Prepare token for gated models
            token = getattr(self.config, 'huggingface_token', None)
            if token:
                self.logger.info("Using Hugging Face token for model access")
            
            # Load tokenizer
            tokenizer = AutoTokenizer.from_pretrained(
                model_id,
                token=token,
                trust_remote_code=True
            )
            if tokenizer.pad_token is None:
                tokenizer.pad_token = tokenizer.eos_token
            
            # Load model with CUDA optimization
            model = AutoModelForCausalLM.from_pretrained(
                model_id,
                token=token,
                torch_dtype=config["torch_dtype"],
                device_map=config["device_map"],
                load_in_4bit=True,  # Use 4-bit quantization for memory efficiency
                trust_remote_code=True,
                use_safetensors=True
            )
            
            # Create pipeline
            self.llm_pipeline = pipeline(
                "text-generation",
                model=model,
                tokenizer=tokenizer,
                max_new_tokens=512,  # Increased for better responses
                do_sample=True,
                temperature=0.1,
                top_p=0.9,
                pad_token_id=tokenizer.eos_token_id
            )
            
            self.logger.info("Local LLM model loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to load local LLM model '{model_id}': {str(e)}")
            raise RuntimeError(f"Model initialization failed: {str(e)}")
    
    def _initialize_gguf(self):
        """Initialize GGUF model for local inference."""
        if not LLAMA_CPP_AVAILABLE:
            raise RuntimeError("llama-cpp-python not available for GGUF model")
            
        try:
            model_path = self.config.gguf_model_path
            self.logger.info(f"Loading GGUF model: {model_path}")
            
            # Initialize GGUF model with optimized settings
            self.gguf_model = Llama(
                model_path=model_path,
                n_ctx=2048,  # Context window
                n_threads=4,  # CPU threads
                n_gpu_layers=0,  # Set to >0 for GPU acceleration if available
                verbose=False
            )
            
            self.logger.info("GGUF model loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to load GGUF model '{model_path}': {str(e)}")
            raise RuntimeError(f"GGUF model initialization failed: {str(e)}")
    
    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract entities from text content.
        
        Args:
            text: Text content to extract entities from
            
        Returns:
            List of extracted entities
        """
        self.logger.info("Extracting entities from text")
        
        try:
            if self.gguf_model:
                return self._extract_with_gguf(text)
            elif self.llm_pipeline:
                return self._extract_with_llama(text)
            else:
                raise RuntimeError("No LLM backend available - model initialization failed during startup")
                
        except Exception as e:
            self.logger.error(f"Error extracting entities: {str(e)}")
            raise
    
    def _extract_with_gguf(self, text: str) -> List[Dict[str, Any]]:
        """Extract entities using local GGUF model.
        
        Args:
            text: Text content
            
        Returns:
            List of extracted entities
        """
        try:
            prompt = self._create_extraction_prompt(text)
            
            # Generate response using GGUF model
            result = self.gguf_model(
                prompt,
                max_tokens=512,
                temperature=0.1,
                top_p=0.9,
                stop=["\n\n", "```"]
            )
            
            generated_text = result['choices'][0]['text']
            
            # Extract JSON from response
            json_start = generated_text.find('[')
            json_end = generated_text.rfind(']') + 1
            
            if json_start != -1 and json_end != 0:
                json_str = generated_text[json_start:json_end]
                entities = json.loads(json_str)
                
                if isinstance(entities, list):
                    self.logger.info(f"GGUF model extracted {len(entities)} entities")
                    return entities
                else:
                    self.logger.warning("GGUF model response is not a list")
                    return []
            else:
                self.logger.warning("No JSON array found in GGUF model response")
                return []
                
        except Exception as e:
            self.logger.error(f"GGUF extraction failed: {str(e)}")
            return []
    
    def _extract_with_llama(self, text: str) -> List[Dict[str, Any]]:
        """Extract entities using local LLM model.
        
        Args:
            text: Text content
            
        Returns:
            List of extracted entities
        """
        try:
            prompt = self._create_extraction_prompt(text)
            
            # Generate response
            result = self.llm_pipeline(prompt)
            generated_text = result[0]['generated_text']
            
            # Extract JSON from response
            json_start = generated_text.find('[')
            json_end = generated_text.rfind(']') + 1
            
            if json_start != -1 and json_end != 0:
                json_str = generated_text[json_start:json_end]
                entities = json.loads(json_str)
                
                if isinstance(entities, list):
                    self.logger.info(f"LLM extracted {len(entities)} entities")
                    return entities
                else:
                    self.logger.warning("LLM response is not a list")
                    return []
            else:
                self.logger.warning("No JSON array found in LLM response")
                return []
                
        except Exception as e:
            self.logger.error(f"LLM extraction failed: {str(e)}")
            return []
    
    def _create_extraction_prompt(self, text: str) -> str:
        """Create a prompt for entity extraction.
        
        Args:
            text: Text content
            
        Returns:
            Formatted prompt
        """
        prompt = f"""Extract inventory items from this text and return as a JSON array. For each item found, extract:
- name: The actual product name
- quantity: The number as integer
- price: The price as float (without currency symbol)
- category: The product category
- vendor: Manufacturer or vendor name
- part_number: Part number if available
- description: Product description

Text to extract from: {text}

Return a JSON array with the actual extracted items, not example data. If no items are found, return an empty array [].

JSON:"""
        return prompt
    
    def extract_inventory_items(self, text: str) -> List[InventoryItem]:
        """Extract inventory items from text.
        
        Args:
            text: Text content
            
        Returns:
            List of InventoryItem objects
        """
        entities = self.extract_entities(text)
        items = []
        
        for entity in entities:
            try:
                # Extract item information from LLM response
                item_name = entity.get('name', 'Unknown Item')
                description = entity.get('description', '')
                quantity = entity.get('quantity', 0)
                unit_price = entity.get('price', 0.0)
                category = entity.get('category', 'Unknown')
                vendor_name = entity.get('vendor', '')
                part_number = entity.get('part_number', '')
                
                item = InventoryItem(
                    item_name=item_name,
                    description=description,
                    quantity=quantity,
                    unit_price=unit_price,
                    category=category,
                    vendor_name=vendor_name,
                    part_number=part_number,
                    status=ItemStatus.PENDING
                )
                
                if self.validate_entity(entity):
                    items.append(item)
                else:
                    self.logger.warning(f"Skipping invalid entity: {entity}")
                    
            except Exception as e:
                self.logger.error(f"Error creating inventory item from entity {entity}: {str(e)}")
                continue
        
        return items
    
    def validate_entity(self, entity: Dict[str, Any]) -> bool:
        """Validate extracted entity.
        
        Args:
            entity: Entity dictionary
            
        Returns:
            True if valid, False otherwise
        """
        # Basic validation - must have at least a name
        if not entity.get('name') or entity.get('name') == 'Unknown Item':
            return False
        
        # Must have at least one meaningful field
        meaningful_fields = ['quantity', 'price', 'category', 'description']
        has_meaningful_data = any(
            entity.get(field) and entity.get(field) != 0 
            for field in meaningful_fields
        )
        
        return has_meaningful_data 

    def prompt_llm(self, prompt: str) -> str:
        """Directly prompt the underlying LLM and return the raw response text."""
        if self.gguf_model:
            try:
                result = self.gguf_model(
                    prompt,
                    max_tokens=512,
                    temperature=0.1,
                    top_p=0.9,
                    stop=["\n\n", "```"]
                )
                return result['choices'][0]['text']
            except Exception as e:
                self.logger.error(f"GGUF prompt failed: {str(e)}")
                return f"[ERROR] GGUF prompt failed: {str(e)}"
        elif self.llm_pipeline:
            try:
                result = self.llm_pipeline(prompt)
                return result[0]['generated_text']
            except Exception as e:
                self.logger.error(f"LLM prompt failed: {str(e)}")
                return f"[ERROR] LLM prompt failed: {str(e)}"
        else:
            self.logger.error("No LLM backend available for direct prompt.")
            return "[ERROR] No LLM backend available." 