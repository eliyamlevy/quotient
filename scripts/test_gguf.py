#!/usr/bin/env python3
"""Test GGUF model functionality."""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from quotient.core.config import QuotientConfig
from quotient.babbage.processors.entity_extractor import EntityExtractor

def test_gguf_model():
    """Test GGUF model loading and inference."""
    
    # Create a test config with GGUF model path
    config = QuotientConfig.from_yaml()
    
    print(f"Testing GGUF model: {config.gguf_model_path}")
    
    try:
        # Initialize entity extractor
        extractor = EntityExtractor(config)
        print("✓ Entity extractor initialized successfully")
        
        # Test text extraction
        test_text = """
        Invoice Items:
        - 2x Dell XPS 13 Laptop, $1,299.99 each
        - 1x Logitech MX Master 3 Mouse, $99.99
        - 5x USB-C Cables, $12.50 each
        """
        
        print("\nTesting entity extraction...")
        entities = extractor.extract_entities(test_text)
        
        print(f"✓ Extracted {len(entities)} entities:")
        for entity in entities:
            print(f"  - {entity}")
        
        # Test direct prompting
        print("\nTesting direct prompting...")
        response = extractor.prompt_llm("What is 2+2?")
        print(f"✓ LLM Response: {response[:100]}...")
        
        print("\n✓ All tests passed!")
        
    except Exception as e:
        print(f"✗ Test failed: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    test_gguf_model() 
