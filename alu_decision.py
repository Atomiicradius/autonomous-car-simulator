"""
ALU Decision Logic Module
Author: ALU Engineer (Person 2)

Core decision-making system implementing:
- 5-State Finite State Machine (FSM)
- Hazard score calculation
- Time-To-Collision (TTC) prediction
- Hysteresis for state stability
- Mode-based threshold configuration
"""

import math
from config import VehicleState, DRIVING_MODES


class ALUDecisionEngine:
    """
    Custom ALU-based decision engine for autonomous vehicle control.
    
    This is the heart of the vehicle's intelligence, processing sensor inputs
    and generating state decisions based on a Finite State Machine.
    """
    
    def __init__(self, mode='normal'):
        """
        Initialize the ALU Decision Engine.
        
        Args:
            mode (str): Driving mode - 'cautious', 'normal', or 'aggressive'
        """
        self.mode = mode
        self.config = DRIVING_MODES[mode]
        
        # Current state
        self.current_state = VehicleState.CRUISE
        
        # Hysteresis tracking
        self.state_candidate = VehicleState.CRUISE
        self.state_hold_count = 0
        self.hysteresis_threshold = self.config['hysteresis_cycles']
        
        # Metrics
        self.hazard_score = 0.0
        self.ttc = float('inf')
        self.state_history = []
        
    def set_mode(self, mode):
        """Change driving mode dynamically"""
        if mode in DRIVING_MODES:
            self.mode = mode
            self.config = DRIVING_MODES[mode]
            self.hysteresis_threshold = self.config['hysteresis_cycles']
    
    def calculate_hazard_score(self, sensor_readings):
        """
        Calculate normalized hazard score from sensor readings.
        
        Hazard score is computed as the maximum danger across all sensors,
        normalized to range [0.0, 1.0] where:
        - 0.0 = No danger (all obstacles beyond warning threshold)
        - 1.0 = Maximum danger (obstacle at or below danger threshold)
        
        Args:
            sensor_readings (dict): Dictionary with keys FL, FR, BL, BR
                                   containing distance readings
        
        Returns:
            float: Hazard score in range [0.0, 1.0]
        """
        danger_threshold = self.config['danger_threshold']
        warning_threshold = self.config['warning_threshold']
        
        max_danger = 0.0
        
        for sensor_name, distance in sensor_readings.items():
            if distance <= danger_threshold:
                # Critical danger zone
                danger_value = 1.0
            elif distance <= warning_threshold:
                # Warning zone - linear interpolation
                danger_value = (warning_threshold - distance) / \
                             (warning_threshold - danger_threshold)
            else:
                # Safe zone
                danger_value = 0.0
            
            max_danger = max(max_danger, danger_value)
        
        self.hazard_score = max_danger
        return self.hazard_score
    
    def calculate_ttc(self, front_distance, current_speed):
        """
        Calculate Time-To-Collision (TTC) for predictive braking.
        
        TTC = distance / speed
        
        This is the WOW feature - predictive safety instead of just reactive.
        
        Args:
            front_distance (float): Minimum distance to front obstacles
            current_speed (float): Current vehicle speed (m/s)
        
        Returns:
            float: Time to collision in seconds (inf if speed is 0)
        """
        if current_speed < 0.01:  # Essentially stopped
            self.ttc = float('inf')
        else:
            self.ttc = front_distance / current_speed
        
        return self.ttc
    
    def determine_next_state(self, sensor_readings, current_speed):
        """
        Core FSM logic - determine next vehicle state based on inputs.
        
        State Transition Logic:
        1. Check TTC for emergency intervention
        2. Evaluate sensor readings for obstacles
        3. Apply state-specific transition rules
        4. Use hysteresis to prevent oscillations
        
        Args:
            sensor_readings (dict): Sensor distances {FL, FR, BL, BR}
            current_speed (float): Current vehicle speed
        
        Returns:
            str: Next state from VehicleState enum
        """
        FL = sensor_readings.get('FL', float('inf'))
        FR = sensor_readings.get('FR', float('inf'))
        BL = sensor_readings.get('BL', float('inf'))
        BR = sensor_readings.get('BR', float('inf'))
        
        # Calculate metrics
        front_distance = min(FL, FR)
        self.calculate_hazard_score(sensor_readings)
        self.calculate_ttc(front_distance, current_speed)
        
        danger_threshold = self.config['danger_threshold']
        ttc_threshold = self.config['ttc_threshold']
        
        # =====================================================================
        # EMERGENCY TTC CHECK - Highest Priority
        # =====================================================================
        if self.ttc < ttc_threshold and current_speed > 0.5:
            return VehicleState.EMERGENCY_BRAKE
        
        # =====================================================================
        # FSM STATE TRANSITIONS
        # =====================================================================
        
        # --- EMERGENCY_BRAKE State ---
        if self.current_state == VehicleState.EMERGENCY_BRAKE:
            if front_distance > danger_threshold * 1.5:
                # Safe to resume
                return VehicleState.CRUISE
            elif current_speed < 0.1:
                # Stopped, need to reverse
                return VehicleState.REVERSING
            else:
                return VehicleState.EMERGENCY_BRAKE
        
        # --- REVERSING State ---
        elif self.current_state == VehicleState.REVERSING:
            back_distance = min(BL, BR)
            if back_distance < danger_threshold:
                # Can't reverse further
                return VehicleState.EMERGENCY_BRAKE
            elif front_distance > danger_threshold * 2:
                # Cleared the obstacle
                return VehicleState.CRUISE
            else:
                return VehicleState.REVERSING
        
        # --- AVOID_LEFT State ---
        elif self.current_state == VehicleState.AVOID_LEFT:
            if FL > danger_threshold * 1.5 and FR > danger_threshold * 1.5:
                # Obstacle avoided
                return VehicleState.CRUISE
            elif FR < danger_threshold:
                # Right side now blocked
                return VehicleState.AVOID_RIGHT
            else:
                return VehicleState.AVOID_LEFT
        
        # --- AVOID_RIGHT State ---
        elif self.current_state == VehicleState.AVOID_RIGHT:
            if FL > danger_threshold * 1.5 and FR > danger_threshold * 1.5:
                # Obstacle avoided
                return VehicleState.CRUISE
            elif FL < danger_threshold:
                # Left side now blocked
                return VehicleState.AVOID_LEFT
            else:
                return VehicleState.AVOID_RIGHT
        
        # --- CRUISE State (Default) ---
        else:
            # Check for obstacles requiring action
            if front_distance < danger_threshold:
                # Both sides blocked
                if FL < danger_threshold and FR < danger_threshold:
                    return VehicleState.EMERGENCY_BRAKE
                # Left side blocked more
                elif FL < FR:
                    return VehicleState.AVOID_RIGHT
                # Right side blocked more
                else:
                    return VehicleState.AVOID_LEFT
            else:
                return VehicleState.CRUISE
    
    def update_state(self, sensor_readings, current_speed):
        """
        Update state with hysteresis to prevent rapid oscillations.
        
        Hysteresis mechanism:
        - State candidate must be stable for N cycles before transition
        - Prevents chattering between states with noisy sensors
        
        Args:
            sensor_readings (dict): Sensor data
            current_speed (float): Current speed
        
        Returns:
            str: Active state after hysteresis logic
        """
        # Determine what state the FSM wants to transition to
        desired_state = self.determine_next_state(sensor_readings, current_speed)
        
        # Hysteresis logic
        if desired_state == self.state_candidate:
            self.state_hold_count += 1
        else:
            # New candidate state detected
            self.state_candidate = desired_state
            self.state_hold_count = 1
        
        # Check if we've held the candidate state long enough
        if self.state_hold_count >= self.hysteresis_threshold:
            self.current_state = self.state_candidate
        
        # Record state history
        self.state_history.append(self.current_state)
        
        return self.current_state
    
    def get_control_output(self, state):
        """
        Convert FSM state to vehicle control commands.
        
        Args:
            state (str): Current vehicle state
        
        Returns:
            dict: Control commands {throttle, steering, brake}
                 throttle: -1.0 (reverse) to 1.0 (forward)
                 steering: -1.0 (left) to 1.0 (right)
                 brake: 0.0 to 1.0
        """
        if state == VehicleState.CRUISE:
            return {'throttle': 1.0, 'steering': 0.0, 'brake': 0.0}
        
        elif state == VehicleState.AVOID_LEFT:
            return {'throttle': 0.6, 'steering': -0.8, 'brake': 0.0}
        
        elif state == VehicleState.AVOID_RIGHT:
            return {'throttle': 0.6, 'steering': 0.8, 'brake': 0.0}
        
        elif state == VehicleState.EMERGENCY_BRAKE:
            return {'throttle': 0.0, 'steering': 0.0, 'brake': 1.0}
        
        elif state == VehicleState.REVERSING:
            return {'throttle': -0.5, 'steering': 0.0, 'brake': 0.0}
        
        else:
            # Fallback - emergency brake
            return {'throttle': 0.0, 'steering': 0.0, 'brake': 1.0}
    
    def get_metrics(self):
        """Get current decision metrics for monitoring"""
        return {
            'state': self.current_state,
            'hazard_score': self.hazard_score,
            'ttc': self.ttc,
            'mode': self.mode,
            'state_stability': self.state_hold_count,
        }
    
    def reset(self):
        """Reset the ALU to initial state"""
        self.current_state = VehicleState.CRUISE
        self.state_candidate = VehicleState.CRUISE
        self.state_hold_count = 0
        self.hazard_score = 0.0
        self.ttc = float('inf')
        self.state_history = []
