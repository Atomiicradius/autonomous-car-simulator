import json
import math
from physics import Car

config = json.load(open('config.json'))
car_config = config['car']
world_config = config['world']

car = Car(
    x=20, y=250, theta=math.pi,  # heading left
    config={**car_config, **world_config}
)

print(f"Start: x={car.x:.1f}, theta={math.degrees(car.theta):.1f}°")

for i in range(20):
    car.accelerate(1.0)
    car.update(0.1)
    if i % 5 == 0:
        print(f"Step {i:2d}: x={car.x:6.1f}, v={car.v:5.2f}, theta={math.degrees(car.theta):7.1f}°")

print(f"Final: x={car.x:.1f}, theta={math.degrees(car.theta):.1f}°")
print(f"Car radius: {car.car_radius}")
print(f"World width: {car.world_width}")
