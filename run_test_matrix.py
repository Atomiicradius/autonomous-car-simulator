"""
Test Matrix Runner
Runs all 12 configurations (4 scenarios × 3 modes) and generates comparison data
"""

import os
import json
import csv
from datetime import datetime
from backend import AutonomousVehicleController

# Configuration
SCENARIOS = ['corridor', 'random', 'intersection', 'dense']
MODES = ['cautious', 'normal', 'aggressive']
DURATION = 60.0  # seconds per run

def run_test_matrix():
    """Run all 12 configurations and collect results"""
    
    print("=" * 70)
    print("ALU AUTONOMOUS VEHICLE - TEST MATRIX")
    print("=" * 70)
    print(f"Running {len(SCENARIOS)} scenarios × {len(MODES)} modes = {len(SCENARIOS) * len(MODES)} configurations")
    print(f"Duration per run: {DURATION}s")
    print("=" * 70)
    print()
    
    results = []
    
    for scenario in SCENARIOS:
        for mode in MODES:
            print(f"\n{'='*70}")
            print(f"Running: {scenario.upper()} scenario in {mode.upper()} mode")
            print(f"{'='*70}")
            
            # Create controller
            controller = AutonomousVehicleController(
                mode=mode,
                scenario=scenario,
                test_mode=False
            )
            
            # Run simulation
            controller.run_simulation(duration=DURATION)
            
            # Save telemetry
            json_file = controller.save_telemetry()
            csv_file = controller.save_telemetry_csv()
            
            # Get metrics
            metrics = controller.get_summary_metrics()
            results.append(metrics)
            
            # Print summary
            print(f"\n✓ Completed: {scenario}/{mode}")
            print(f"  Collisions: {metrics['total_collisions']}")
            print(f"  Distance: {metrics['total_distance']:.1f}m")
            print(f"  Avg Speed: {metrics['avg_speed']:.2f} m/s")
            print(f"  Avg Hazard: {metrics['avg_hazard_score']:.3f}")
            print(f"  CSV saved: {csv_file}")
    
    # Save comparison results
    save_comparison_results(results)
    print_comparison_table(results)
    
    return results


def save_comparison_results(results):
    """Save comparison results to CSV"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"logs/comparison_results_{timestamp}.csv"
    
    os.makedirs('logs', exist_ok=True)
    
    with open(filename, 'w', newline='') as f:
        fieldnames = [
            'scenario', 'mode', 'total_time', 'total_cycles',
            'total_collisions', 'total_distance', 'avg_speed',
            'avg_hazard_score', 'state_transitions', 'emergency_brakes',
            'ttc_interventions', 'time_to_first_collision'
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    
    print(f"\n{'='*70}")
    print(f"✓ Comparison results saved: {filename}")
    print(f"{'='*70}")
    
    return filename


def print_comparison_table(results):
    """Print formatted comparison table"""
    
    print("\n" + "="*70)
    print("COMPARISON RESULTS")
    print("="*70)
    print()
    
    # Group by scenario
    for scenario in SCENARIOS:
        scenario_results = [r for r in results if r['scenario'] == scenario]
        
        print(f"\n{scenario.upper()} Scenario:")
        print("-" * 70)
        print(f"{'Mode':<12} {'Collisions':<12} {'Avg Speed':<12} {'Distance':<12} {'Avg Hazard':<12}")
        print("-" * 70)
        
        for result in scenario_results:
            print(f"{result['mode']:<12} "
                  f"{result['total_collisions']:<12} "
                  f"{result['avg_speed']:<12.2f} "
                  f"{result['total_distance']:<12.1f} "
                  f"{result['avg_hazard_score']:<12.3f}")
    
    print("\n" + "="*70)
    
    # Summary statistics
    print("\nSUMMARY BY MODE:")
    print("-" * 70)
    
    for mode in MODES:
        mode_results = [r for r in results if r['mode'] == mode]
        avg_collisions = sum(r['total_collisions'] for r in mode_results) / len(mode_results)
        avg_speed = sum(r['avg_speed'] for r in mode_results) / len(mode_results)
        avg_hazard = sum(r['avg_hazard_score'] for r in mode_results) / len(mode_results)
        
        print(f"\n{mode.upper()}:")
        print(f"  Average Collisions: {avg_collisions:.1f}")
        print(f"  Average Speed: {avg_speed:.2f} m/s")
        print(f"  Average Hazard: {avg_hazard:.3f}")


if __name__ == '__main__':
    import sys
    
    print("\n⚠️  WARNING: This will run 12 simulations (60s each = 12 minutes total)")
    print("Press Ctrl+C to cancel, or Enter to continue...")
    
    try:
        input()
    except KeyboardInterrupt:
        print("\n\nCancelled.")
        sys.exit(0)
    
    results = run_test_matrix()
    
    print("\n" + "="*70)
    print("✓ ALL TESTS COMPLETE!")
    print("="*70)
