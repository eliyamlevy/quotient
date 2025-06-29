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
        
        if not TORCH_AVAILABLE:
            self.logger.warning("PyTorch not available, AI features will be limited")
            return
        
        if not TRANSFORMERS_AVAILABLE:
            self.logger.warning("Transformers not available, AI features will be limited")
            return
        
        self.device = get_optimal_device()
        self._initialize_llama()
    
    def _initialize_llama(self):
        """Initialize Llama model for local inference."""
        if not TORCH_AVAILABLE or not TRANSFORMERS_AVAILABLE:
            self.logger.error("PyTorch or Transformers not available for Llama model")
            return
            
        try:
            model_id = getattr(self.config, 'llama_model', 'meta-llama/Llama-2-7b-chat-hf')
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
                trust_remote_code=True
            )
            
            # Create pipeline
            self.llm_pipeline = pipeline(
                "text-generation",
                model=model,
                tokenizer=tokenizer,
                device=self.device,
                max_new_tokens=512,  # Increased for better responses
                do_sample=True,
                temperature=0.1,
                top_p=0.9,
                pad_token_id=tokenizer.eos_token_id
            )
            
            self.logger.info("Local LLM model loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to load local LLM model: {str(e)}")
            self.llm_pipeline = None
    
    def extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract entities from text content.
        
        Args:
            text: Text content to extract entities from
            
        Returns:
            List of extracted entities
        """
        self.logger.info("Extracting entities from text")
        
        try:
            if self.llm_pipeline:
                return self._extract_with_llama(text)
            else:
                return self._extract_with_rules(text)
                
        except Exception as e:
            self.logger.error(f"Error extracting entities: {str(e)}")
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
                    return entities
                else:
                    self.logger.warning("LLM response is not a list, using rule-based extraction")
                    return self._extract_with_rules(text)
            else:
                self.logger.warning("No JSON array found in LLM response, using rule-based extraction")
                return self._extract_with_rules(text)
                
        except Exception as e:
            self.logger.error(f"LLM extraction failed: {str(e)}")
            return self._extract_with_rules(text)
    
    def _create_extraction_prompt(self, text: str) -> str:
        """Create a prompt for entity extraction.
        
        Args:
            text: Text content
            
        Returns:
            Formatted prompt
        """
        prompt = f"""Extract inventory items from this text and return as JSON array. Each item should have: name, quantity, price, category, status.

Text: {text}

Return only the JSON array, no other text:
["""
        return prompt
    
    def _extract_with_rules(self, text: str) -> List[Dict[str, Any]]:
        """Extract entities using rule-based approach.
        
        Args:
            text: Text content
            
        Returns:
            List of extracted entities
        """
        entities = []
        
        # Split text into lines for processing
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            entity = self._extract_entity_from_line(line)
            if entity:
                entities.append(entity)
        
        return entities
    
    def _extract_entity_from_line(self, line: str) -> Optional[Dict[str, Any]]:
        """Extract entity information from a single line.
        
        Args:
            line: Text line
            
        Returns:
            Entity dictionary or None
        """
        # Skip lines that are clearly not product information
        if len(line) < 5 or line.startswith('#'):
            return None
        
        entity = {'original_line': line}  # Store original line for clean name extraction
        
        # Extract quantity
        quantity_match = re.search(r'\b(\d+)\s*(pcs?|pieces?|units?|items?|kg|lbs?|meters?|m|cm|mm)\b', line, re.IGNORECASE)
        if quantity_match:
            entity['quantity'] = int(quantity_match.group(1))
            entity['unit'] = quantity_match.group(2)
        
        # Extract price information
        price_match = re.search(r'\$(\d+\.?\d*)', line)
        if price_match:
            entity['unit_price'] = float(price_match.group(1))
        
        # Extract part numbers (common patterns)
        part_patterns = [
            r'\b[A-Z]{2,}\d+[A-Z0-9]*\b',  # ABC123
            r'\b\d+[A-Z]{2,}\d*\b',  # 123ABC
            r'\b[A-Z]+\-\d+\b',  # ABC-123
            r'\b\d+\-[A-Z]+\b',  # 123-ABC
        ]
        
        for pattern in part_patterns:
            part_match = re.search(pattern, line)
            if part_match:
                entity['part_number'] = part_match.group(0)
                break
        
        # Extract manufacturer names (common patterns)
        manufacturer_patterns = [
            r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Inc|Corp|LLC|Ltd|Company|Co)\b',
            r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Technologies|Systems|Solutions|Group)\b',
        ]
        
        for pattern in manufacturer_patterns:
            mfg_match = re.search(pattern, line)
            if mfg_match:
                entity['manufacturer'] = mfg_match.group(0)
                break
        
        # Extract category information
        category_keywords = {
            'electronics': ['circuit', 'board', 'chip', 'resistor', 'capacitor', 'diode'],
            'mechanical': ['bolt', 'nut', 'screw', 'bearing', 'gear', 'pump'],
            'chemical': ['chemical', 'acid', 'base', 'solvent', 'reagent'],
            'office': ['paper', 'pen', 'pencil', 'folder', 'binder'],
            'tools': ['wrench', 'screwdriver', 'hammer', 'drill', 'saw'],
        }
        
        line_lower = line.lower()
        for category, keywords in category_keywords.items():
            if any(keyword in line_lower for keyword in keywords):
                entity['category'] = category
                break
        
        # Extract description (remaining text after removing structured data)
        description = self._extract_description(line)
        if description:
            entity['description'] = description
        
        # Only return entity if we have meaningful information
        if len(entity) >= 3:  # At least 2 fields plus original_line
            return entity
        
        return None
    
    def _extract_description(self, line: str) -> str:
        """Extract description from line by removing structured data.
        
        Args:
            line: Text line
            
        Returns:
            Cleaned description
        """
        # Remove price information
        line = re.sub(r'\$\d+\.?\d*', '', line)
        
        # Remove quantity information
        line = re.sub(r'\b\d+\s*(pcs?|pieces?|units?|items?|kg|lbs?|meters?|m|cm|mm)\b', '', line, flags=re.IGNORECASE)
        
        # Remove part numbers
        line = re.sub(r'\b[A-Z]{2,}\d+[A-Z0-9]*\b', '', line)
        line = re.sub(r'\b\d+[A-Z]{2,}\d*\b', '', line)
        line = re.sub(r'\b[A-Z]+\-\d+\b', '', line)
        line = re.sub(r'\b\d+\-[A-Z]+\b', '', line)
        
        # Remove manufacturer names
        line = re.sub(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Inc|Corp|LLC|Ltd|Company|Co)\b', '', line)
        line = re.sub(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Technologies|Systems|Solutions|Group)\b', '', line)
        
        # Remove common invoice prefixes and suffixes
        line = re.sub(r'^Qty:\s*-\s*', '', line)  # Remove "Qty: - " prefix
        line = re.sub(r'\s*-\s*each\s*-\s*Total:.*$', '', line)  # Remove "- each - Total: $X.XX"
        line = re.sub(r'\s*-\s*Total:.*$', '', line)  # Remove "- Total: $X.XX"
        line = re.sub(r'\s*each\s*', '', line)  # Remove "each"
        
        # Clean up extra whitespace and dashes
        description = re.sub(r'\s+', ' ', line).strip()
        description = re.sub(r'^\s*-\s*', '', description)  # Remove leading dash
        description = re.sub(r'\s*-\s*$', '', description)  # Remove trailing dash
        
        return description if len(description) > 3 else ""
    
    def _extract_item_name(self, line: str) -> str:
        """Extract clean item name from line.
        
        Args:
            line: Text line
            
        Returns:
            Clean item name
        """
        # Start with the cleaned description
        item_name = self._extract_description(line)
        
        # If we have a good item name, return it
        if item_name and len(item_name) > 3:
            return item_name
        
        # Fallback: try to extract product name patterns
        # Look for common product patterns
        product_patterns = [
            r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(?:Resistor|Capacitor|LED|Diode|Transistor|IC|Chip)\b',
            r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+\d+[A-ZΩµ]+\b',  # e.g., "Resistor 10kΩ"
            r'\b[A-Z][a-z]+\s+\d+[A-ZΩµ]+\s+\d+[A-Z]+\b',  # e.g., "Capacitor 100µF 25V"
        ]
        
        for pattern in product_patterns:
            match = re.search(pattern, line)
            if match:
                return match.group(0)
        
        # If all else fails, return a generic name
        return "Unknown Item"
    
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
                # Get the original line to extract clean item name
                original_line = entity.get('original_line', '')
                
                # Extract clean item name
                item_name = self._extract_item_name(original_line) if original_line else entity.get('name', 'Unknown Item')
                
                # If we don't have a good item name, try to create one from available data
                if item_name == 'Unknown Item' or len(item_name) < 3:
                    # Try to construct a name from available fields
                    name_parts = []
                    if entity.get('part_number'):
                        name_parts.append(entity.get('part_number'))
                    if entity.get('category') and entity.get('category') != 'Unknown':
                        name_parts.append(entity.get('category'))
                    if entity.get('description') and len(entity.get('description', '')) > 3:
                        name_parts.append(entity.get('description'))
                    
                    if name_parts:
                        item_name = ' '.join(name_parts)
                    else:
                        item_name = entity.get('description', 'Unknown Item')
                
                item = InventoryItem(
                    item_name=item_name,
                    description=entity.get('description', ''),
                    quantity=entity.get('quantity', 0),
                    unit_price=entity.get('unit_price', 0.0),
                    category=entity.get('category', 'Unknown'),
                    vendor_name=entity.get('manufacturer', ''),
                    part_number=entity.get('part_number', ''),
                    sku=entity.get('part_number', ''),
                    status=ItemStatus.PENDING
                )
                items.append(item)
                
            except Exception as e:
                self.logger.warning(f"Failed to create InventoryItem from entity: {str(e)}")
                continue
        
        return items
    
    def validate_entity(self, entity: Dict[str, Any]) -> bool:
        """Validate extracted entity.
        
        Args:
            entity: Entity dictionary
            
        Returns:
            True if entity is valid
        """
        # Must have at least a name or description
        if not entity.get('name') and not entity.get('description'):
            return False
        
        # Quantity should be positive if present
        if 'quantity' in entity and entity['quantity'] <= 0:
            return False
        
        # Price should be positive if present
        if 'unit_price' in entity and entity['unit_price'] < 0:
            return False
        
        return True 