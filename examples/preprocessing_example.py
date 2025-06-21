#!/usr/bin/env python3
"""Example script demonstrating preprocessing integration in text processing."""

import requests
import json
import time

# API base URL - adjust as needed
BASE_URL = "http://localhost:8000"

def example_with_preprocessing():
    """Example: Process text with preprocessing enabled."""
    print("🔧 Example: Text Processing with Preprocessing")
    print("=" * 60)
    
    # Sample inventory text
    text = """
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
        # Make API request with preprocessing enabled
        response = requests.post(
            f"{BASE_URL}/process-text",
            json={
                "text": text,
                "max_items": 10,
                "use_preprocessing": True,  # Enable preprocessing
                "return_preproc_results": True  # Include preprocessing results
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            
            print("✅ Processing successful!")
            print(f"📊 Items extracted: {result['items_extracted']}")
            print(f"⏱️  Processing time: {result['processing_time_seconds']}s")
            print(f"🔧 Preprocessing enabled: {result['use_preprocessing']}")
            
            # Display extracted items
            print(f"\n📦 Extracted Inventory Items:")
            for i, item in enumerate(result['items'], 1):
                print(f"  {i}. {item['item_name']}")
                print(f"     Quantity: {item['quantity']}")
                print(f"     Unit Price: ${item['unit_price']}")
                print(f"     Category: {item['category']}")
                print(f"     Vendor: {item['vendor_name']}")
                print()
            
            # Display preprocessing information
            if 'preprocessing_results' in result:
                preproc_info = result['preprocessing_results']['preprocessing']
                print(f"🔧 Preprocessing Details:")
                print(f"  Enabled: {preproc_info['enabled']}")
                print(f"  Original text length: {result['preprocessing_results']['text_length']} characters")
                print(f"  Preprocessed text length: {preproc_info['preprocessed_text_length']} characters")
                
                if preproc_info['results']:
                    print(f"  Layer results: {list(preproc_info['results'].keys())}")
            
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ API server not running. Start with: python api.py")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def example_without_preprocessing():
    """Example: Process text without preprocessing."""
    print("\n🔧 Example: Text Processing without Preprocessing")
    print("=" * 60)
    
    # Simple inventory text
    text = """
    INVENTORY LIST:
    
    Item: Laptop Dell XPS 13
    Quantity: 5
    Price: $1,299.99
    Category: Electronics
    
    Item: Office Chair
    Quantity: 10
    Price: $299.50
    Category: Furniture
    """
    
    try:
        # Make API request with preprocessing disabled
        response = requests.post(
            f"{BASE_URL}/process-text",
            json={
                "text": text,
                "max_items": 10,
                "use_preprocessing": False,  # Disable preprocessing
                "return_preproc_results": True  # Still get preprocessing info
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            
            print("✅ Processing successful!")
            print(f"📊 Items extracted: {result['items_extracted']}")
            print(f"⏱️  Processing time: {result['processing_time_seconds']}s")
            print(f"🔧 Preprocessing enabled: {result['use_preprocessing']}")
            
            # Display extracted items
            print(f"\n📦 Extracted Inventory Items:")
            for i, item in enumerate(result['items'], 1):
                print(f"  {i}. {item['item_name']} - Qty: {item['quantity']} - Price: ${item['unit_price']}")
            
            # Show preprocessing status
            if 'preprocessing_results' in result:
                preproc_info = result['preprocessing_results']['preprocessing']
                print(f"\n🔧 Preprocessing Status: {'Disabled' if not preproc_info['enabled'] else 'Enabled'}")
            
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text)
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ API server not running")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def example_comparison():
    """Example: Compare results with and without preprocessing."""
    print("\n🔧 Example: Comparing Preprocessing vs No Preprocessing")
    print("=" * 60)
    
    # Complex text that might benefit from preprocessing
    text = """
    messy inventory data:
    
    laptop dell xps 13 - 5 pcs - $1299.99
    office chair - qty 10 - $299.50
    coffee machine - 2 units - $89.99
    
    misc items:
    - pens (50 count) - $15.00
    - paper (500 sheets) - $25.00
    """
    
    try:
        # Test with preprocessing
        print("Testing WITH preprocessing...")
        response_with = requests.post(
            f"{BASE_URL}/process-text",
            json={
                "text": text,
                "max_items": 10,
                "use_preprocessing": True,
                "return_preproc_results": False
            }
        )
        
        # Test without preprocessing
        print("Testing WITHOUT preprocessing...")
        response_without = requests.post(
            f"{BASE_URL}/process-text",
            json={
                "text": text,
                "max_items": 10,
                "use_preprocessing": False,
                "return_preproc_results": False
            }
        )
        
        if response_with.status_code == 200 and response_without.status_code == 200:
            result_with = response_with.json()
            result_without = response_without.json()
            
            print(f"\n📊 Comparison Results:")
            print(f"  With preprocessing: {result_with['items_extracted']} items")
            print(f"  Without preprocessing: {result_without['items_extracted']} items")
            print(f"  Processing time with: {result_with['processing_time_seconds']}s")
            print(f"  Processing time without: {result_without['processing_time_seconds']}s")
            
            # Show items extracted with preprocessing
            print(f"\n📦 Items extracted WITH preprocessing:")
            for i, item in enumerate(result_with['items'], 1):
                print(f"  {i}. {item['item_name']} - Qty: {item['quantity']} - Price: ${item['unit_price']}")
            
            # Show items extracted without preprocessing
            print(f"\n📦 Items extracted WITHOUT preprocessing:")
            for i, item in enumerate(result_without['items'], 1):
                print(f"  {i}. {item['item_name']} - Qty: {item['quantity']} - Price: ${item['unit_price']}")
            
            return True
        else:
            print(f"❌ Error in comparison test")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ API server not running")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    """Run all preprocessing examples."""
    print("🔧 Preprocessing Integration Examples")
    print("=" * 60)
    print("This script demonstrates the new preprocessing functionality")
    print("in the text processing endpoint.")
    print()
    
    examples = [
        ("With Preprocessing", example_with_preprocessing),
        ("Without Preprocessing", example_without_preprocessing),
        ("Comparison", example_comparison),
    ]
    
    results = []
    for example_name, example_func in examples:
        print(f"\n📋 {example_name}")
        print("-" * 40)
        success = example_func()
        results.append((example_name, success))
    
    # Summary
    print("\n📊 Example Results Summary")
    print("=" * 40)
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for example_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {example_name}")
    
    print(f"\nOverall: {passed}/{total} examples completed successfully")
    
    if passed == total:
        print("🎉 All examples completed! Preprocessing integration is working.")
    else:
        print("⚠️  Some examples failed. Check the output above.")

if __name__ == "__main__":
    main() 