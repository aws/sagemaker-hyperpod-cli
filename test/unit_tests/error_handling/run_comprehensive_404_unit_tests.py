"""
Comprehensive test runner for all 404 error handling unit tests.
Executes all unit tests for the enhanced 404 error handling system.
"""

import pytest
import sys
import os
from pathlib import Path

def main():
    """Run all 404 error handling unit tests."""
    
    print("🧪 Running Comprehensive 404 Error Handling Unit Tests")
    print("=" * 60)
    
    # Change to project root directory for pytest to find setup.cfg
    current_dir = Path(__file__).parent
    project_root = current_dir.parent.parent.parent
    os.chdir(project_root)
    
    # Test files to run (relative to project root)
    test_files = [
        "test/unit_tests/error_handling/test_error_constants.py",
        "test/unit_tests/error_handling/test_error_context.py", 
        "test/unit_tests/error_handling/test_not_found_handler.py",
        "test/unit_tests/error_handling/test_cli_decorators.py",
        "test/unit_tests/error_handling/test_utils_404_handling.py"
    ]
    
    # Check that all test files exist
    missing_files = []
    for test_file in test_files:
        if not Path(test_file).exists():
            missing_files.append(test_file)
    
    if missing_files:
        print(f"❌ Missing test files:")
        for file in missing_files:
            print(f"   - {file}")
        return 1
    
    print(f"✅ Found all {len(test_files)} test files")
    print()
    
    # Run pytest with comprehensive options
    pytest_args = [
        "-v",  # Verbose output
        "--tb=short",  # Short traceback format
        "--strict-markers",  # Strict marker handling
        "--disable-warnings",  # Disable warnings for cleaner output
        "-x",  # Stop on first failure for debugging
        "--color=yes",  # Colored output
    ]
    
    # Add test files
    pytest_args.extend(test_files)
    
    print("🚀 Executing pytest with arguments:")
    print(f"   {' '.join(pytest_args)}")
    print()
    
    # Run the tests
    exit_code = pytest.main(pytest_args)
    
    # Summary
    print()
    print("=" * 60)
    if exit_code == 0:
        print("🎉 All 404 Error Handling Unit Tests PASSED!")
        print()
        print("📊 Test Coverage Summary:")
        print("   ✅ Error Constants (enums, mappings)")
        print("   ✅ Error Context (dataclass, context gathering)")
        print("   ✅ Not Found Handler (message generation, main handler)")
        print("   ✅ CLI Decorators (smart handler, auto-detection)")
        print("   ✅ Utils 404 Handling (handle_404, handle_exception)")
        print()
        print("🔧 Components Tested:")
        print("   • ResourceType and OperationType enums")
        print("   • RESOURCE_LIST_COMMANDS and RESOURCE_DISPLAY_NAMES")
        print("   • ErrorContext dataclass functionality")
        print("   • ContextGatherer with timeout protection")
        print("   • NotFoundMessageGenerator message templates")
        print("   • NotFoundHandler main coordination")
        print("   • Smart CLI exception handler with auto-detection")
        print("   • Legacy exception handling compatibility")
        print("   • Integration scenarios for all resource types")
        print()
        print("🎯 All 404 error handling components are fully tested!")
    else:
        print("❌ Some tests FAILED!")
        print("   Check the output above for details.")
        print("   Fix the failing tests and run again.")
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
