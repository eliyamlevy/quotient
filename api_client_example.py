#!/usr/bin/env python3
"""Example client for the Quotient API."""

import requests
import json
from pathlib import Path

class QuotientAPIClient:
    """Client for the Quotient API."""
    
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def health_check(self):
        """Check API health."""
        response = requests.get(f"{self.base_url}/health")
        return response.json()
    
    def get_supported_formats(self):
        """Get supported file formats."""
        response = requests.get(f"{self.base_url}/supported-formats")
        return response.json()
    
    def process_text(self, text, max_items=50):
        """Process text and extract inventory items."""
        response = requests.post(
            f"{self.base_url}/process-text",
            json={"text": text, "max_items": max_items}
        )
        return response.json()
    
    def process_file(self, file_path, max_items=50):
        """Process a file and extract inventory items."""
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(file_path, 'rb') as f:
            files = {'file': (file_path.name, f, 'application/octet-stream')}
            response = requests.post(
                f"{self.base_url}/process-file",
                files=files,
                params={"max_items": max_items}
            )
        return response.json()

def main():
    """Example usage of the Quotient API client."""
    client = QuotientAPIClient()
    
    print("🔍 Quotient API Client Example")
    print("=" * 40)
    
    # Health check
    print("\n1. Health Check:")
    try:
        health = client.health_check()
        print(f"✅ API Status: {health['status']}")
        print(f"Pipeline Ready: {health['pipeline_ready']}")
    except requests.exceptions.ConnectionError:
        print("❌ API server not running. Start with: ./start_api.sh")
        return
    
    # Supported formats
    print("\n2. Supported Formats:")
    formats = client.get_supported_formats()
    for fmt in formats['supported_formats']:
        print(f"  - {fmt['extension']}: {fmt['type']}")
    
    # Process text
    print("\n3. Text Processing Example:")
    sample_text = """
    INVENTORY REPORT - Q1 2024
    
    ITEM: Dell Latitude 5520 Laptop
    QUANTITY: 15 units
    PRICE: $1,199.99 each
    CATEGORY: Electronics
    VENDOR: Dell Inc.
    PART#: DL-5520-15
    
    ITEM: Herman Miller Aeron Chair
    QUANTITY: 8 units
    PRICE: $1,295.00 each
    CATEGORY: Office Furniture
    VENDOR: Herman Miller
    PART#: HM-AERON-8
    
    ITEM: HP LaserJet Pro M404n
    QUANTITY: 3 units
    PRICE: $299.99 each
    CATEGORY: Office Equipment
    VENDOR: HP Inc.
    PART#: HP-M404N-3
    """
    
    try:
        result = client.process_text(sample_text, max_items=10)
        print(f"✅ Extracted {result['items_extracted']} items:")
        for item in result['items']:
            print(f"  - {item['item_name']}: {item['quantity']} @ ${item['unit_price']}")
    except Exception as e:
        print(f"❌ Text processing failed: {e}")
    
    # Process file
    print("\n4. File Processing Example:")
    sample_file = Path("data/sample_inventory.xlsx")
    if sample_file.exists():
        try:
            result = client.process_file(sample_file, max_items=10)
            print(f"✅ Extracted {result['items_extracted']} items from {result['filename']}:")
            for item in result['items']:
                print(f"  - {item['item_name']}: {item['quantity']} @ ${item['unit_price']}")
        except Exception as e:
            print(f"❌ File processing failed: {e}")
    else:
        print(f"⚠️  Sample file not found: {sample_file}")
        print("   Run the data generation script first to create sample files.")

if __name__ == "__main__":
    main() 