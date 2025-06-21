#!/usr/bin/env python3
"""Test Babbage with different Llama models locally."""

import os
import sys
import logging

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from quotient.core.config import QuotientConfig
from quotient.babbage.processors.entity_extractor import EntityExtractor
from quotient.utils.hardware_utils import print_hardware_info

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_with_open_model():
    """Test with an open-access model."""
    
    # Try different open models
    open_models = [
        "microsoft/DialoGPT-medium",  # Smaller, open model
        "gpt2",  # Very small, definitely open
        "distilgpt2",  # Even smaller
    ]
    
    test_text = """
    Invoice #12345
    
    Qty: 100 pcs - Resistor 10kΩ 1/4W - $0.05 each - Total: $5.00
    Qty: 50 pcs - Capacitor 100µF 25V - $0.10 each - Total: $5.00
    Qty: 25 pcs - LED Red 5mm - $0.02 each - Total: $0.50
    
    Vendor: ABC Electronics Inc.
    Part Numbers: RES-10K-1/4W, CAP-100UF-25V, LED-RED-5MM
    """
    
    for model_id in open_models:
        print(f"\n{'='*60}")
        print(f"Testing with model: {model_id}")
        print(f"{'='*60}")
        
        try:
            # Create configuration
            config = QuotientConfig()
            config.llm_backend = "llama"
            config.llm_id = model_id
            
            # Create entity extractor
            extractor = EntityExtractor(config)
            
            # Extract entities
            entities = extractor.extract_entities(test_text)
            print(f"Extracted {len(entities)} entities:")
            
            for i, entity in enumerate(entities, 1):
                print(f"  {i}. {entity}")
            
            # Extract inventory items
            items = extractor.extract_inventory_items(test_text)
            print(f"\nExtracted {len(items)} inventory items:")
            
            for i, item in enumerate(items, 1):
                print(f"  {i}. {item.item_name} - Qty: {item.quantity} - Price: ${item.unit_price}")
            
            print(f"\n✅ Model {model_id} works!")
            return True
            
        except Exception as e:
            print(f"❌ Model {model_id} failed: {str(e)}")
            continue
    
    return False


def test_rule_based_fallback():
    """Test the rule-based fallback when LLM is not available."""
    print(f"\n{'='*60}")
    print("Testing Rule-Based Fallback")
    print(f"{'='*60}")
    
    test_text = """
    Invoice #12345
    
    Qty: 100 pcs - Resistor 10kΩ 1/4W - $0.05 each - Total: $5.00
    Qty: 50 pcs - Capacitor 100µF 25V - $0.10 each - Total: $5.00
    Qty: 25 pcs - LED Red 5mm - $0.02 each - Total: $0.50
    
    Vendor: ABC Electronics Inc.
    Part Numbers: RES-10K-1/4W, CAP-100UF-25V, LED-RED-5MM
    """
    
    try:
        # Create configuration without LLM
        config = QuotientConfig()
        config.llm_backend = "none"  # Force rule-based
        
        # Create entity extractor
        extractor = EntityExtractor(config)
        
        # Extract entities
        entities = extractor.extract_entities(test_text)
        print(f"Extracted {len(entities)} entities:")
        
        for i, entity in enumerate(entities, 1):
            print(f"  {i}. {entity}")
        
        # Extract inventory items
        items = extractor.extract_inventory_items(test_text)
        print(f"\nExtracted {len(items)} inventory items:")
        
        for i, item in enumerate(items, 1):
            print(f"  {i}. {item.item_name} - Qty: {item.quantity} - Price: ${item.unit_price}")
        
        print("\n✅ Rule-based extraction works!")
        return True
        
    except Exception as e:
        print(f"❌ Rule-based extraction failed: {str(e)}")
        return False


def main():
    """Main test function."""
    print("Testing Babbage with Local LLM Models")
    print("=" * 60)
    
    # Print hardware information
    print_hardware_info()
    
    # Test with open models
    success = test_with_open_model()
    
    if not success:
        print("\nFalling back to rule-based extraction...")
        test_rule_based_fallback()
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main() 