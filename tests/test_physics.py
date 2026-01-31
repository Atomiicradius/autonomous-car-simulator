"""
Unit tests for Day 1 physics implementation.
Tests car kinematics, obstacles, and collision detection.
"""

import math
import json
import sys
import os

# Add src folder to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from physics import Car, CarState
from obstacles import CircleObstacle, ObstacleManager, ObstacleType
from test_utils import load_config


def test_car_initialization():
    """Test car spawns at correct position."""
    config = load_config('config.json')
    car_config = config['car']
    world_config = config['world']
    
    car = Car(
        x=car_config['start_x'],
        y=car_config['start_y'],
        theta=car_config['start_theta'],
        config={**car_config, **world_config}
    )
    
    assert car.x == car_config['start_x'], f"Expected x={car_config['start_x']}, got {car.x}"
    assert car.y == car_config['start_y'], f"Expected y={car_config['start_y']}, got {car.y}"
    assert car.v == 0.0, "Initial velocity should be 0"
    assert car.collision_count == 0, "Initial collision count should be 0"
    print("✓ Car initialization test passed")


def test_car_forward_movement():
    """Test car moves forward when accelerated."""
    config = load_config('config.json')
    car_config = config['car']
    world_config = config['world']
    
    car = Car(
        x=250, y=250, theta=0,  # heading right (+X)
        config={**car_config, **world_config}
    )
    
    # Accelerate forward
    car.accelerate(1.0)
    initial_x = car.x
    
    # Update for 1 second (10 steps of 0.1s each)
    for _ in range(10):
        car.update(0.1)
    
    assert car.x > initial_x, f"Car should move right; x: {initial_x} → {car.x}"
    assert car.v > 0, f"Velocity should be positive, got {car.v}"
    print(f"✓ Forward movement test passed (moved {car.x - initial_x:.1f} units)")


def test_car_backward_movement():
    """Test car moves backward when reverse is applied."""
    config = load_config('config.json')
    car_config = config['car']
    world_config = config['world']
    
    car = Car(
        x=250, y=250, theta=0,
        config={**car_config, **world_config}
    )
    
    # Accelerate backward
    car.accelerate(-1.0)
    initial_x = car.x
    
    # Update for 0.5 seconds
    for _ in range(5):
        car.update(0.1)
    
    assert car.x < initial_x, f"Car should move left; x: {initial_x} → {car.x}"
    assert car.v < 0, f"Velocity should be negative, got {car.v}"
    print(f"✓ Backward movement test passed (moved {initial_x - car.x:.1f} units)")


def test_car_turning():
    """Test car heading changes when turning."""
    config = load_config('config.json')
    car_config = config['car']
    world_config = config['world']
    
    car = Car(
        x=250, y=250, theta=0,
        config={**car_config, **world_config}
    )
    
    initial_theta = car.theta
    
    # Turn left
    car.turn(1.0)
    
    assert car.theta > initial_theta, f"Theta should increase; {initial_theta} → {car.theta}"
    print(f"✓ Turning test passed (rotated {car.theta - initial_theta:.2f} rad)")


def test_car_braking():
    """Test brake brings car to stop."""
    config = load_config('config.json')
    car_config = config['car']
    world_config = config['world']
    
    car = Car(
        x=250, y=250, theta=0,
        config={**car_config, **world_config}
    )
    
    # Build up speed
    for _ in range(5):
        car.accelerate(1.0)
    
    assert car.v > 0, "Car should have velocity"
    
    # Brake
    car.brake()
    
    assert car.v == 0, f"Velocity after brake should be 0, got {car.v}"
    print("✓ Braking test passed")


def test_car_friction():
    """Test friction slows car down over time."""
    config = load_config('config.json')
    car_config = config['car']
    world_config = config['world']
    
    car = Car(
        x=250, y=250, theta=0,
        config={**car_config, **world_config}
    )
    
    # Accelerate once, then let friction slow it
    car.accelerate(1.0)
    car.update(0.1)
    vel_after_accel = car.v
    
    # No more acceleration, just friction
    car.update(0.1)
    vel_after_friction = car.v
    
    assert vel_after_friction < vel_after_accel, "Friction should reduce velocity"
    print(f"✓ Friction test passed (v: {vel_after_accel:.2f} → {vel_after_friction:.2f})")


def test_car_boundary_bounce():
    """Test car bounces off world boundaries with velocity reversal and heading reflection."""
    config = load_config('config.json')
    car_config = config['car']
    world_config = config['world']
    
    # Spawn near left edge (x=12), facing left (π radians)
    # Car radius is 10, so boundary is at x=10
    car = Car(
        x=12, y=250, theta=math.pi,  # heading left
        config={**car_config, **world_config}
    )
    
    # Accelerate hard toward wall - should hit within a few steps
    for _ in range(50):
        car.accelerate(1.0)
        car.update(0.1)
        if car.x <= car.car_radius:
            break  # Hit the wall
    
    # Should have bounced and stayed in bounds
    assert car.x >= car.car_radius, f"Car x={car.x} should be >= car_radius={car.car_radius}"
    
    # Heading should have reflected: if facing left (π), should face right (0) after bounce
    # Reflection formula: θ_new = (π - θ_old) % 2π
    # π - π = 0, so should be facing right (0°)
    theta_degrees = math.degrees(car.theta) % 360
    assert theta_degrees < 45 or theta_degrees > 315, \
        f"After bouncing off left wall, should face right; got {theta_degrees:.1f}°"
    
    print("✓ Boundary bounce test passed")


def test_obstacle_creation():
    """Test obstacle creation."""
    obs = CircleObstacle(x=250, y=250, radius=20, obstacle_type=ObstacleType.STATIC)
    
    assert obs.x == 250, "Obstacle x position incorrect"
    assert obs.y == 250, "Obstacle y position incorrect"
    assert obs.radius == 20, "Obstacle radius incorrect"
    print("✓ Obstacle creation test passed")


def test_obstacle_manager_add():
    """Test adding obstacles to manager."""
    config = load_config('config.json')
    world_config = config['world']
    
    manager = ObstacleManager(world_config)
    
    obs1 = CircleObstacle(x=100, y=100, radius=15, obstacle_type=ObstacleType.STATIC)
    obs2 = CircleObstacle(x=400, y=400, radius=15, obstacle_type=ObstacleType.STATIC)
    
    manager.add_obstacle(obs1)
    manager.add_obstacle(obs2)
    
    assert len(manager.obstacles) == 2, f"Expected 2 obstacles, got {len(manager.obstacles)}"
    print("✓ Obstacle manager add test passed")


def test_collision_detection():
    """Test circle-circle collision detection."""
    config = load_config('config.json')
    car_config = config['car']
    world_config = config['world']
    
    manager = ObstacleManager(world_config)
    
    # Create obstacle at (250, 250) with radius 20
    obs = CircleObstacle(x=250, y=250, radius=20, obstacle_type=ObstacleType.STATIC)
    manager.add_obstacle(obs)
    
    # Car far away: no collision
    car_pos = (100, 100)
    assert not manager.check_car_collision(car_pos, 10), "Should not collide when far away"
    
    # Car very close: collision
    car_pos = (260, 250)
    assert manager.check_car_collision(car_pos, 10), "Should collide when very close"
    
    print("✓ Collision detection test passed")


def test_scenario_loading():
    """Test loading scenario from config."""
    config = load_config('config.json')
    world_config = config['world']
    
    manager = ObstacleManager(world_config)
    
    # Load corridor scenario (now has 6 obstacles: 3 on top, 3 on bottom)
    corridor_obs = config['scenarios']['corridor']['obstacles']
    manager.add_obstacles_from_list(corridor_obs)
    
    assert len(manager.obstacles) == 6, f"Expected 6 obstacles in corridor, got {len(manager.obstacles)}"
    print("✓ Scenario loading test passed")


def test_moving_obstacle():
    """Test moving obstacle updates position."""
    config = load_config('config.json')
    world_config = config['world']
    
    obs = CircleObstacle(
        x=250,
        y=250,
        radius=15,
        obstacle_type=ObstacleType.BOUNCE,
        velocity=10.0,  # units/s
        direction_angle=0,  # moving right
        world_width=world_config['width'],
        world_height=world_config['height']
    )
    
    initial_x = obs.x
    obs.update(0.1)  # 100ms step
    
    # Should move ~1 unit to the right
    assert obs.x > initial_x, f"Moving obstacle should have moved; x: {initial_x} → {obs.x}"
    print(f"✓ Moving obstacle test passed (moved {obs.x - initial_x:.1f} units)")


def run_all_tests():
    """Run all tests."""
    print("\n" + "="*60)
    print("RUNNING DAY 1 PHYSICS TESTS")
    print("="*60 + "\n")
    
    tests = [
        test_car_initialization,
        test_car_forward_movement,
        test_car_backward_movement,
        test_car_turning,
        test_car_braking,
        test_car_friction,
        test_car_boundary_bounce,
        test_obstacle_creation,
        test_obstacle_manager_add,
        test_collision_detection,
        test_scenario_loading,
        test_moving_obstacle,
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
