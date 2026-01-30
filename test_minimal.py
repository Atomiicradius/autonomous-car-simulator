"""
SUPER MINIMAL TEST - No pygame, no backend imports
Tests ONLY the core ALU logic
"""

import sys

# Test imports one by one
print("Testing imports...")
try:
    from config import VehicleState, DRIVING_MODES
    print("✓ config imported")
except Exception as e:
    print(f"✗ config failed: {e}")
    sys.exit(1)

try:
    from alu_decision import ALUDecisionEngine
    print("✓ alu_decision imported")
except Exception as e:
    print(f"✗ alu_decision failed: {e}")
    sys.exit(1)

print("\n" + "="*50)
print("CORE ALU LOGIC TESTS")
print("="*50)

# Test 1
print("\n1. Testing FSM - Clear path")
alu = ALUDecisionEngine(mode='normal')
sensors = {'FL': 10.0, 'FR': 10.0, 'BL': 10.0, 'BR': 10.0}
state = alu.determine_next_state(sensors, current_speed=2.0)
result = "PASS" if state == VehicleState.CRUISE else "FAIL"
print(f"   Result: {state} [{result}]")

# Test 2
print("\n2. Testing FSM - Front blocked")
sensors = {'FL': 1.0, 'FR': 1.0, 'BL': 10.0, 'BR': 10.0}
state = alu.determine_next_state(sensors, current_speed=2.0)
result = "PASS" if state == VehicleState.EMERGENCY_BRAKE else "FAIL"
print(f"   Result: {state} [{result}]")

# Test 3
print("\n3. Testing Hazard Score")
sensors = {'FL': 0.5, 'FR': 10.0, 'BL': 10.0, 'BR': 10.0}
hazard = alu.calculate_hazard_score(sensors)
result = "PASS" if hazard == 1.0 else "FAIL"
print(f"   Result: Hazard={hazard:.2f} [{result}]")

# Test 4
print("\n4. Testing TTC Prediction")
sensors = {'FL': 2.0, 'FR': 2.0, 'BL': 10.0, 'BR': 10.0}
state = alu.determine_next_state(sensors, current_speed=10.0)
ttc = alu.ttc
result = "PASS" if state == VehicleState.EMERGENCY_BRAKE else "FAIL"
print(f"   Result: TTC={ttc:.2f}s, State={state} [{result}]")

# Test 5
print("\n5. Testing Mode Differences")
alu_cautious = ALUDecisionEngine(mode='cautious')
alu_aggressive = ALUDecisionEngine(mode='aggressive')
sensors = {'FL': 2.5, 'FR': 2.5, 'BL': 10.0, 'BR': 10.0}
h1 = alu_cautious.calculate_hazard_score(sensors)
h2 = alu_aggressive.calculate_hazard_score(sensors)
result = "PASS" if h1 > h2 else "FAIL"
print(f"   Cautious: {h1:.3f}, Aggressive: {h2:.3f} [{result}]")

print("\n" + "="*50)
print("✅ BASIC ALU TESTS COMPLETE")
print("="*50)
print("\nNOTE: Full integration tests require pygame")
print("Run 'python visualizer.py' to see live demo")
