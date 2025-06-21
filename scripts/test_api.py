#!/usr/bin/env python3
"""Test script for the Quotient API."""

import requests
import json
from pathlib import Path

# API base URL - updated for server deployment
BASE_URL = "http://multivac:8000"

def test_health():
    """Test the health endpoint."""
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Health check: {response.status_code}")
        print(json.dumps(response.json(), indent=2))
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        print("❌ API server not running. Start with: python api.py")
        return False

def test_root():
    """Test the root endpoint."""
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"Root endpoint: {response.status_code}")
        print(json.dumps(response.json(), indent=2))
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        print("❌ API server not running")
        return False

def test_supported_formats():
    """Test the supported formats endpoint."""
    try:
        response = requests.get(f"{BASE_URL}/supported-formats")
        print(f"Supported formats: {response.status_code}")
        print(json.dumps(response.json(), indent=2))
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        print("❌ API server not running")
        return False

def test_stats():
    """Test the statistics endpoint."""
    try:
        response = requests.get(f"{BASE_URL}/stats")
        print(f"Statistics: {response.status_code}")
        print(json.dumps(response.json(), indent=2))
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        print("❌ API server not running")
        return False

def test_system_info():
    """Test the system info endpoint."""
    try:
        response = requests.get(f"{BASE_URL}/system-info")
        print(f"System info: {response.status_code}")
        print(json.dumps(response.json(), indent=2))
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        print("❌ API server not running")
        return False

def test_process_text():
    """Test text processing endpoint."""
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
        response = requests.post(
            f"{BASE_URL}/process-text",
            json={"text": sample_text, "max_items": 10}
        )
        print(f"Text processing: {response.status_code}")
        print(json.dumps(response.json(), indent=2))
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        print("❌ API server not running")
        return False

def test_process_file():
    """Test file processing endpoint."""
    # Check if sample data exists
    sample_file = Path("data/sample_inventory.xlsx")
    if not sample_file.exists():
        print(f"❌ Sample file not found: {sample_file}")
        return False
    
    try:
        with open(sample_file, 'rb') as f:
            files = {'file': (sample_file.name, f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
            response = requests.post(f"{BASE_URL}/process-file", files=files)
        
        print(f"File processing: {response.status_code}")
        print(json.dumps(response.json(), indent=2))
        return response.status_code == 200
    except requests.exceptions.ConnectionError:
        print("❌ API server not running")
        return False
    except Exception as e:
        print(f"❌ File processing error: {e}")
        return False

def main():
    """Run all API tests."""
    print("🧪 Testing Quotient API...")
    print("=" * 50)
    
    tests = [
        ("Health Check", test_health),
        ("Root Endpoint", test_root),
        ("Supported Formats", test_supported_formats),
        ("Statistics", test_stats),
        ("System Info", test_system_info),
        ("Text Processing", test_process_text),
        ("File Processing", test_process_file),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
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
        print("🎉 All tests passed! API is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above.")

if __name__ == "__main__":
    main() 