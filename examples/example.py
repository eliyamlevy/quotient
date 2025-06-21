#!/usr/bin/env python3
"""
Example usage of the Quotient AI-powered inventory management system.

This script demonstrates how to use the three-layer architecture to process
various types of documents and extract inventory information.
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from quotient.core import QuotientPipeline, QuotientConfig


def main():
    """Main example function."""
    print("🚀 Quotient - AI-Powered Inventory Management System")
    print("=" * 60)
    
    try:
        # Initialize the pipeline
        print("📋 Initializing Quotient pipeline...")
        config = QuotientConfig.from_yaml()
        pipeline = QuotientPipeline(config)
        print("✅ Pipeline initialized successfully")
        
        # Check if a file was provided as command line argument
        if len(sys.argv) > 1:
            file_path = Path(sys.argv[1])
            if file_path.exists():
                print(f"\n📄 Processing file: {file_path}")
                print("-" * 40)
                
                result = pipeline.process_single_document(file_path)
                
                # Display results
                print(f"📊 Processing Results:")
                print(f"   - Items extracted: {len(result.items)}")
                print(f"   - Processing time: {result.processing_time:.2f} seconds")
                print(f"   - Confidence: {result.extraction_confidence:.2f}")
                
                if result.items:
                    print(f"\n📦 Extracted Items:")
                    for i, item in enumerate(result.items, 1):
                        print(f"   {i}. {item.item_name}")
                        print(f"      Part #: {item.part_number or 'N/A'}")
                        print(f"      Quantity: {item.quantity or 'N/A'}")
                        print(f"      Unit Price: ${item.unit_price or 'N/A'}")
                        print(f"      Vendor: {item.vendor_name or 'N/A'}")
                        print(f"      Status: {item.status.value}")
                        print()
                else:
                    print("❌ No items extracted from the file")
                
                return
            else:
                print(f"❌ File not found: {file_path}")
                return
        
        # Example 1: Process a text file with inventory data
        print("\n📄 Example 1: Processing text file")
        print("-" * 40)
        
        # Create a sample text file
        sample_text = """
        INVENTORY QUOTE
        
        Item: Laptop Computer
        Part #: LAP-001
        Quantity: 5
        Unit Price: $1,200.00
        Total: $6,000.00
        Vendor: Tech Solutions Inc.
        
        Item: Wireless Mouse
        Part #: MOUSE-002
        Quantity: 10
        Unit Price: $25.50
        Total: $255.00
        Vendor: Tech Solutions Inc.
        
        Item: USB Cable
        Part #: CABLE-003
        Quantity: 20
        Unit Price: $5.00
        Total: $100.00
        Vendor: Cable Co.
        """
        
        # Write sample text to file
        sample_file = Path("sample_inventory.txt")
        with open(sample_file, "w") as f:
            f.write(sample_text)
        
        # Process the file
        result = pipeline.process_single_document(sample_file)
        
        # Display results
        print(f"📊 Processing Results:")
        print(f"   - Items extracted: {len(result.items)}")
        print(f"   - Processing time: {result.processing_time:.2f} seconds")
        print(f"   - Confidence: {result.extraction_confidence:.2f}")
        
        if result.items:
            print(f"\n📦 Extracted Items:")
            for i, item in enumerate(result.items, 1):
                print(f"   {i}. {item.item_name}")
                print(f"      Part #: {item.part_number or 'N/A'}")
                print(f"      Quantity: {item.quantity or 'N/A'}")
                print(f"      Unit Price: ${item.unit_price or 'N/A'}")
                print(f"      Vendor: {item.vendor_name or 'N/A'}")
                print(f"      Status: {item.status.value}")
                print()
        
        # Example 2: Get processing status
        print("\n📈 Example 2: Processing Status")
        print("-" * 40)
        
        status = pipeline.get_processing_status()
        print(f"📊 Pipeline Status:")
        for key, value in status.items():
            if isinstance(value, dict):
                print(f"   - {key}:")
                for sub_key, sub_value in value.items():
                    print(f"     {sub_key}: {sub_value}")
            else:
                print(f"   - {key}: {value}")
        
        # Example 3: Validate a document
        print("\n🔍 Example 3: Document Validation")
        print("-" * 40)
        
        validation = pipeline.validate_document(sample_file)
        print(f"📄 Validation Results:")
        for key, value in validation.items():
            print(f"   - {key}: {value}")
        
        # Clean up
        if sample_file.exists():
            sample_file.unlink()
        
        print("\n✅ Examples completed successfully!")
        print("\n🎯 Next Steps:")
        print("   - Try processing your own PDF, Excel, or image files")
        print("   - Configure web search agents in Layer 2")
        print("   - Set up vector database for historical learning")
        print("   - Build custom extractors for your specific use case")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        print("\n🔧 Troubleshooting:")
        print("   - Ensure all dependencies are installed")
        print("   - Check the logs for more details")


if __name__ == "__main__":
    main() 