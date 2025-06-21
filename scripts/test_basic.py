#!/usr/bin/env python3
"""
Basic tests for the Quotient system.

This script tests the core functionality without requiring external APIs.
"""

import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from quotient.utils.data_models import InventoryItem, ItemStatus, DataSource
from quotient.utils.formatters import format_currency, parse_currency, format_quantity
from quotient.utils.validators import validate_file_type


def test_data_models():
    """Test data model functionality."""
    print("🧪 Testing data models...")
    
    # Test InventoryItem creation
    item = InventoryItem(
        item_name="Test Item",
        part_number="TEST-001",
        quantity=10,
        unit_price=25.50
    )
    
    assert item.item_name == "Test Item"
    assert item.part_number == "TEST-001"
    assert item.quantity == 10
    assert item.unit_price == 25.50
    assert item.total_price == 255.0  # Should be calculated automatically
    
    # Test status
    assert item.status == ItemStatus.PENDING
    
    # Test completeness
    assert item.is_complete() == True
    
    print("✅ Data models test passed")


def test_formatters():
    """Test formatting utilities."""
    print("🧪 Testing formatters...")
    
    # Test currency formatting
    assert format_currency(1234.56) == "$1,234.56"
    assert format_currency("1234.56") == "$1,234.56"
    
    # Test currency parsing
    assert parse_currency("$1,234.56") == 1234.56
    assert parse_currency("1,234.56") == 1234.56
    assert parse_currency("1234.56") == 1234.56
    
    # Test quantity formatting
    assert format_quantity(100, "pcs") == "100 pcs"
    assert format_quantity("100", "units") == "100 units"
    
    print("✅ Formatters test passed")


def test_validators():
    """Test validation utilities."""
    print("🧪 Testing validators...")
    
    # Test file type validation
    is_valid, error_msg = validate_file_type("test.pdf", ["pdf", "txt"])
    assert is_valid == True
    assert error_msg == ""
    
    is_valid, error_msg = validate_file_type("test.xyz", ["pdf", "txt"])
    assert is_valid == False
    assert "Unsupported file type" in error_msg
    
    print("✅ Validators test passed")


def test_enum_values():
    """Test enum values."""
    print("🧪 Testing enum values...")
    
    # Test ItemStatus
    assert ItemStatus.PENDING.value == "pending"
    assert ItemStatus.COMPLETE.value == "complete"
    assert ItemStatus.INCOMPLETE.value == "incomplete"
    assert ItemStatus.ERROR.value == "error"
    
    # Test DataSource
    assert DataSource.PDF.value == "pdf"
    assert DataSource.EMAIL.value == "email"
    assert DataSource.EXCEL.value == "excel"
    assert DataSource.CSV.value == "csv"
    assert DataSource.IMAGE.value == "image"
    assert DataSource.TEXT.value == "text"
    
    print("✅ Enum values test passed")


def main():
    """Run all tests."""
    print("🚀 Running basic tests for Quotient")
    print("=" * 50)
    
    try:
        test_data_models()
        test_formatters()
        test_validators()
        test_enum_values()
        
        print("\n✅ All basic tests passed!")
        print("\n🎯 The core system is working correctly.")
        print("   You can now proceed to test with real data and APIs.")
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 