#!/usr/bin/env python3
"""Test model manager functionality."""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from quotient.core.config import QuotientConfig
from quotient.utils.model_manager import validate_model_config, ModelManager

def test_model_manager():
    """Test model manager functionality."""
    
    print("🧪 Testing Model Manager...")
    print("=" * 50)
    
    # Load config
    config = QuotientConfig.from_yaml()
    
    # Test model manager
    manager = ModelManager(config)
    model_info = manager.get_model_info()
    
    print("📋 Model Information:")
    print(f"  Backend: {model_info['backend']}")
    print(f"  Status: {model_info['status']}")
    
    if model_info['local_model']:
        print(f"  Local Model: {model_info['local_model']['path']}")
        print(f"  Local Model Exists: {model_info['local_model']['exists']}")
    
    if model_info['remote_model']:
        print(f"  Remote Model: {model_info['remote_model']['id']}")
        print(f"  Token Configured: {model_info['remote_model']['token_configured']}")
    
    print("\n🔍 Validation Test:")
    is_valid = validate_model_config(config)
    print(f"  Configuration Valid: {'✅ Yes' if is_valid else '❌ No'}")
    
    print("\n🚀 Model Availability Test:")
    is_available = manager.ensure_model_available()
    print(f"  Model Available: {'✅ Yes' if is_available else '❌ No'}")
    
    print("\n" + "=" * 50)
    
    if is_valid and is_available:
        print("✅ All tests passed!")
        return True
    else:
        print("❌ Some tests failed!")
        return False

if __name__ == "__main__":
    test_model_manager() 