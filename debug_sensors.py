import json
import math
from sensors import SensorArray

config = json.load(open('config.json'))
sensor_config = config['sensors']

sensors = SensorArray(sensor_config, car_radius=10)

print("Sensor angles:")
for name, angle in sensors.sensor_offsets.items():
    print(f"  {name}: {math.degrees(angle):.1f}°")

print("\nTesting raycast:")
car_x, car_y, car_theta = 100, 250, 0
print(f"Car at ({car_x}, {car_y}), heading {math.degrees(car_theta):.0f}°")

# Obstacle directly ahead-right (at heading 0 + (-45°) = -45°, which is lower-right)
obs_x, obs_y, obs_r = 200, 250, 15
print(f"Obstacle at ({obs_x}, {obs_y}), radius {obs_r}")

# Manually check if FR ray should hit
# FR is at -45° from car heading (0°), so absolute angle is 0 + (-45°) = -45°
# Ray: starts at (100, 250), goes in direction (cos(-45°), sin(-45°))
ray_dx = math.cos(math.radians(-45))
ray_dy = math.sin(math.radians(-45))
print(f"FR ray direction: ({ray_dx:.3f}, {ray_dy:.3f})")

distances = sensors.raycast(car_x, car_y, car_theta, [(obs_x, obs_y, obs_r)])
print(f"\nRaycast results:")
for name, dist in sorted(distances.items()):
    print(f"  {name}: {dist:.1f}")
