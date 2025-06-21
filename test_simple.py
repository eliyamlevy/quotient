#!/usr/bin/env python3
"""Simple test to verify Quotient setup works."""

import sys
from pathlib import Path

def test_imports():
    """Test that all imports work correctly."""
    print("Testing imports...")
    
    try:
        from quotient.core.config import QuotientConfig
        print("✅ QuotientConfig imported successfully")
        
        from quotient.utils.data_models import InventoryItem, ProcessingResult
        print("✅ Data models imported successfully")
        
        from quotient.babbage import Babbage
        print("✅ Babbage service imported successfully")
        
        from quotient.core.pipeline import QuotientPipeline
        print("✅ QuotientPipeline imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_config():
    """Test configuration creation."""
    print("\nTesting configuration...")
    
    try:
        from quotient.core.config import QuotientConfig
        
        config = QuotientConfig()
        print("✅ Configuration created successfully")
        print(f"   - OpenAI configured: {config.is_ai_enabled()}")
        print(f"   - Supported formats: {len(config.get_supported_formats())}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_data_models():
    """Test data model creation."""
    print("\nTesting data models...")
    
    try:
        from quotient.utils.data_models import InventoryItem, ProcessingResult, ItemStatus
        
        # Test InventoryItem
        item = InventoryItem(
            item_name="Test Item",
            quantity=10,
            unit_price=5.99
        )
        print("✅ InventoryItem created successfully")
        
        # Test ProcessingResult
        result = ProcessingResult(
            source_path="test.txt",
            items=[item]
        )
        print("✅ ProcessingResult created successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Data model test failed: {e}")
        return False

def test_babbage_service():
    """Test Babbage service initialization."""
    print("\nTesting Babbage service...")
    
    try:
        from quotient.core.config import QuotientConfig
        from quotient.babbage import Babbage
        
        config = QuotientConfig()
        babbage = Babbage(config)
        
        print("✅ Babbage service initialized successfully")
        print(f"   - Supported formats: {babbage.get_supported_formats()}")
        
        # Test service status
        status = babbage.get_service_status()
        print(f"   - Service status: {status['status']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Babbage service test failed: {e}")
        return False

def test_pipeline():
    """Test pipeline initialization."""
    print("\nTesting pipeline...")
    
    try:
        from quotient.core.config import QuotientConfig
        from quotient.core.pipeline import QuotientPipeline
        
        config = QuotientConfig()
        pipeline = QuotientPipeline(config)
        
        print("✅ Pipeline initialized successfully")
        
        # Test pipeline status
        status = pipeline.get_processing_status()
        print(f"   - Layer 1 (Babbage): {status['layer1_babbage']}")
        print(f"   - Layer 2: {status['layer2_gap_analysis']}")
        print(f"   - Layer 3: {status['layer3_data_completion']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Pipeline test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing Quotient Setup")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_config,
        test_data_models,
        test_babbage_service,
        test_pipeline
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Quotient is ready to use.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 