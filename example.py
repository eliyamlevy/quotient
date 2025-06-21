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
    
    # Check if OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY environment variable is required")
        print("Please set your OpenAI API key:")
        print("export OPENAI_API_KEY='your-api-key-here'")
        return
    
    try:
        # Initialize the pipeline
        print("📋 Initializing Quotient pipeline...")
        pipeline = QuotientPipeline()
        print("✅ Pipeline initialized successfully")
        
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
        result = pipeline.process_document(sample_file)
        
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
        
        # Example 2: Process email content
        print("\n📧 Example 2: Processing email content")
        print("-" * 40)
        
        sample_email = """
        From: vendor@example.com
        To: buyer@company.com
        Subject: Quote for Office Supplies
        
        Dear Buyer,
        
        Please find our quote for the requested office supplies:
        
        - 50 reams of printer paper (A4, 80gsm) at $8.50 per ream
        - 20 boxes of pens (black, ballpoint) at $12.00 per box
        - 10 desk organizers at $45.00 each
        
        Total: $1,370.00
        
        Best regards,
        Office Supply Co.
        """
        
        email_result = pipeline.process_email(sample_email)
        
        print(f"📊 Email Processing Results:")
        print(f"   - Items extracted: {len(email_result.items)}")
        print(f"   - Processing time: {email_result.processing_time:.2f} seconds")
        
        if email_result.items:
            print(f"\n📦 Extracted Items from Email:")
            for i, item in enumerate(email_result.items, 1):
                print(f"   {i}. {item.item_name}")
                print(f"      Quantity: {item.quantity or 'N/A'}")
                print(f"      Unit Price: ${item.unit_price or 'N/A'}")
                print()
        
        # Example 3: Get processing statistics
        print("\n📈 Example 3: Processing Statistics")
        print("-" * 40)
        
        stats = pipeline.get_processing_stats()
        print(f"📊 Overall Statistics:")
        for key, value in stats.items():
            print(f"   - {key}: {value}")
        
        # Example 4: Export data
        print("\n💾 Example 4: Exporting Data")
        print("-" * 40)
        
        # Export to CSV
        csv_path = pipeline.export_data("csv", "inventory_export.csv")
        print(f"📄 Data exported to: {csv_path}")
        
        # Export to DataFrame
        df = pipeline.export_data("dataframe")
        print(f"📊 DataFrame shape: {df.shape}")
        
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
        print("   - Check your OpenAI API key is valid")
        print("   - Ensure all dependencies are installed")
        print("   - Check the logs for more details")


if __name__ == "__main__":
    main() 