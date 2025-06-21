"""AI-powered entity extraction from text content."""

import logging
from typing import List, Dict, Any, Optional
import json
import re

# Optional imports for AI/ML functionality
try:
    import torch
    from openai import OpenAI
    TORCH_AVAILABLE = True
    OPENAI_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    OPENAI_AVAILABLE = False

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
        self.llm_backend = getattr(config, 'llm_backend', 'openai')
        self.device = None
        self.llm_pipeline = None
        self.client = None
        
        if not TORCH_AVAILABLE:
            self.logger.warning("PyTorch not available, AI features will be limited")
            return
        
        self.device = get_optimal_device()
        
        if self.llm_backend == 'llama':
            self._initialize_llama()
        elif OPENAI_AVAILABLE and hasattr(config, 'openai_api_key') and config.openai_api_key:
            self.client = OpenAI(api_key=config.openai_api_key)
        else:
            self.logger.warning("No LLM backend configured, entity extraction will be limited")
    
    def _initialize_llama(self):
        """Initialize Llama model for local inference."""
        if not TORCH_AVAILABLE:
            self.logger.error("PyTorch not available for Llama model")
            return
            
        try:
            from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
            
            model_id = getattr(self.config, 'llama_model', 'meta-llama/Meta-Llama-3-8B-Instruct')
            self.logger.info(f"Loading Llama model: {model_id}")
            
            # Get hardware-optimized config
            config = get_model_config(model_size_gb=8.0)  # Assume 8GB model
            
            # Load tokenizer
            tokenizer = AutoTokenizer.from_pretrained(model_id)
            
            # Load model with hardware optimization
            model = AutoModelForCausalLM.from_pretrained(
                model_id,
                torch_dtype=config["torch_dtype"],
                device_map=config["device_map"],
                load_in_8bit=config["load_in_8bit"],
                load_in_4bit=config.get("load_in_4bit", False),
                trust_remote_code=True
            )
            
            # Create pipeline
            self.llm_pipeline = pipeline(
                "text-generation",
                model=model,
                tokenizer=tokenizer,
                device=self.device,
                max_new_tokens=512,
                do_sample=True,
                temperature=0.1,
                top_p=0.9
            )
            
            self.logger.info("Llama model loaded successfully")
            
        except ImportError:
            self.logger.error("transformers library not installed. Install with: pip install transformers")
            self.llm_pipeline = None
        except Exception as e:
            self.logger.error(f"Failed to load Llama model: {str(e)}")
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
            if self.llm_backend == 'llama' and self.llm_pipeline:
                return self._extract_with_llama(text)
            elif self.client:
                return self._extract_with_openai(text)
            else:
                return self._extract_with_rules(text)
                
        except Exception as e:
            self.logger.error(f"Error extracting entities: {str(e)}")
            return []
    
    def _extract_with_llama(self, text: str) -> List[Dict[str, Any]]:
        """Extract entities using local Llama model.
        
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
                    self.logger.warning("Llama response is not a list, using rule-based extraction")
                    return self._extract_with_rules(text)
            else:
                self.logger.warning("No JSON array found in Llama response, using rule-based extraction")
                return self._extract_with_rules(text)
                
        except Exception as e:
            self.logger.error(f"Llama extraction failed: {str(e)}")
            return self._extract_with_rules(text)
    
    def _extract_with_openai(self, text: str) -> List[Dict[str, Any]]:
        """Extract entities using OpenAI.
        
        Args:
            text: Text content
            
        Returns:
            List of extracted entities
        """
        try:
            prompt = self._create_extraction_prompt(text)
            
            response = self.client.chat.completions.create(
                model=self.config.openai_model or "gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert at extracting inventory-related information from text. Extract all relevant entities and return them as a JSON array."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content
            
            # Parse JSON response
            try:
                entities = json.loads(content)
                if isinstance(entities, list):
                    return entities
                else:
                    self.logger.warning("AI response is not a list, using rule-based extraction")
                    return self._extract_with_rules(text)
                    
            except json.JSONDecodeError:
                self.logger.warning("Failed to parse AI response as JSON, using rule-based extraction")
                return self._extract_with_rules(text)
                
        except Exception as e:
            self.logger.error(f"AI extraction failed: {str(e)}")
            return self._extract_with_rules(text)
    
    def _create_extraction_prompt(self, text: str) -> str:
        """Create prompt for entity extraction.
        
        Args:
            text: Text content
            
        Returns:
            Formatted prompt
        """
        return f"""
Extract inventory-related entities from the following text. Return the results as a JSON array of objects with these fields:
- name: Product/part name
- description: Description of the item
- quantity: Quantity (number)
- unit_price: Unit price (number, extract from text)
- total_price: Total price (number, calculate if possible)
- category: Category/type of item
- manufacturer: Manufacturer/vendor name
- part_number: Part number/SKU
- unit: Unit of measurement (pcs, kg, etc.)

Text to analyze:
{text[:3000]}  # Limit text length for API

Return only valid JSON array.
"""
    
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
        
        entity = {}
        
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
        if len(entity) >= 2:  # At least 2 fields
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
        
        # Clean up extra whitespace
        description = re.sub(r'\s+', ' ', line).strip()
        
        return description if len(description) > 3 else ""
    
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
                item = InventoryItem(
                    item_name=entity.get('name', entity.get('description', 'Unknown Item')),
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