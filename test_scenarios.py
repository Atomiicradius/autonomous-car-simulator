"""
Testing Framework for ALU Decision Logic
Author: ALU Engineer (Person 2)

Comprehensive test suite including:
- Dummy sensor tests
- Edge case validation
- Scenario-based testing
- Mode comparison
"""

import sys
from alu_decision import ALUDecisionEngine, VehicleState
from backend import AutonomousVehicleController
from config import DRIVING_MODES


class ALUTestSuite:
    """Test suite for ALU decision logic"""
    
    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0
    
    def assert_test(self, condition, test_name):
        """Assert a test condition"""
        if condition:
            print(f"✓ PASS: {test_name}")
            self.tests_passed += 1
        else:
            print(f"✗ FAIL: {test_name}")
            self.tests_failed += 1
    
    def test_dummy_sensors(self):
        """Test ALU with dummy sensor values"""
        print("\n" + "="*60)
        print("TEST CATEGORY: Dummy Sensor Tests")
        print("="*60)
        
        alu = ALUDecisionEngine(mode='normal')
        
        # Test 1: All sensors clear - should CRUISE
        sensors = {'FL': 10.0, 'FR': 10.0, 'BL': 10.0, 'BR': 10.0}
        state = alu.determine_next_state(sensors, current_speed=2.0)
        self.assert_test(state == VehicleState.CRUISE, 
                        "Clear sensors → CRUISE state")
        
        # Test 2: Front obstacle - should avoid or brake
        sensors = {'FL': 1.0, 'FR': 1.0, 'BL': 10.0, 'BR': 10.0}
        state = alu.determine_next_state(sensors, current_speed=2.0)
        self.assert_test(state == VehicleState.EMERGENCY_BRAKE,
                        "Both front sensors blocked → EMERGENCY_BRAKE")
        
        # Test 3: Left obstacle only - should avoid right
        sensors = {'FL': 1.0, 'FR': 10.0, 'BL': 10.0, 'BR': 10.0}
        state = alu.determine_next_state(sensors, current_speed=2.0)
        self.assert_test(state == VehicleState.AVOID_RIGHT,
                        "Left obstacle → AVOID_RIGHT")
        
        # Test 4: Right obstacle only - should avoid left
        sensors = {'FL': 10.0, 'FR': 1.0, 'BL': 10.0, 'BR': 10.0}
        state = alu.determine_next_state(sensors, current_speed=2.0)
        self.assert_test(state == VehicleState.AVOID_LEFT,
                        "Right obstacle → AVOID_LEFT")
        
        # Test 5: TTC trigger
        sensors = {'FL': 3.0, 'FR': 3.0, 'BL': 10.0, 'BR': 10.0}
        state = alu.determine_next_state(sensors, current_speed=5.0)  # High speed
        ttc = 3.0 / 5.0  # = 0.6s
        self.assert_test(state == VehicleState.EMERGENCY_BRAKE,
                        "Low TTC → EMERGENCY_BRAKE (predictive)")
    
    def test_edge_cases(self):
        """Test edge cases and boundary conditions"""
        print("\n" + "="*60)
        print("TEST CATEGORY: Edge Case Tests")
        print("="*60)
        
        alu = ALUDecisionEngine(mode='normal')
        
        # Edge 1: No obstacles (all max range)
        sensors = {'FL': 10.0, 'FR': 10.0, 'BL': 10.0, 'BR': 10.0}
        state = alu.determine_next_state(sensors, current_speed=2.0)
        self.assert_test(state == VehicleState.CRUISE,
                        "No obstacles → CRUISE")
        
        # Edge 2: Fully blocked vehicle
        sensors = {'FL': 0.5, 'FR': 0.5, 'BL': 0.5, 'BR': 0.5}
        alu.current_state = VehicleState.EMERGENCY_BRAKE
        state = alu.determine_next_state(sensors, current_speed=0.0)  # Stopped
        self.assert_test(state == VehicleState.REVERSING,
                        "Fully blocked + stopped → REVERSING")
        
        # Edge 3: Zero speed (no TTC trigger)
        sensors = {'FL': 1.0, 'FR': 1.0, 'BL': 10.0, 'BR': 10.0}
        state = alu.determine_next_state(sensors, current_speed=0.0)
        ttc = alu.ttc
        self.assert_test(ttc == float('inf'),
                        "Zero speed → TTC = infinity")
        
        # Edge 4: Hazard score calculation
        sensors_safe = {'FL': 10.0, 'FR': 10.0, 'BL': 10.0, 'BR': 10.0}
        hazard_safe = alu.calculate_hazard_score(sensors_safe)
        self.assert_test(hazard_safe == 0.0,
                        "Safe sensors → Hazard score = 0.0")
        
        sensors_danger = {'FL': 0.5, 'FR': 10.0, 'BL': 10.0, 'BR': 10.0}
        hazard_danger = alu.calculate_hazard_score(sensors_danger)
        self.assert_test(hazard_danger == 1.0,
                        "Dangerous sensor → Hazard score = 1.0")
    
    def test_hysteresis(self):
        """Test hysteresis mechanism prevents oscillation"""
        print("\n" + "="*60)
        print("TEST CATEGORY: Hysteresis Test")
        print("="*60)
        
        alu = ALUDecisionEngine(mode='normal')
        sensors = {'FL': 1.5, 'FR': 10.0, 'BL': 10.0, 'BR': 10.0}
        
        # Initial state
        initial_state = alu.current_state
        
        # Update multiple times with same sensor input
        hysteresis_cycles = DRIVING_MODES['normal']['hysteresis_cycles']
        for i in range(hysteresis_cycles - 1):
            alu.update_state(sensors, current_speed=2.0)
        
        # State should NOT have changed yet (hysteresis)
        self.assert_test(alu.current_state == initial_state,
                        f"State unchanged after {hysteresis_cycles-1} cycles (hysteresis)")
        
        # One more cycle should trigger transition
        alu.update_state(sensors, current_speed=2.0)
        self.assert_test(alu.current_state != initial_state,
                        f"State changed after {hysteresis_cycles} cycles")
    
    def test_mode_differences(self):
        """Test that different modes produce different behavior"""
        print("\n" + "="*60)
        print("TEST CATEGORY: Mode Behavior Difference")
        print("="*60)
        
        # Same sensor scenario, different modes
        sensors = {'FL': 2.5, 'FR': 2.5, 'BL': 10.0, 'BR': 10.0}
        speed = 3.0
        
        alu_cautious = ALUDecisionEngine(mode='cautious')
        alu_normal = ALUDecisionEngine(mode='normal')
        alu_aggressive = ALUDecisionEngine(mode='aggressive')
        
        hazard_cautious = alu_cautious.calculate_hazard_score(sensors)
        hazard_normal = alu_normal.calculate_hazard_score(sensors)
        hazard_aggressive = alu_aggressive.calculate_hazard_score(sensors)
        
        # Cautious should perceive higher hazard than aggressive
        self.assert_test(hazard_cautious > hazard_aggressive,
                        "Cautious mode perceives higher hazard than Aggressive")
        
        # Check TTC thresholds differ
        ttc_threshold_cautious = DRIVING_MODES['cautious']['ttc_threshold']
        ttc_threshold_aggressive = DRIVING_MODES['aggressive']['ttc_threshold']
        
        self.assert_test(ttc_threshold_cautious > ttc_threshold_aggressive,
                        "Cautious has higher TTC threshold than Aggressive")
    
    def test_scenario_performance(self, scenario, mode, duration=30):
        """Run a scenario and return performance metrics"""
        print(f"\n  Testing: Scenario={scenario}, Mode={mode}")
        
        controller = AutonomousVehicleController(mode=mode, scenario=scenario)
        
        # Run simulation for duration
        import time
        end_time = time.time() + duration
        while time.time() < end_time:
            controller.run_cycle()
            time.sleep(controller.dt)
        
        metrics = controller.metrics
        print(f"    Collisions: {metrics['total_collisions']}")
        print(f"    Avg Hazard: {metrics['avg_hazard_score']:.3f}")
        print(f"    State Transitions: {metrics['state_transitions']}")
        
        return metrics
    
    def test_scenarios(self):
        """Test all predefined scenarios"""
        print("\n" + "="*60)
        print("TEST CATEGORY: Scenario-Based Tests")
        print("="*60)
        
        scenarios = ['corridor', 'random', 'intersection', 'dense']
        
        # Test each scenario with normal mode (short duration for testing)
        for scenario in scenarios:
            print(f"\nScenario: {scenario}")
            metrics = self.test_scenario_performance(scenario, 'normal', duration=10)
            
            # Acceptance criteria: should complete without excessive collisions
            self.assert_test(metrics['total_collisions'] < 5,
                            f"{scenario} scenario completed with acceptable collisions")
    
    def test_mode_comparison(self):
        """Compare behavior across all three modes"""
        print("\n" + "="*60)
        print("TEST CATEGORY: Mode Comparison (Random Scenario)")
        print("="*60)
        
        modes = ['cautious', 'normal', 'aggressive']
        results = {}
        
        for mode in modes:
            print(f"\n  Mode: {mode.upper()}")
            metrics = self.test_scenario_performance('random', mode, duration=20)
            results[mode] = metrics
        
        print("\n  COMPARISON SUMMARY:")
        print("  " + "-"*50)
        for mode in modes:
            m = results[mode]
            print(f"  {mode.upper():12s} - Collisions: {m['total_collisions']:2d} | "
                  f"Hazard: {m['avg_hazard_score']:.3f} | "
                  f"Transitions: {m['state_transitions']:3d}")
    
    def run_all_tests(self, include_scenarios=True):
        """Run complete test suite"""
        print("\n" + "#"*60)
        print("# ALU DECISION LOGIC - COMPREHENSIVE TEST SUITE")
        print("#"*60)
        
        self.test_dummy_sensors()
        self.test_edge_cases()
        self.test_hysteresis()
        self.test_mode_differences()
        
        if include_scenarios:
            self.test_scenarios()
            self.test_mode_comparison()
        
        # Final report
        print("\n" + "="*60)
        print("TEST RESULTS SUMMARY")
        print("="*60)
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_failed}")
        print(f"Success Rate: {self.tests_passed/(self.tests_passed+self.tests_failed)*100:.1f}%")
        print("="*60)
        
        return self.tests_failed == 0


def main():
    """Run test suite"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ALU Decision Logic Test Suite')
    parser.add_argument('--quick', action='store_true',
                       help='Skip scenario tests (faster)')
    
    args = parser.parse_args()
    
    suite = ALUTestSuite()
    success = suite.run_all_tests(include_scenarios=not args.quick)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
