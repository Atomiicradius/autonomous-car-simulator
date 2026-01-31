"""
Simple Unit Tests for ALU Decision Logic
Author: ALU Engineer (Person 2)

Quick validation tests without scenario simulations.
"""

import sys
import os

# Add src and config folders to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'config'))

from alu_decision import ALUDecisionEngine, VehicleState
from config import DRIVING_MODES


def test_fsm_transitions():
    """Test FSM state transitions"""
    print("\n" + "="*60)
    print("TEST: FSM State Transitions")
    print("="*60)
    
    alu = ALUDecisionEngine(mode='normal')
    
    # Test 1: Clear path -> CRUISE
    sensors = {'FL': 10.0, 'FR': 10.0, 'BL': 10.0, 'BR': 10.0}
    state = alu.determine_next_state(sensors, current_speed=2.0)
    print(f"✓ Clear sensors -> {state} (expected: CRUISE)")
    assert state == VehicleState.CRUISE
    
    # Test 2: Both front blocked -> EMERGENCY_BRAKE
    sensors = {'FL': 1.0, 'FR': 1.0, 'BL': 10.0, 'BR': 10.0}
    state = alu.determine_next_state(sensors, current_speed=2.0)
    print(f"✓ Both front blocked -> {state} (expected: EMERGENCY_BRAKE)")
    assert state == VehicleState.EMERGENCY_BRAKE
    
    # Test 3: Left blocked -> AVOID_RIGHT
    sensors = {'FL': 1.0, 'FR': 10.0, 'BL': 10.0, 'BR': 10.0}
    state = alu.determine_next_state(sensors, current_speed=2.0)
    print(f"✓ Left blocked -> {state} (expected: AVOID_RIGHT)")
    assert state == VehicleState.AVOID_RIGHT
    
    # Test 4: Right blocked -> AVOID_LEFT
    sensors = {'FL': 10.0, 'FR': 1.0, 'BL': 10.0, 'BR': 10.0}
    state = alu.determine_next_state(sensors, current_speed=2.0)
    print(f"✓ Right blocked -> {state} (expected: AVOID_LEFT)")
    assert state == VehicleState.AVOID_LEFT
    
    print("\nAll FSM tests passed! ✓")


def test_ttc_prediction():
    """Test Time-To-Collision prediction"""
    print("\n" + "="*60)
    print("TEST: TTC Prediction")
    print("="*60)
    
    alu = ALUDecisionEngine(mode='normal')
    
    # Test 1: High speed, moderate distance -> Emergency brake
    sensors = {'FL': 3.0, 'FR': 3.0, 'BL': 10.0, 'BR': 10.0}
    state = alu.determine_next_state(sensors, current_speed=5.0)
    ttc = alu.ttc
    print(f"✓ High speed (5 m/s), distance 3m -> TTC={ttc:.2f}s, State={state}")
    assert state == VehicleState.EMERGENCY_BRAKE  # TTC = 0.6s < 2.0s threshold
    
    # Test 2: Zero speed -> TTC infinite
    sensors = {'FL': 1.0, 'FR': 1.0, 'BL': 10.0, 'BR': 10.0}
    state = alu.determine_next_state(sensors, current_speed=0.0)
    ttc = alu.ttc
    print(f"✓ Zero speed -> TTC={ttc} (expected: inf)")
    assert ttc == float('inf')
    
    print("\nAll TTC tests passed! ✓")


def test_hazard_score():
    """Test hazard score calculation"""
    print("\n" + "="*60)
    print("TEST: Hazard Score Calculation")
    print("="*60)
    
    alu = ALUDecisionEngine(mode='normal')
    
    # Test 1: All clear -> Hazard = 0.0
    sensors = {'FL': 10.0, 'FR': 10.0, 'BL': 10.0, 'BR': 10.0}
    hazard = alu.calculate_hazard_score(sensors)
    print(f"✓ All clear -> Hazard={hazard:.2f} (expected: 0.00)")
    assert hazard == 0.0
    
    # Test 2: Critical danger -> Hazard = 1.0
    sensors = {'FL': 0.5, 'FR': 10.0, 'BL': 10.0, 'BR': 10.0}
    hazard = alu.calculate_hazard_score(sensors)
    print(f"✓ Critical danger -> Hazard={hazard:.2f} (expected: 1.00)")
    assert hazard == 1.0
    
    # Test 3: Warning zone -> 0.0 < Hazard < 1.0
    sensors = {'FL': 2.5, 'FR': 10.0, 'BL': 10.0, 'BR': 10.0}
    hazard = alu.calculate_hazard_score(sensors)
    print(f"✓ Warning zone -> Hazard={hazard:.2f} (range: 0.0-1.0)")
    assert 0.0 < hazard < 1.0
    
    print("\nAll hazard tests passed! ✓")


def test_mode_differences():
    """Test mode behavioral differences"""
    print("\n" + "="*60)
    print("TEST: Mode Behavioral Differences")
    print("="*60)
    
    sensors = {'FL': 2.5, 'FR': 2.5, 'BL': 10.0, 'BR': 10.0}
    
    alu_cautious = ALUDecisionEngine(mode='cautious')
    alu_aggressive = ALUDecisionEngine(mode='aggressive')
    
    hazard_cautious = alu_cautious.calculate_hazard_score(sensors)
    hazard_aggressive = alu_aggressive.calculate_hazard_score(sensors)
    
    print(f"✓ Cautious hazard: {hazard_cautious:.3f}")
    print(f"✓ Aggressive hazard: {hazard_aggressive:.3f}")
    print(f"✓ Cautious perceives higher danger: {hazard_cautious > hazard_aggressive}")
    
    assert hazard_cautious > hazard_aggressive
    
    # Check thresholds
    assert DRIVING_MODES['cautious']['ttc_threshold'] > DRIVING_MODES['aggressive']['ttc_threshold']
    assert DRIVING_MODES['cautious']['max_speed'] < DRIVING_MODES['aggressive']['max_speed']
    
    print("\nAll mode comparison tests passed! ✓")


def test_hysteresis():
    """Test hysteresis mechanism"""
    print("\n" + "="*60)
    print("TEST: Hysteresis Mechanism")
    print("="*60)
    
    alu = ALUDecisionEngine(mode='normal')
    sensors = {'FL': 1.5, 'FR': 10.0, 'BL': 10.0, 'BR': 10.0}
    
    initial_state = alu.current_state
    print(f"Initial state: {initial_state}")
    
    # Update N-1 times (should not change state yet)
    hysteresis_cycles = DRIVING_MODES['normal']['hysteresis_cycles']
    for i in range(hysteresis_cycles - 1):
        alu.update_state(sensors, current_speed=2.0)
    
    print(f"✓ After {hysteresis_cycles-1} cycles: State={alu.current_state} (unchanged)")
    assert alu.current_state == initial_state
    
    # One more update should trigger transition
    alu.update_state(sensors, current_speed=2.0)
    print(f"✓ After {hysteresis_cycles} cycles: State={alu.current_state} (changed)")
    assert alu.current_state != initial_state
    
    print("\nHysteresis test passed! ✓")


def main():
    """Run all unit tests"""
    print("\n" + "#"*60)
    print("# ALU DECISION LOGIC - UNIT TESTS")
    print("#"*60)
    
    try:
        test_fsm_transitions()
        test_ttc_prediction()
        test_hazard_score()
        test_mode_differences()
        test_hysteresis()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        return 0
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
