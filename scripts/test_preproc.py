#!/usr/bin/env python3
"""Test script for the Quotient preprocessing pipeline."""

import requests
import json
import time
from pathlib import Path

# API base URL - adjust as needed
BASE_URL = "http://multivac:8000"

def test_preproc_endpoint(text: str, test_name: str = "Unknown"):
    """Test the preprocessing endpoint with given text."""
    try:
        print(f"\n🧪 Testing: {test_name}")
        print("-" * 50)
        print(f"Input text:\n{text}")
        print("-" * 50)
        
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/preproc-text",
            json={"text": text}
        )
        processing_time = time.time() - start_time
        
        print(f"Status: {response.status_code}")
        print(f"Processing time: {processing_time:.2f}s")
        
        if response.status_code == 200:
            result = response.json()
            print("\n📋 Results:")
            print("=" * 30)
            
            for layer, output in result.items():
                print(f"\n🔹 {layer.upper()}:")
                print(f"{output}")
                print("-" * 20)
            
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

def test_simple_inventory():
    """Test with simple, clean inventory text."""
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
    return test_preproc_endpoint(text, "Simple Inventory")

def test_complex_inventory():
    """Test with complex inventory text with various formats."""
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
    return test_preproc_endpoint(text, "Complex Inventory")

def test_messy_text():
    """Test with messy, inconsistent text."""
    text = """
    random inventory stuff
    
    laptop dell xps 13 - 5 pcs - $1299.99
    office chair - qty 10 - $299.50
    coffee machine - 2 units - $89.99
    
    misc items:
    - pens (50 count) - $15.00
    - paper (500 sheets) - $25.00
    """
    return test_preproc_endpoint(text, "Messy Text")

def test_edge_cases():
    """Test with edge cases and ambiguous text."""
    text = """
    INVENTORY UPDATE:
    
    We need to order:
    - More laptops (Dell XPS 13) - around 5-10 pieces
    - Some chairs - maybe 10-15 units
    - Coffee machines - 2 or 3 should be enough
    
    Also check:
    - Current stock levels
    - Price variations
    - Delivery times
    """
    return test_preproc_endpoint(text, "Edge Cases")

def test_technical_specs():
    """Test with technical specifications."""
    text = """
    TECHNICAL SPECIFICATIONS:
    
    Product: Dell XPS 13 (Model: XPS13-9320)
    Specifications:
    - Processor: Intel Core i7-1250U
    - Memory: 16GB LPDDR5
    - Storage: 512GB PCIe NVMe SSD
    - Display: 13.4" FHD+ (1920x1200)
    - Weight: 2.59 lbs
    - Dimensions: 11.63" x 7.86" x 0.55"
    
    Quantity Required: 5 units
    Unit Cost: $1,299.99
    """
    return test_preproc_endpoint(text, "Technical Specs")

def test_multilingual():
    """Test with mixed language content."""
    text = """
    INVENTARIO / INVENTORY:
    
    Español:
    - Laptop Dell XPS 13: 5 unidades
    - Silla de oficina: 10 piezas
    - Máquina de café: 2 unidades
    
    English:
    - Dell XPS 13 Laptop: 5 units
    - Office Chair: 10 pieces
    - Coffee Machine: 2 units
    
    Français:
    - Ordinateur portable Dell XPS 13: 5 unités
    - Chaise de bureau: 10 pièces
    - Machine à café: 2 unités
    """
    return test_preproc_endpoint(text, "Multilingual")

def test_receipt_format():
    """Test with receipt-like format."""
    text = """
    RECEIPT
    Store: TechMart
    Date: 01/15/2024
    Time: 14:30
    
    ITEM                    QTY    PRICE    TOTAL
    Dell XPS 13 Laptop     5      $1299.99 $6499.95
    Office Chair           10     $299.50  $2995.00
    Coffee Machine         2      $89.99   $179.98
    
    SUBTOTAL: $9674.93
    TAX: $774.00
    TOTAL: $10448.93
    """
    return test_preproc_endpoint(text, "Receipt Format")

def test_json_like():
    """Test with JSON-like structured text."""
    text = """
    {
      "order_id": "PO-2024-001",
      "items": [
        {
          "name": "Dell XPS 13 Laptop",
          "sku": "DELL-XPS13-2024",
          "quantity": 5,
          "unit_price": 1299.99,
          "total": 6499.95
        },
        {
          "name": "Office Chair",
          "sku": "CHAIR-001",
          "quantity": 10,
          "unit_price": 299.50,
          "total": 2995.00
        }
      ]
    }
    """
    return test_preproc_endpoint(text, "JSON-like Structure")

def main():
    """Run all preprocessing tests."""
    print("🧪 Testing Quotient Preprocessing Pipeline...")
    print("=" * 60)
    
    # Test cases
    test_cases = [
        test_simple_inventory,
        test_complex_inventory,
        test_messy_text,
        test_edge_cases,
        test_technical_specs,
        test_multilingual,
        test_receipt_format,
        test_json_like,
    ]
    
    results = []
    for test_func in test_cases:
        success, result = test_func()
        results.append((test_func.__name__, success, result))
        
        if success:
            print("✅ Test completed successfully")
        else:
            print("❌ Test failed")
        
        print("\n" + "="*60)
    
    # Summary
    print("\n📊 Test Results Summary")
    print("=" * 60)
    passed = sum(1 for _, success, _ in results if success)
    total = len(results)
    
    for test_name, success, _ in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All preprocessing tests passed!")
    else:
        print("⚠️  Some tests failed. Review the output above.")
    
    # Analysis suggestions
    print("\n💡 Analysis Suggestions:")
    print("- Check if Layer 1 (lowercase) is working correctly")
    print("- Verify Layer 2 (label clarification) is replacing quantity/item_id terms")
    print("- Ensure Layer 3 (item recognition) is properly separating items")
    print("- Look for any LLM hallucinations or misinterpretations")
    print("- Consider prompt refinements based on failures")

if __name__ == "__main__":
    main() 