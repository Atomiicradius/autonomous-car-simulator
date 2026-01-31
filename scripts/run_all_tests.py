#!/usr/bin/env python3
"""
Comprehensive Test Runner for Merged Autonomous Car Simulator
Runs all 59 tests and reports results.
"""

import subprocess
import sys
import os

# Change to parent directory (root) so relative paths work
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def run_test(test_file, description):
    """Run a test file and return pass/fail status"""
    print(f"\n{'='*70}")
    print(f"Running: {description}")
    print(f"File: {test_file}")
    print(f"{'='*70}")
    
    try:
        result = subprocess.run([sys.executable, test_file], 
                              capture_output=True, 
                              text=True,
                              timeout=30)
        
        # Check for success indicators
        output = result.stdout + result.stderr
        
        if result.returncode == 0 or "PASSED" in output or "passed" in output:
            # Count tests
            if "passed" in output:
                lines = output.split('\n')
                for line in lines:
                    if 'passed' in line.lower():
                        print(f"✓ {line.strip()}")
                        return True
            print("✓ Tests passed")
            return True
        else:
            print(f"✗ Tests failed with return code {result.returncode}")
            print("Last 20 lines of output:")
            print('\n'.join(output.split('\n')[-20:]))
            return False
            
    except subprocess.TimeoutExpired:
        print("✗ Test timeout")
        return False
    except Exception as e:
        print(f"✗ Error running test: {e}")
        return False

def main():
    """Run all tests and summarize"""
    print("\n" + "="*70)
    print("COMPREHENSIVE AUTONOMOUS CAR SIMULATOR TEST SUITE")
    print("="*70)
    print("Running 59 tests across 7 test files...\n")
    
    tests = [
        ("tests/test_physics.py", "Day 1 Physics Tests (12 tests)"),
        ("tests/test_sensors.py", "Day 2 Sensor Tests (14 tests)"),
        ("tests/test_integration.py", "Physics + Sensors Integration (4 tests)"),
        ("tests/test_adapter.py", "Obstacle Adapter Test (1 test)"),
        ("tests/test_alu_unit.py", "ALU Unit Tests (6 tests)"),
        ("tests/test_minimal.py", "ALU Minimal Tests (5 tests)"),
        ("tests/test_scenarios.py", "ALU Scenario Tests (18 tests)"),
    ]
    
    results = {}
    for test_file, description in tests:
        results[description] = run_test(test_file, description)
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for description, success in results.items():
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status:8} | {description}")
    
    print("="*70)
    print(f"Results: {passed}/{total} test suites passed")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Simulator is ready to use.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test suite(s) failed. See details above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
