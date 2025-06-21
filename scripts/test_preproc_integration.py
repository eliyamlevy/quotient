#!/usr/bin/env python3
"""Test script for preprocessing integration in text processing endpoint."""

import requests
import json
import time
from pathlib import Path

# API base URL - adjust as needed
BASE_URL = "http://localhost:8000"

def test_text_processing_with_preprocessing():
    """Test text processing with preprocessing enabled."""
    sample_text = """
    INVENTORY LIST:
    
    Item: Laptop Dell XPS 13
    Quantity: 5
    Price: $1,299.99
    Category: Electronics
    
    Item: Office Chair
    Quantity: 10
    Price: $299.50
    Category: Furniture
    
    Item: Coffee Machine
    Quantity: 2
    Price: $89.99
    Category: Appliances
    """
    
    try:
        print("🧪 Testing text processing with preprocessing enabled...")
        print("-" * 60)
        print(f"Input text:\n{sample_text}")
        print("-" * 60)
        
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/process-text",
            json={
                "text": sample_text,
                "max_items": 10,
                "use_preprocessing": True,
                "return_preproc_results": True
            }
        )
        processing_time = time.time() - start_time
        
        print(f"Status: {response.status_code}")
        print(f"Processing time: {processing_time:.2f}s")
        
        if response.status_code == 200:
            result = response.json()
            print("\n📋 Results:")
            print("=" * 30)
            print(f"Success: {result.get('success')}")
            print(f"Items extracted: {result.get('items_extracted')}")
            print(f"Processing time: {result.get('processing_time_seconds')}s")
            print(f"Preprocessing enabled: {result.get('use_preprocessing')}")
            
            # Show extracted items
            print(f"\n📦 Extracted Items ({len(result.get('items', []))}):")
            for i, item in enumerate(result.get('items', []), 1):
                print(f"  {i}. {item.get('item_name')} - Qty: {item.get('quantity')} - Price: ${item.get('unit_price')}")
            
            # Show preprocessing results if available
            if 'preprocessing_results' in result:
                preproc_info = result['preprocessing_results'].get('preprocessing', {})
                print(f"\n🔧 Preprocessing Results:")
                print(f"  Enabled: {preproc_info.get('enabled')}")
                print(f"  Original text length: {result['preprocessing_results'].get('text_length')}")
                print(f"  Preprocessed text length: {preproc_info.get('preprocessed_text_length')}")
                
                if preproc_info.get('results'):
                    print(f"  Layer results available: {list(preproc_info['results'].keys())}")
            
            return True, result
        else:
            print(f"❌ Error: {response.text}")
            return False, None
            
    except requests.exceptions.ConnectionError:
        print("❌ API server not running. Start with: python api.py")
        return False, None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False, None

def test_text_processing_without_preprocessing():
    """Test text processing with preprocessing disabled."""
    sample_text = """
    INVENTORY LIST:
    
    Item: Laptop Dell XPS 13
    Quantity: 5
    Price: $1,299.99
    Category: Electronics
    """
    
    try:
        print("\n🧪 Testing text processing without preprocessing...")
        print("-" * 60)
        
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/process-text",
            json={
                "text": sample_text,
                "max_items": 10,
                "use_preprocessing": False,
                "return_preproc_results": True
            }
        )
        processing_time = time.time() - start_time
        
        print(f"Status: {response.status_code}")
        print(f"Processing time: {processing_time:.2f}s")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Success: {result.get('success')}")
            print(f"Items extracted: {result.get('items_extracted')}")
            print(f"Preprocessing enabled: {result.get('use_preprocessing')}")
            
            # Show preprocessing results
            if 'preprocessing_results' in result:
                preproc_info = result['preprocessing_results'].get('preprocessing', {})
                print(f"Preprocessing enabled in results: {preproc_info.get('enabled')}")
            
            return True, result
        else:
            print(f"❌ Error: {response.text}")
            return False, None
            
    except requests.exceptions.ConnectionError:
        print("❌ API server not running")
        return False, None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False, None

def test_complex_text_with_preprocessing():
    """Test complex text with preprocessing."""
    complex_text = """
    PURCHASE ORDER #PO-2024-001
    
    Vendor: Tech Supplies Inc.
    Date: 2024-01-15
    
    ITEMS ORDERED:
    1. Dell XPS 13 Laptop (SKU: DELL-XPS13-2024)
       Qty: 5 units
       Unit Price: $1,299.99
       Total: $6,499.95
    
    2. Herman Miller Aeron Chair (Product Code: HM-AERON-M)
       Amount: 10 pieces
       Price per unit: $299.50
       Subtotal: $2,995.00
    
    3. Coffee Machine - Breville BES870XL (Item #: BR-BES870XL)
       Number of items: 2
       Cost: $89.99 each
       Line total: $179.98
    
    GRAND TOTAL: $9,674.93
    """
    
    try:
        print("\n🧪 Testing complex text with preprocessing...")
        print("-" * 60)
        
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/process-text",
            json={
                "text": complex_text,
                "max_items": 10,
                "use_preprocessing": True,
                "return_preproc_results": True
            }
        )
        processing_time = time.time() - start_time
        
        print(f"Status: {response.status_code}")
        print(f"Processing time: {processing_time:.2f}s")
        
        if response.status_code == 200:
            result = response.json()
            print(f"Success: {result.get('success')}")
            print(f"Items extracted: {result.get('items_extracted')}")
            
            # Show extracted items
            print(f"\n📦 Extracted Items:")
            for i, item in enumerate(result.get('items', []), 1):
                print(f"  {i}. {item.get('item_name')} - Qty: {item.get('quantity')} - Price: ${item.get('unit_price')}")
            
            return True, result
        else:
            print(f"❌ Error: {response.text}")
            return False, None
            
    except requests.exceptions.ConnectionError:
        print("❌ API server not running")
        return False, None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False, None

def main():
    """Run all preprocessing integration tests."""
    print("🧪 Testing Preprocessing Integration in Text Processing...")
    print("=" * 70)
    
    tests = [
        ("Text Processing with Preprocessing", test_text_processing_with_preprocessing),
        ("Text Processing without Preprocessing", test_text_processing_without_preprocessing),
        ("Complex Text with Preprocessing", test_complex_text_with_preprocessing),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 50)
        success = test_func()
        results.append((test_name, success))
        print()
    
    # Summary
    print("📊 Test Results Summary")
    print("=" * 50)
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Preprocessing integration is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above.")

if __name__ == "__main__":
    main() 