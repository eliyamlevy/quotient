#!/usr/bin/env python3
"""
Test script for the slimmed-down Quotient system.
"""

import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from quotient.core import QuotientPipeline, QuotientConfig


def test_hardware():
    """Test hardware detection."""
    print("🔍 Testing Hardware Detection")
    print("=" * 40)
    
    try:
        from quotient.utils.hardware_utils import print_hardware_info
        print_hardware_info()
    except Exception as e:
        print(f"❌ Hardware detection failed: {e}")


def test_config():
    """Test configuration."""
    print("\n⚙️ Testing Configuration")
    print("=" * 40)
    
    try:
        config = QuotientConfig.from_yaml()
        print(f"✅ Configuration loaded successfully")
        print(f"   LLM Backend: {config.llm_backend}")
        print(f"   Model: {config.llama_model}")
        print(f"   CUDA: {config.use_cuda}")
        print(f"   MPS: {config.use_mps}")
        print(f"   Max Memory: {config.max_memory_gb}GB")
        print(f"   Supported Formats: {config.supported_formats}")
    except Exception as e:
        print(f"❌ Configuration failed: {e}")


def test_pipeline():
    """Test pipeline initialization."""
    print("\n🚀 Testing Pipeline")
    print("=" * 40)
    
    try:
        config = QuotientConfig.from_yaml()
        pipeline = QuotientPipeline(config)
        print("✅ Pipeline initialized successfully")
        
        # Test status
        status = pipeline.get_processing_status()
        print(f"   Layer 1 (Babbage): {status['layer1_babbage']}")
        print(f"   LLM Backend: {status['config']['llm_backend']}")
        print(f"   Model: {status['config']['llama_model']}")
        
    except Exception as e:
        print(f"❌ Pipeline initialization failed: {e}")


def test_document_processing():
    """Test document processing."""
    print("\n📄 Testing Document Processing")
    print("=" * 40)
    
    # Test with a simple text file
    test_content = """
    INVENTORY LIST
    
    Item: Laptop Computer
    Quantity: 5
    Price: $1200.00
    
    Item: Wireless Mouse
    Quantity: 10
    Price: $25.50
    
    Item: USB Cable
    Quantity: 20
    Price: $5.00
    """
    
    test_file = Path("test_inventory.txt")
    try:
        with open(test_file, "w") as f:
            f.write(test_content)
        
        config = QuotientConfig.from_yaml()
        pipeline = QuotientPipeline(config)
        
        print(f"Processing test file: {test_file}")
        result = pipeline.process_single_document(test_file)
        
        print(f"✅ Processing completed")
        print(f"   Items extracted: {len(result.items)}")
        print(f"   Processing time: {result.processing_time:.2f}s")
        print(f"   Confidence: {result.extraction_confidence:.2f}")
        
        if result.items:
            print("\n📦 Extracted Items:")
            for i, item in enumerate(result.items, 1):
                print(f"   {i}. {item.item_name}")
                print(f"      Quantity: {item.quantity}")
                print(f"      Price: ${item.unit_price}")
        
        # Clean up
        test_file.unlink()
        
    except Exception as e:
        print(f"❌ Document processing failed: {e}")
        if test_file.exists():
            test_file.unlink()


def main():
    """Run all tests."""
    print("🧪 Testing Slimmed-Down Quotient System")
    print("=" * 50)
    
    test_hardware()
    test_config()
    test_pipeline()
    test_document_processing()
    
    print("\n✅ All tests completed!")


if __name__ == "__main__":
    main() 