"""
Backend Control Loop
Author: ALU Engineer (Person 2)

Main control system integrating sensors, ALU decision logic, and physics.
Runs at 100ms control cycle (10 Hz).
"""

import time
import json
import csv
import os
from datetime import datetime
from alu_decision import ALUDecisionEngine
from sensors import SensorArray
from physics import Vehicle, Environment
from config import CONTROL_CONFIG, DRIVING_MODES


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

        # Initialize subsystems
        self.alu = ALUDecisionEngine(mode=mode)
        self.sensors = SensorArray()
        self.vehicle = Vehicle(x=10.0, y=10.0, heading=0.0)
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

        sensor_readings = self.sensors.scan(
            self.vehicle.position,
            self.vehicle.heading,
            self.environment.get_obstacles()
        )

        max_speed = DRIVING_MODES[self.mode]['max_speed']
        state = self.alu.update_state(sensor_readings, self.vehicle.speed)
        control_output = self.alu.get_control_output(state)

        self.vehicle.apply_control(control_output, self.dt, max_speed)
        collision = self.vehicle.check_collision(self.environment.get_obstacles())

        telemetry = self._collect_telemetry(sensor_readings, state, collision)
        self.telemetry_log.append(telemetry)
        self._update_metrics(telemetry)

        self.cycle_count += 1
        return telemetry

    def _collect_telemetry(self, sensor_readings, state, collision):
        alu_metrics = self.alu.get_metrics()
        vehicle_state = self.vehicle.get_state()

        return {
            'cycle': self.cycle_count,
            'timestamp': time.time() - (self.start_time or time.time()),
            'state': state,
            'position': vehicle_state['position'],
            'speed': vehicle_state['speed'],
            'heading': vehicle_state['heading'],
            'sensors': sensor_readings,
            'hazard_score': alu_metrics['hazard_score'],
            'ttc': alu_metrics['ttc'],
            'collision': collision,
            'total_collisions': vehicle_state['collisions'],
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
        """Save telemetry data to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"logs/telemetry_{self.mode}_{self.scenario}_{timestamp}.json"
        
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)

        with open(filename, 'w') as f:
            json.dump({
                'mode': self.mode,
                'scenario': self.scenario,
                'metrics': self.metrics,
                'telemetry': self.telemetry_log,
            }, f, indent=2)
        
        return filename
    
    def save_telemetry_csv(self, filename=None):
        """Save telemetry data to CSV file for analysis"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"logs/telemetry_{self.mode}_{self.scenario}_{timestamp}.csv"
        
        # Create logs directory if it doesn't exist
        os.makedirs('logs', exist_ok=True)
        
        with open(filename, 'w', newline='') as f:
            fieldnames = [
                'cycle', 'timestamp', 'state', 
                'x', 'y', 'speed', 'heading',
                'FL', 'FR', 'BL', 'BR',
                'hazard_score', 'ttc', 'collision', 'total_collisions'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for entry in self.telemetry_log:
                row = {
                    'cycle': entry['cycle'],
                    'timestamp': entry['timestamp'],
                    'state': entry['state'],
                    'x': entry['position'][0],
                    'y': entry['position'][1],
                    'speed': entry['speed'],
                    'heading': entry['heading'],
                    'FL': entry['sensors']['FL'],
                    'FR': entry['sensors']['FR'],
                    'BL': entry['sensors']['BL'],
                    'BR': entry['sensors']['BR'],
                    'hazard_score': entry['hazard_score'],
                    'ttc': entry['ttc'] if entry['ttc'] != float('inf') else 999.0,
                    'collision': 1 if entry['collision'] else 0,
                    'total_collisions': entry['total_collisions']
                }
                writer.writerow(row)
        
        return filename
    
    def get_summary_metrics(self):
        """Compute summary metrics for the simulation run"""
        if not self.telemetry_log:
            return {}
        
        total_time = self.telemetry_log[-1]['timestamp'] if self.telemetry_log else 0
        total_distance = 0
        
        # Calculate distance traveled
        for i in range(1, len(self.telemetry_log)):
            prev_pos = self.telemetry_log[i-1]['position']
            curr_pos = self.telemetry_log[i]['position']
            dx = curr_pos[0] - prev_pos[0]
            dy = curr_pos[1] - prev_pos[1]
            total_distance += (dx**2 + dy**2)**0.5
        
        avg_speed = sum(t['speed'] for t in self.telemetry_log) / len(self.telemetry_log)
        avg_hazard = self.metrics['avg_hazard_score']
        
        # Time to first collision
        time_to_first_collision = None
        for entry in self.telemetry_log:
            if entry['collision']:
                time_to_first_collision = entry['timestamp']
                break
        
        return {
            'mode': self.mode,
            'scenario': self.scenario,
            'total_time': total_time,
            'total_cycles': self.cycle_count,
            'total_collisions': self.metrics['total_collisions'],
            'total_distance': total_distance,
            'avg_speed': avg_speed,
            'avg_hazard_score': avg_hazard,
            'state_transitions': self.metrics['state_transitions'],
            'emergency_brakes': self.metrics['emergency_brakes'],
            'ttc_interventions': self.metrics['ttc_interventions'],
            'time_to_first_collision': time_to_first_collision
        }

    def get_current_state(self):
        return {
            'vehicle': self.vehicle.get_state(),
            'obstacles': self.environment.get_obstacles_as_dicts(),
            'sensor_rays': self.sensors.get_sensor_rays(
                self.vehicle.position,
                self.vehicle.heading
            ),
            'alu_state': self.alu.current_state,
            'alu_metrics': self.alu.get_metrics(),
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
        json_file = controller.save_telemetry()
        csv_file = controller.save_telemetry_csv()
        print(f"\nTelemetry saved:")
        print(f"  JSON: {json_file}")
        print(f"  CSV:  {csv_file}")
        
        # Print summary metrics
        metrics = controller.get_summary_metrics()
        print(f"\nSummary Metrics:")
        print(f"  Mode: {metrics['mode']}")
        print(f"  Scenario: {metrics['scenario']}")
        print(f"  Duration: {metrics['total_time']:.1f}s")
        print(f"  Collisions: {metrics['total_collisions']}")
        print(f"  Distance: {metrics['total_distance']:.1f}m")
        print(f"  Avg Speed: {metrics['avg_speed']:.2f} m/s")
        print(f"  Avg Hazard: {metrics['avg_hazard_score']:.3f}")
        print(f"  State Transitions: {metrics['state_transitions']}")
        print(f"  Emergency Brakes: {metrics['emergency_brakes']}")


if __name__ == '__main__':
    main()
