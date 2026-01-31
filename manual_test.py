import json
from physics import Car
from obstacles import CircleObstacle, ObstacleManager

config = json.load(open('config.json'))

# Spawn car
car = Car(50, 250, 0, {**config['car'], **config['world']})

# Spawn obstacle
manager = ObstacleManager(config['world'])
manager.add_obstacles_from_list(config['scenarios']['corridor']['obstacles'])

# Simulate 100 steps
for i in range(100):
    car.accelerate(1.0)
    car.update(0.1)
    manager.update(0.1)
    
    collision = manager.check_car_collision(car.get_position(), car.car_radius)
    if i % 10 == 0:
        print(f"Step {i}: pos={car.get_position()}, v={car.get_velocity():.2f}, collision={collision}")