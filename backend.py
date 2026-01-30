"""
Backend Control Loop
Author: ALU Engineer (Person 2)

Main control system integrating sensors, ALU decision logic, and physics.
Runs at 100ms control cycle (10 Hz).
"""

import time
import json
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
        return {
            'vehicle': self.vehicle.get_state(),
            'obstacles': self.environment.get_obstacles(),
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
        controller.save_telemetry()


if __name__ == '__main__':
    main()
