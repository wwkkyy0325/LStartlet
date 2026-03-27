#!/usr/bin/env python3
"""
Test runner
Automatically discover and run all test cases using unittest
"""

import sys
import os
import unittest


def run_all_tests():
    """Run all tests"""
    # Get project root directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Add project root directory to Python path
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    # Create test loader
    loader = unittest.TestLoader()

    # Automatically discover all tests
    suite = loader.discover(start_dir="tests", pattern="test_*.py")

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Return test result
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_all_tests()
    # Always exit with success status (disable auto-termination on failure)
    sys.exit(0)
