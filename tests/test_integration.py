"""
Integration test combining Day 1 physics with Day 2 sensors.
Simulates car navigating with sensor feedback.
"""

import json
import math
import sys
import os

# Add src folder to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from physics import Car
from obstacles import ObstacleManager, CircleObstacle, ObstacleType
from sensors import SensorArray
from test_utils import load_config


def test_physics_sensors_integration():
    """
    Integration test: car with physics and sensors in corridor scenario.
    """
    config = load_config('config.json')
    
    # Initialize components
    car = Car(
        x=config['car']['start_x'],
        y=config['car']['start_y'],
        theta=config['car']['start_theta'],
        config={**config['car'], **config['world']}
    )
    
    obstacles_mgr = ObstacleManager(config['world'])
    obstacles_mgr.add_obstacles_from_list(
        config['scenarios']['corridor']['obstacles']
    )
    
    sensors = SensorArray(config['sensors'], car_radius=car.car_radius)
    sensors.set_noise_enabled(False)
    sensors.set_filter_enabled(False)
    
    # Simulation parameters
    dt = config['world']['dt']
    num_steps = 100
    
    print(f"\n{'='*60}")
    print("INTEGRATION TEST: Physics + Sensors (Corridor)")
    print(f"{'='*60}\n")
    
    print(f"Starting position: ({car.x:.1f}, {car.y:.1f})")
    print(f"Obstacles: {len(obstacles_mgr.obstacles)}")
    print(f"Simulation: {num_steps} steps @ {dt}s = {num_steps * dt}s total\n")
    
    # Run simulation
    for step in range(num_steps):
        # Apply throttle
        car.accelerate(1.0)
        
        # Update physics
        car.update(dt)
        obstacles_mgr.update(dt)
        
        # Read sensors
        obs_list = [(o.x, o.y, o.radius) for o in obstacles_mgr.obstacles]
        sensor_distances = sensors.update(
            car.x, car.y, car.theta, obs_list, timestamp=step * dt
        )
        
        # Check collision
        if obstacles_mgr.check_car_collision(car.get_position(), car.car_radius):
            car.increment_collision()
        
        # Print progress every 20 steps
        if step % 20 == 0:
            print(f"Step {step:3d}: pos=({car.x:6.1f}, {car.y:6.1f}), "
                  f"v={car.v:4.2f}, "
                  f"FL={sensor_distances['FL']:6.1f}, "
                  f"FR={sensor_distances['FR']:6.1f}")
    
    print(f"\nFinal position: ({car.x:.1f}, {car.y:.1f})")
    print(f"Final velocity: {car.v:.2f}")
    print(f"Total collisions: {car.collision_count}")
    print(f"Distance traveled: {car.x - config['car']['start_x']:.1f} units")
    
    # Assertions
    assert car.x > config['car']['start_x'], "Car should have moved forward"
    assert car.y == config['car']['start_y'], "Car should stay in Y (corridor constraint)"
    
    print(f"\n✓ Integration test passed")


def test_all_scenarios_sensors():
    """Test sensors work with all scenarios."""
    config = load_config('config.json')
    
    print(f"\n{'='*60}")
    print("TESTING ALL SCENARIOS WITH SENSORS")
    print(f"{'='*60}\n")
    
    for scenario_name in ['corridor', 'random', 'intersection', 'dense']:
        scenario = config['scenarios'][scenario_name]
        
        # Setup
        obstacles_mgr = ObstacleManager(config['world'])
        obstacles_mgr.add_obstacles_from_list(scenario['obstacles'])
        
        sensors = SensorArray(config['sensors'], car_radius=10)
        
        # Get sensor reading
        obs_list = [(o.x, o.y, o.radius) for o in obstacles_mgr.obstacles]
        distances = sensors.raycast(50, 250, 0, obs_list)
        
        min_dist = min(distances.values())
        max_dist = max(distances.values())
        
        print(f"{scenario_name:15s}: min={min_dist:6.1f}, max={max_dist:6.1f}, "
              f"obstacles={len(obstacles_mgr.obstacles)}")
    
    print(f"\n✓ All scenarios test passed")


def test_noise_and_filter_integration():
    """Test noise and filter with physics/sensors."""
    config = load_config('config.json')
    
    print(f"\n{'='*60}")
    print("TESTING NOISE & FILTER WITH PHYSICS")
    print(f"{'='*60}\n")
    
    car = Car(
        x=100, y=250, theta=0,
        config={**config['car'], **config['world']}
    )
    
    obstacles_mgr = ObstacleManager(config['world'])
    obstacles_mgr.add_obstacles_from_list(
        config['scenarios']['random']['obstacles']
    )
    
    sensors = SensorArray(config['sensors'], car_radius=car.car_radius)
    
    # Test each combination
    combos = [
        (False, False, "No noise, no filter"),
        (True, False, "With noise, no filter"),
        (False, True, "No noise, with filter"),
        (True, True, "With noise & filter"),
    ]
    
    for noise_on, filter_on, label in combos:
        sensors.set_noise_enabled(noise_on)
        sensors.set_filter_enabled(filter_on)
        sensors.reset_filters()
        
        # Run 20 steps and collect FL readings
        fl_readings = []
        for _ in range(20):
            car.accelerate(1.0)
            car.update(0.1)
            obstacles_mgr.update(0.1)
            
            obs_list = [(o.x, o.y, o.radius) for o in obstacles_mgr.obstacles]
            distances = sensors.update(car.x, car.y, car.theta, obs_list)
            fl_readings.append(distances['FL'])
        
        # Compute variance
        if len(fl_readings) > 1:
            variance = max(fl_readings) - min(fl_readings)
        else:
            variance = 0
        
        print(f"  {label:30s}: variance={variance:6.2f}, "
              f"range=[{min(fl_readings):6.1f}, {max(fl_readings):6.1f}]")
    
    print(f"\n✓ Noise & filter integration test passed")


if __name__ == '__main__':
    test_physics_sensors_integration()
    test_all_scenarios_sensors()
    test_noise_and_filter_integration()
    
    print(f"\n{'='*60}")
    print("ALL INTEGRATION TESTS PASSED ✓")
    print(f"{'='*60}\n")
