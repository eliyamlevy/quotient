#!/usr/bin/env python3
"""Test script for hardware detection and optimization."""

import os
import sys
import logging

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from quotient.utils.hardware_utils import HardwareDetector, print_hardware_info, get_optimal_device, get_model_config
from quotient.core.config import QuotientConfig
from quotient.babbage.processors.entity_extractor import EntityExtractor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_hardware_detection():
    """Test hardware detection functionality."""
    print("=== Testing Hardware Detection ===")
    
    try:
        # Create hardware detector
        detector = HardwareDetector()
        
        # Get device info
        device_info = detector.get_device_info()
        
        print(f"Device Type: {device_info['device_type']}")
        print(f"Available Memory: {device_info['available_memory_gb']:.1f}GB")
        
        if device_info['device_type'] == 'cuda':
            print(f"GPU: {device_info['gpu_name']}")
            print(f"CUDA Version: {device_info['cuda_version']}")
            print(f"Compute Capability: {device_info['gpu_compute_capability']}")
        
        print(f"Optimization Config: {device_info['optimization_config']}")
        
        # Test model configuration
        model_config = detector.get_model_config(model_size_gb=8.0)
        print(f"Model Config for 8GB model: {model_config}")
        
        return True
        
    except Exception as e:
        print(f"Hardware detection failed: {str(e)}")
        return False


def test_entity_extractor():
    """Test entity extractor with hardware optimization."""
    print("\n=== Testing Entity Extractor ===")
    
    try:
        # Create configuration
        config = QuotientConfig()
        config.llm_backend = "llama"  # Use local Llama model
        
        # Create entity extractor
        extractor = EntityExtractor(config)
        
        # Test text
        test_text = """
        Invoice #12345
        
        Qty: 100 pcs - Resistor 10kΩ 1/4W - $0.05 each - Total: $5.00
        Qty: 50 pcs - Capacitor 100µF 25V - $0.10 each - Total: $5.00
        Qty: 25 pcs - LED Red 5mm - $0.02 each - Total: $0.50
        
        Vendor: ABC Electronics Inc.
        Part Numbers: RES-10K-1/4W, CAP-100UF-25V, LED-RED-5MM
        """
        
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
        
        return True
        
    except Exception as e:
        print(f"Entity extraction failed: {str(e)}")
        return False


def test_configuration():
    """Test configuration for CUDA deployment with Llama backend."""
    print("\n=== Testing Configuration ===")
    
    try:
        # Test Llama configuration
        config_llama = QuotientConfig()
        config_llama.llm_backend = "llama"
        config_llama.llama_model = "meta-llama/Llama-2-7b-chat-hf"
        
        print(f"Llama Config: {config_llama.llm_backend}")
        print(f"Llama Model: {config_llama.llama_model}")
        
        # Test hardware configuration
        hw_config = config_llama.get_hardware_config()
        print(f"Hardware Config: {hw_config}")
        
        return True
        
    except Exception as e:
        print(f"Configuration test failed: {str(e)}")
        return False


def main():
    """Main test function."""
    print("Quotient Hardware-Aware AI System Test")
    print("=" * 50)
    
    # Print hardware information
    print_hardware_info()
    
    # Run tests
    tests = [
        ("Hardware Detection", test_hardware_detection),
        ("Configuration", test_configuration),
        ("Entity Extractor", test_entity_extractor),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\nRunning {test_name} test...")
        try:
            result = test_func()
            results.append((test_name, result))
            print(f"{test_name}: {'PASSED' if result else 'FAILED'}")
        except Exception as e:
            print(f"{test_name}: FAILED - {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "PASSED" if result else "FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The system is ready for deployment.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 