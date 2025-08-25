#!/usr/bin/env python3
"""
Test runner for EmailDiffusionPipeline

Provides options to run different test categories and generate coverage reports.
"""

import sys
import os
import argparse
import subprocess
from pathlib import Path

def run_tests(test_pattern: str = None, verbose: bool = False, coverage: bool = False):
    """Run tests with specified options"""
    
    # Base command
    cmd = [sys.executable, "-m", "pytest"]
    
    # Add test file
    test_file = "test_diffusion_pipeline.py"
    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        return False
    
    cmd.append(test_file)
    
    # Add test pattern if specified
    if test_pattern:
        cmd.extend(["-k", test_pattern])
    
    # Add verbose flag
    if verbose:
        cmd.append("-v")
    
    # Add coverage if requested
    if coverage:
        cmd.extend(["--cov=email_diffusion_pipeline", "--cov-report=html", "--cov-report=term"])
    
    # Run the tests
    print(f"🚀 Running tests with command: {' '.join(cmd)}")
    print("=" * 60)
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print("\n✅ All tests passed!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Tests failed with exit code: {e.returncode}")
        return False

def run_specific_test_category(category: str, verbose: bool = False):
    """Run tests for a specific category"""
    
    category_patterns = {
        'dataclasses': 'TestImageTextResult or TestQuoteLevelInfo or TestItemMetadata or TestProcessedQuote',
        'pipeline': 'TestEmailDiffusionPipeline',
        'integration': 'TestEmailDiffusionPipelineIntegration',
        'edge_cases': 'TestEmailDiffusionPipelineEdgeCases',
        'filters': 'test_convert_images_to_text or test_extract_quote_level_info or test_extract_item_metadata',
        'utils': 'test_extract_table_structure or test_combine_text_and_images or test_clean_json_string'
    }
    
    if category not in category_patterns:
        print(f"❌ Unknown test category: {category}")
        print(f"Available categories: {', '.join(category_patterns.keys())}")
        return False
    
    pattern = category_patterns[category]
    print(f"🎯 Running tests for category: {category}")
    print(f"📋 Pattern: {pattern}")
    
    return run_tests(test_pattern=pattern, verbose=verbose)

def run_unit_tests(verbose: bool = False):
    """Run all unit tests"""
    print("🧪 Running all unit tests...")
    return run_tests(verbose=verbose)

def run_integration_tests(verbose: bool = False):
    """Run integration tests"""
    print("🔗 Running integration tests...")
    return run_tests(test_pattern="TestEmailDiffusionPipelineIntegration", verbose=verbose)

def run_coverage_tests(verbose: bool = False):
    """Run tests with coverage reporting"""
    print("📊 Running tests with coverage...")
    return run_tests(verbose=verbose, coverage=True)

def list_test_categories():
    """List all available test categories"""
    categories = {
        'dataclasses': 'Test dataclass creation and validation',
        'pipeline': 'Test pipeline initialization and flow',
        'integration': 'Test full pipeline integration',
        'edge_cases': 'Test error handling and edge cases',
        'filters': 'Test individual pipeline filters',
        'utils': 'Test utility methods'
    }
    
    print("📋 Available test categories:")
    print("=" * 40)
    for category, description in categories.items():
        print(f"  {category:15} - {description}")
    print()

def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(
        description="Test runner for EmailDiffusionPipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py                    # Run all tests
  python run_tests.py --category pipeline    # Run pipeline tests only
  python run_tests.py --verbose             # Run with verbose output
  python run_tests.py --coverage            # Run with coverage report
  python run_tests.py --list               # List test categories
        """
    )
    
    parser.add_argument(
        '--category', '-c',
        choices=['dataclasses', 'pipeline', 'integration', 'edge_cases', 'filters', 'utils'],
        help='Run tests for specific category'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Run tests with verbose output'
    )
    
    parser.add_argument(
        '--coverage', '--cov',
        action='store_true',
        help='Run tests with coverage reporting'
    )
    
    parser.add_argument(
        '--list', '-l',
        action='store_true',
        help='List available test categories'
    )
    
    parser.add_argument(
        '--pattern', '-k',
        help='Run tests matching pattern (pytest -k option)'
    )
    
    args = parser.parse_args()
    
    # List categories if requested
    if args.list:
        list_test_categories()
        return
    
    # Check if we're in the right directory
    if not os.path.exists("test_diffusion_pipeline.py"):
        print("❌ Error: test_diffusion_pipeline.py not found in current directory")
        print("Please run this script from the noam/ directory")
        return 1
    
    # Run tests based on arguments
    success = False
    
    if args.category:
        success = run_specific_test_category(args.category, args.verbose)
    elif args.pattern:
        success = run_tests(test_pattern=args.pattern, verbose=args.verbose)
    elif args.coverage:
        success = run_coverage_tests(args.verbose)
    else:
        success = run_unit_tests(args.verbose)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())

