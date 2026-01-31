"""
Quick test of the new obstacle adapter method.
Demonstrates the clean integration point for Person 3 (Backend).
"""

import json
import sys
import os

# Add src folder to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from obstacles import ObstacleManager
from sensors import SensorArray
from test_utils import load_config

config = load_config('config.json')

# Create obstacle manager with obstacles
obstacles = ObstacleManager(config['world'])
obstacles.add_obstacles_from_list(config['scenarios']['random']['obstacles'])

print("Testing obstacle adapter for backend integration:\n")

# Old way (what backend would do without adapter):
print("❌ Without adapter (backend would do this):")
obs_list_manual = [(o.x, o.y, o.radius) for o in obstacles.get_all()]
print(f"   obstacles.get_all() → [{obs_list_manual[0]}...]")
print(f"   Manual conversion needed: {len(obs_list_manual)} lines\n")

# New way (clean integration):
print("✅ With adapter (now built-in):")
obs_list_adapter = obstacles.get_obstacle_tuples()
print(f"   obstacles.get_obstacle_tuples() → [{obs_list_adapter[0]}...]")
print(f"   No conversion needed: 1 line!\n")

# Verify they're the same
assert obs_list_manual == obs_list_adapter, "Adapter should produce identical output"

# Show usage in sensors
print("Usage in sensor raycast:")
sensors = SensorArray(config['sensors'], car_radius=10)
distances = sensors.raycast(
    car_x=50, car_y=250, car_theta=0,
    obstacles=obstacles.get_obstacle_tuples()  # ← Clean adapter call
)
print(f"   distances = sensors.raycast(..., obstacles=obstacles.get_obstacle_tuples())")
print(f"   Result: {distances}\n")

print("✓ Adapter is ready for Person 3 backend integration")
