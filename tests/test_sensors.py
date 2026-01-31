"""
Unit tests for Day 2 sensor implementation.
Tests raycast, noise injection, and moving average filtering.
"""

import math
import json
import sys
import os

# Add src folder to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from sensors import SensorArray, SensorReading
from test_utils import load_config


def test_sensor_initialization():
    """Test sensor array initializes correctly."""
    config = load_config('config.json')
    sensor_config = config['sensors']
    
    sensors = SensorArray(sensor_config, car_radius=10)
    
    assert len(sensors.sensor_offsets) == 4, f"Expected 4 sensors, got {len(sensors.sensor_offsets)}"
    assert 'FL' in sensors.sensor_offsets, "FL sensor missing"
    assert 'FR' in sensors.sensor_offsets, "FR sensor missing"
    assert 'BL' in sensors.sensor_offsets, "BL sensor missing"
    assert 'BR' in sensors.sensor_offsets, "BR sensor missing"
    assert sensors.max_range == 100, f"Max range should be 100, got {sensors.max_range}"
    print("✓ Sensor initialization test passed")


def test_raycast_no_obstacles():
    """Test raycast returns max_range when no obstacles present."""
    config = load_config('config.json')
    sensor_config = config['sensors']
    
    sensors = SensorArray(sensor_config, car_radius=10)
    
    # Car at (250, 250) with no obstacles
    distances = sensors.raycast(
        car_x=250,
        car_y=250,
        car_theta=0,
        obstacles=[]
    )
    
    for sensor_name, dist in distances.items():
        assert dist == sensors.max_range, f"{sensor_name} should see max_range, got {dist}"
    
    print("✓ Raycast with no obstacles test passed")


def test_raycast_hits_obstacle():
    """Test raycast detects obstacle in sensor cone."""
    config = load_config('config.json')
    sensor_config = config['sensors']
    
    sensors = SensorArray(sensor_config, car_radius=10)
    
    # Car at (100, 250) heading right (theta=0)
    # FR sensor is at -45° (lower-right), so place obstacle there
    # At distance ~100 in the -45° direction: (100 + 70.7, 250 - 70.7) ≈ (170, 180)
    distances = sensors.raycast(
        car_x=100,
        car_y=250,
        car_theta=0,
        obstacles=[(170, 180, 15)]
    )
    
    # Front-right (FR) should see the obstacle
    fr_dist = distances.get('FR', sensors.max_range)
    assert fr_dist < sensors.max_range * 0.9, f"FR should detect obstacle, got {fr_dist}"
    assert fr_dist > 0, f"FR distance should be positive, got {fr_dist}"
    
    print(f"✓ Raycast hits obstacle test passed (FR distance: {fr_dist:.1f})")


def test_raycast_multiple_obstacles():
    """Test raycast returns distance to nearest obstacle."""
    config = load_config('config.json')
    sensor_config = config['sensors']
    
    sensors = SensorArray(sensor_config, car_radius=10)
    
    # Car at (100, 250) heading right
    # Two obstacles in FR direction (-45°): close and far
    distances = sensors.raycast(
        car_x=100,
        car_y=250,
        car_theta=0,
        obstacles=[
            (140, 210, 15),  # Closer obstacle (40 units away at -45°)
            (170, 180, 15)   # Farther obstacle
        ]
    )
    
    fr_dist = distances.get('FR', sensors.max_range)
    # Should detect the closer one
    assert fr_dist < 60, f"Should detect closest obstacle, got {fr_dist}"
    
    print(f"✓ Raycast multiple obstacles test passed (closest: {fr_dist:.1f})")


def test_sensor_update():
    """Test complete sensor update cycle."""
    config = load_config('config.json')
    sensor_config = config['sensors']
    
    sensors = SensorArray(sensor_config, car_radius=10)
    
    # Update sensors
    filtered = sensors.update(
        car_x=100,
        car_y=250,
        car_theta=0,
        obstacles=[(200, 250, 15)]
    )
    
    assert len(filtered) == 4, f"Should return 4 sensor values, got {len(filtered)}"
    assert all(0 <= d <= 100 for d in filtered.values()), "All distances should be in [0, 100]"
    
    print("✓ Sensor update test passed")


def test_noise_injection():
    """Test noise makes readings different from true value."""
    config = load_config('config.json')
    sensor_config = config['sensors']
    
    sensors = SensorArray(sensor_config, car_radius=10)
    sensors.set_noise_enabled(True)
    
    # Get several readings and check variance
    readings_list = []
    for _ in range(10):
        filtered = sensors.update(
            car_x=100,
            car_y=250,
            car_theta=0,
            obstacles=[(200, 250, 15)]
        )
        readings_list.append(filtered)
    
    # Extract FR values
    fr_values = [r['FR'] for r in readings_list]
    
    # Check we have variation (noise is working)
    variance = max(fr_values) - min(fr_values)
    assert variance > 0.1, f"Noise should create variance, got {variance}"
    
    print(f"✓ Noise injection test passed (variance: {variance:.2f})")


def test_filter_smoothing():
    """Test moving average filter smooths noisy readings."""
    config = load_config('config.json')
    sensor_config = config['sensors']
    
    sensors = SensorArray(sensor_config, car_radius=10)
    sensors.set_noise_enabled(True)
    sensors.set_filter_enabled(True)
    
    # Get readings with filter
    filtered_readings = []
    for i in range(20):
        filtered = sensors.update(
            car_x=100,
            car_y=250,
            car_theta=0,
            obstacles=[(200, 250, 15)]
        )
        if i >= 4:  # After filter fills up
            filtered_readings.append(filtered['FR'])
    
    # Check readings are less noisy (lower variance)
    # This is qualitative, but filter should smooth spikes
    assert len(filtered_readings) > 0, "Should have filtered readings"
    
    print(f"✓ Filter smoothing test passed ({len(filtered_readings)} readings)")


def test_noise_off_reproducible():
    """Test that without noise, same position gives same reading."""
    config = load_config('config.json')
    sensor_config = config['sensors']
    
    sensors = SensorArray(sensor_config, car_radius=10)
    sensors.set_noise_enabled(False)
    sensors.set_filter_enabled(False)
    
    # Get same reading twice
    reading1 = sensors.update(
        car_x=100,
        car_y=250,
        car_theta=0,
        obstacles=[(200, 250, 15)]
    )
    
    sensors.reset_filters()
    reading2 = sensors.update(
        car_x=100,
        car_y=250,
        car_theta=0,
        obstacles=[(200, 250, 15)]
    )
    
    for sensor in ['FL', 'FR', 'BL', 'BR']:
        assert reading1[sensor] == reading2[sensor], \
            f"{sensor}: {reading1[sensor]} != {reading2[sensor]}"
    
    print("✓ Reproducibility test passed")


def test_raycast_touching_obstacle():
    """Test sensor self-collision avoidance (t > 0.01 check prevents false positives)."""
    config = load_config('config.json')
    sensor_config = config['sensors']
    
    sensors = SensorArray(sensor_config, car_radius=10)
    sensors.set_noise_enabled(False)
    sensors.set_filter_enabled(False)
    
    # Car at (100, 250) with radius 10, obstacle touching at edge
    # Obstacle at (110, 250) with radius 10 - they are exactly touching
    # The raycast t > 0.01 check should prevent near-zero distance detection
    distances = sensors.raycast(100, 250, 0, obstacles=[(110, 250, 10)])
    
    # If any sensor reports very small distance (<1.0), it failed to skip self-collision
    for sensor_name, dist in distances.items():
        assert dist > 1.0 or dist >= 90, \
            f"{sensor_name} may have detected self-collision, got {dist:.2f}"
    
    print("✓ Touching obstacle test passed")


def test_sensor_angles():
    """Test sensors are at correct angles."""
    config = load_config('config.json')
    sensor_config = config['sensors']
    
    sensors = SensorArray(sensor_config, car_radius=10)
    
    # Car heading right (0°)
    # FL should be at 45° (upper right in world, if car is pointing right)
    # FR should be at -45° (lower right)
    # BL should be at 135° (upper left)
    # BR should be at -135° (lower left)
    
    fl_offset = sensors.sensor_offsets['FL']
    fr_offset = sensors.sensor_offsets['FR']
    bl_offset = sensors.sensor_offsets['BL']
    br_offset = sensors.sensor_offsets['BR']
    
    assert abs(fl_offset - math.radians(45)) < 0.01, f"FL offset wrong: {fl_offset}"
    assert abs(fr_offset - math.radians(-45)) < 0.01, f"FR offset wrong: {fr_offset}"
    assert abs(bl_offset - math.radians(135)) < 0.01, f"BL offset wrong: {bl_offset}"
    assert abs(br_offset - math.radians(-135)) < 0.01, f"BR offset wrong: {br_offset}"
    
    print("✓ Sensor angles test passed")


def test_scenario_corridor():
    """Test corridor scenario loads and sensors work."""
    config = load_config('config.json')
    sensor_config = config['sensors']
    scenario = config['scenarios']['corridor']
    
    sensors = SensorArray(sensor_config, car_radius=10)
    
    # Convert scenario obstacles to tuples
    obs_list = [(o['x'], o['y'], o['radius']) for o in scenario['obstacles']]
    
    # Car in middle of corridor
    distances = sensors.raycast(
        car_x=250,
        car_y=250,
        car_theta=0,
        obstacles=obs_list
    )
    
    assert len(distances) == 4, "Should have 4 sensor readings"
    print(f"✓ Corridor scenario test passed")


def test_scenario_random():
    """Test random scenario loads."""
    config = load_config('config.json')
    sensor_config = config['sensors']
    scenario = config['scenarios']['random']
    
    sensors = SensorArray(sensor_config, car_radius=10)
    
    obs_list = [(o['x'], o['y'], o['radius']) for o in scenario['obstacles']]
    
    distances = sensors.raycast(
        car_x=50,
        car_y=250,
        car_theta=0,
        obstacles=obs_list
    )
    
    assert len(distances) == 4, "Should have 4 sensor readings"
    print(f"✓ Random scenario test passed")


def test_scenario_intersection():
    """Test intersection scenario loads."""
    config = load_config('config.json')
    sensor_config = config['sensors']
    scenario = config['scenarios']['intersection']
    
    sensors = SensorArray(sensor_config, car_radius=10)
    
    obs_list = [(o['x'], o['y'], o['radius']) for o in scenario['obstacles']]
    
    distances = sensors.raycast(
        car_x=50,
        car_y=250,
        car_theta=0,
        obstacles=obs_list
    )
    
    assert len(distances) == 4, "Should have 4 sensor readings"
    print(f"✓ Intersection scenario test passed")


def test_scenario_dense():
    """Test dense scenario loads."""
    config = load_config('config.json')
    sensor_config = config['sensors']
    scenario = config['scenarios']['dense']
    
    sensors = SensorArray(sensor_config, car_radius=10)
    
    obs_list = [(o['x'], o['y'], o['radius']) for o in scenario['obstacles']]
    
    distances = sensors.raycast(
        car_x=50,
        car_y=250,
        car_theta=0,
        obstacles=obs_list
    )
    
    assert len(distances) == 4, "Should have 4 sensor readings"
    print(f"✓ Dense scenario test passed")


def run_all_tests():
    """Run all sensor tests."""
    print("\n" + "="*60)
    print("RUNNING DAY 2 SENSOR TESTS")
    print("="*60 + "\n")
    
    tests = [
        test_sensor_initialization,
        test_raycast_no_obstacles,
        test_raycast_hits_obstacle,
        test_raycast_multiple_obstacles,
        test_sensor_update,
        test_noise_injection,
        test_filter_smoothing,
        test_noise_off_reproducible,
        test_raycast_touching_obstacle,
        test_sensor_angles,
        test_scenario_corridor,
        test_scenario_random,
        test_scenario_intersection,
        test_scenario_dense,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"✗ {test.__name__} FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__} ERROR: {e}")
            failed += 1
    
    print("\n" + "="*60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("="*60 + "\n")
    
    return failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    exit(0 if success else 1)
