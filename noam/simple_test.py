#!/usr/bin/env python3
"""
Simple test runner for EmailDiffusionPipeline using standard unittest

This file can run without installing pytest or other dependencies.
"""

import unittest
import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

def run_simple_tests():
    """Run tests using standard unittest module"""
    
    # Import test modules
    try:
        from test_diffusion_pipeline import (
            TestImageTextResult,
            TestQuoteLevelInfo,
            TestItemMetadata,
            TestProcessedQuote,
            TestEmailDiffusionPipeline,
            TestEmailDiffusionPipelineIntegration,
            TestEmailDiffusionPipelineEdgeCases
        )
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure all test files are in the same directory")
        return False
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestImageTextResult,
        TestQuoteLevelInfo,
        TestItemMetadata,
        TestProcessedQuote,
        TestEmailDiffusionPipeline,
        TestEmailDiffusionPipelineIntegration,
        TestEmailDiffusionPipelineEdgeCases
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    print("🧪 Running EmailDiffusionPipeline tests...")
    print("=" * 50)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print(f"  Tests run: {result.testsRun}")
    print(f"  Failures: {len(result.failures)}")
    print(f"  Errors: {len(result.errors)}")
    
    if result.failures:
        print("\n❌ Failures:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print("\n💥 Errors:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split('Exception:')[-1].strip()}")
    
    if result.wasSuccessful():
        print("\n✅ All tests passed!")
        return True
    else:
        print("\n❌ Some tests failed!")
        return False

def run_quick_tests():
    """Run a quick subset of tests"""
    print("🚀 Running quick tests...")
    
    # Test dataclasses only
    try:
        from test_diffusion_pipeline import (
            TestImageTextResult,
            TestQuoteLevelInfo,
            TestItemMetadata,
            TestProcessedQuote
        )
        
        test_suite = unittest.TestSuite()
        test_classes = [
            TestImageTextResult,
            TestQuoteLevelInfo,
            TestItemMetadata,
            TestProcessedQuote
        ]
        
        for test_class in test_classes:
            tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
            test_suite.addTests(tests)
        
        runner = unittest.TextTestRunner(verbosity=1)
        result = runner.run(test_suite)
        
        return result.wasSuccessful()
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def main():
    """Main function"""
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        success = run_quick_tests()
    else:
        success = run_simple_tests()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())

