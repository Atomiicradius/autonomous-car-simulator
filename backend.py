"""
Backend Control Loop
Author: ALU Engineer (Person 2)

Main control system integrating sensors, ALU decision logic, and physics.
Runs at 100ms control cycle (10 Hz).
"""

import time
import json
from datetime import datetime
from math import cos, sin
from alu_decision import ALUDecisionEngine
from sensors import SensorArray
from physics import Vehicle, Environment
from config import CONTROL_CONFIG, DRIVING_MODES, PHYSICS_CONFIG


class AutonomousVehicleController:
    """
    Main controller orchestrating the autonomous vehicle system.
    """

    def __init__(self, mode='normal', scenario='random', test_mode=False):
        """
        Initialize the autonomous vehicle controller.

        Args:
            mode (str): Driving mode
            scenario (str): Environment scenario
            test_mode (bool): Disable real-time delays for testing
        """
        self.mode = mode
        self.scenario = scenario
        self.test_mode = test_mode

        # Load configuration
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        car_config = config['car']
        sensor_config = config['sensors']
        world_config = config['world']

        # Initialize subsystems
        self.alu = ALUDecisionEngine(mode=mode)
        self.sensors = SensorArray(config=sensor_config, car_radius=car_config['car_radius'])
        
        # Create car config with all needed parameters
        car_init_config = {
            **car_config,
            **world_config
        }
        self.vehicle = Vehicle(
            x=car_config['start_x'],
            y=car_config['start_y'],
            theta=car_config['start_theta'],
            config=car_init_config
        )
        self.environment = Environment(scenario=scenario)

        # Control timing
        self.dt = CONTROL_CONFIG['cycle_time_ms'] / 1000.0
        self.cycle_count = 0
        self.start_time = None

        # Telemetry
        self.telemetry_log = []
        self.metrics = {
            'total_collisions': 0,
            'avg_hazard_score': 0.0,
            'state_transitions': 0,
            'emergency_brakes': 0,
            'ttc_interventions': 0,
        }

    def run_cycle(self):
        """Execute one control cycle"""

        # Get obstacles in the format expected by raycast (tuples of x, y, radius)
        obstacles = []
        for obs in self.environment.get_obstacles():
            obs_x = obs['pos'][0]
            obs_y = obs['pos'][1]
            obs_radius = obs['radius']
            obstacles.append((obs_x, obs_y, obs_radius))

        # Get sensor readings using raycast
        sensor_readings = self.sensors.raycast(
            self.vehicle.x,
            self.vehicle.y,
            self.vehicle.theta,
            obstacles
        )

        max_speed = DRIVING_MODES[self.mode]['max_speed']
        state = self.alu.update_state(sensor_readings, self.vehicle.v)
        control_output = self.alu.get_control_output(state)

        # Apply control commands (Car API expects just magnitude/direction)
        throttle = control_output.get('throttle', 0)
        steering = control_output.get('steering', 0)
        brake = control_output.get('brake', 0)
        
        if brake:
            self.vehicle.brake()
        else:
            self.vehicle.accelerate(throttle)
        
        self.vehicle.turn(steering)
        self.vehicle.update(self.dt)
        
        # Check for collision
        collision = False
        car_radius = self.vehicle.car_radius
        for obs_x, obs_y, obs_radius in obstacles:
            dist_to_obs = ((self.vehicle.x - obs_x)**2 + (self.vehicle.y - obs_y)**2)**0.5
            if dist_to_obs < car_radius + obs_radius:
                collision = True
                self.vehicle.increment_collision()
                break

        telemetry = self._collect_telemetry(sensor_readings, state, collision)
        self.telemetry_log.append(telemetry)
        self._update_metrics(telemetry)

        self.cycle_count += 1
        return telemetry

    def _collect_telemetry(self, sensor_readings, state, collision):
        alu_metrics = self.alu.get_metrics() if hasattr(self.alu, 'get_metrics') else {
            'hazard_score': self.alu.hazard_score,
            'ttc': self.alu.ttc
        }
        
        vehicle_state_obj = self.vehicle.get_state()
        vehicle_state = vehicle_state_obj.to_dict()

        return {
            'cycle': self.cycle_count,
            'timestamp': time.time() - (self.start_time or time.time()),
            'state': state,
            'position': (vehicle_state['x'], vehicle_state['y']),
            'speed': vehicle_state['v'],
            'heading': vehicle_state['theta'],
            'sensors': sensor_readings,
            'hazard_score': alu_metrics.get('hazard_score', 0),
            'ttc': alu_metrics.get('ttc', float('inf')),
            'collision': collision,
            'total_collisions': self.vehicle.collision_count,
        }

    def _update_metrics(self, telemetry):
        if len(self.telemetry_log) > 1:
            prev_state = self.telemetry_log[-2]['state']
            if prev_state != telemetry['state']:
                self.metrics['state_transitions'] += 1

        if telemetry['state'] == 'EMERGENCY_BRAKE':
            self.metrics['emergency_brakes'] += 1

        if telemetry['ttc'] < DRIVING_MODES[self.mode]['ttc_threshold']:
            self.metrics['ttc_interventions'] += 1

        total_hazard = sum(t['hazard_score'] for t in self.telemetry_log)
        self.metrics['avg_hazard_score'] = total_hazard / len(self.telemetry_log)
        self.metrics['total_collisions'] = telemetry['total_collisions']

    def run_simulation(self, duration=None):
        """
        Run simulation (real-time for demo, fast for tests)
        """
        if duration is None:
            duration = CONTROL_CONFIG['simulation_duration']

        self.start_time = time.time()
        end_time = self.start_time + duration

        max_cycles = 20 if self.test_mode else float('inf')

        while time.time() < end_time and self.cycle_count < max_cycles:
            cycle_start = time.time()
            self.run_cycle()

            if not self.test_mode:
                elapsed = time.time() - cycle_start
                sleep_time = max(0, self.dt - elapsed)
                time.sleep(sleep_time)

    def save_telemetry(self, filename=None):
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"telemetry_{self.mode}_{self.scenario}_{timestamp}.json"

        with open(filename, 'w') as f:
            json.dump({
                'mode': self.mode,
                'scenario': self.scenario,
                'metrics': self.metrics,
                'telemetry': self.telemetry_log,
            }, f, indent=2)

    def get_current_state(self):
        """Get current state for visualization"""
        # Convert obstacles to visualization format
        obstacles = []
        for obs in self.environment.get_obstacles():
            obstacles.append({
                'x': obs['pos'][0],
                'y': obs['pos'][1],
                'radius': obs['radius']
            })
        
        # Get vehicle state
        vehicle_state_obj = self.vehicle.get_state()
        vehicle = {
            'x': self.vehicle.x,
            'y': self.vehicle.y,
            'heading': self.vehicle.theta,
            'speed': self.vehicle.v,
            'radius': self.vehicle.car_radius
        }
        
        # Generate sensor rays for visualization
        sensor_rays = []
        if hasattr(self.sensors, 'sensor_offsets'):
            for sensor_name, angle_offset in self.sensors.sensor_offsets.items():
                ray_angle = self.vehicle.theta + angle_offset
                ray_end_x = self.vehicle.x + self.sensors.max_range * (cos(ray_angle))
                ray_end_y = self.vehicle.y + self.sensors.max_range * (sin(ray_angle))
                
                sensor_rays.append({
                    'name': sensor_name,
                    'start': (self.vehicle.x, self.vehicle.y),
                    'end': (ray_end_x, ray_end_y),
                    'distance': 0  # Will be filled from sensor readings
                })
        
        alu_metrics = self.alu.get_metrics() if hasattr(self.alu, 'get_metrics') else {
            'hazard_score': self.alu.hazard_score,
            'ttc': self.alu.ttc
        }
        
        return {
            'vehicle': vehicle,
            'obstacles': obstacles,
            'sensor_rays': sensor_rays,
            'alu_state': self.alu.current_state,
            'alu_metrics': alu_metrics,
            'cycle': self.cycle_count
        }


def main():
    import argparse

    parser = argparse.ArgumentParser(description='ALU-Based Autonomous Vehicle Simulator')
    parser.add_argument('--mode', default='normal')
    parser.add_argument('--scenario', default='random')
    parser.add_argument('--duration', type=float, default=60.0)
    parser.add_argument('--save', action='store_true')

    args = parser.parse_args()

    controller = AutonomousVehicleController(
        mode=args.mode,
        scenario=args.scenario,
        test_mode=False
    )

    controller.run_simulation(duration=args.duration)

    if args.save:
        controller.save_telemetry()


if __name__ == '__main__':
    main()
