"""
Configuration Module for ALU-Based Autonomous Vehicle
Author: ALU Engineer (Person 2)

Centralized configuration for driving modes, thresholds, and system parameters.
"""

# ============================================================================
# DRIVING MODES - Different behavioral profiles for the ALU
# ============================================================================

DRIVING_MODES = {
    'cautious': {
        'danger_threshold': 3.0,      # Distance considered dangerous (meters)
        'warning_threshold': 5.0,     # Distance to start warning (meters)
        'max_speed': 2.0,              # Maximum speed in m/s
        'ttc_threshold': 3.0,          # Time-to-collision threshold (seconds)
        'hysteresis_cycles': 5,        # Cycles before state change
    },
    'normal': {
        'danger_threshold': 2.0,
        'warning_threshold': 3.5,
        'max_speed': 3.5,
        'ttc_threshold': 2.0,
        'hysteresis_cycles': 3,
    },
    'aggressive': {
        'danger_threshold': 1.0,
        'warning_threshold': 2.0,
        'max_speed': 5.0,
        'ttc_threshold': 1.0,
        'hysteresis_cycles': 2,
    }
}

# ============================================================================
# SENSOR CONFIGURATION
# ============================================================================

SENSOR_CONFIG = {
    'max_range': 10.0,              # Maximum sensor detection range (meters)
    'num_sensors': 4,               # FL, FR, BL, BR
    'sensor_angles': {
        'FL': 45,                   # Front-Left sensor angle (degrees)
        'FR': -45,                  # Front-Right sensor angle (degrees)
        'BL': 135,                  # Back-Left sensor angle (degrees)
        'BR': -135,                 # Back-Right sensor angle (degrees)
    },
    'field_of_view': 60,            # Field of view for each sensor (degrees)
    'noise_factor': 0.05,           # Sensor noise (5% of reading)
}

# ============================================================================
# PHYSICS PARAMETERS
# ============================================================================

PHYSICS_CONFIG = {
    'acceleration': 1.0,            # m/s²
    'brake_deceleration': 2.0,      # m/s² (stronger braking)
    'friction': 0.1,                # Friction coefficient
    'vehicle_radius': 0.5,          # Vehicle collision radius (meters)
    'world_width': 20.0,            # World bounds (meters)
    'world_height': 20.0,
}

# ============================================================================
# CONTROL LOOP TIMING
# ============================================================================

CONTROL_CONFIG = {
    'cycle_time_ms': 100,           # 100ms control cycle (10 Hz)
    'simulation_duration': 60,      # Simulation duration in seconds
}

# ============================================================================
# VISUALIZATION SETTINGS
# ============================================================================

VISUAL_CONFIG = {
    'window_width': 1200,
    'window_height': 800,
    'pixels_per_meter': 30,         # Scale factor for rendering
    'fps': 60,                      # Display refresh rate
    'show_sensor_rays': True,
    'show_danger_zones': True,
}

# ============================================================================
# FSM STATES (for reference)
# ============================================================================

class VehicleState:
    """Enum-like class for vehicle states"""
    CRUISE = "CRUISE"
    AVOID_LEFT = "AVOID_LEFT"
    AVOID_RIGHT = "AVOID_RIGHT"
    EMERGENCY_BRAKE = "EMERGENCY_BRAKE"
    REVERSING = "REVERSING"

# ============================================================================
# COLOR SCHEME
# ============================================================================

COLORS = {
    'background': (20, 20, 30),
    'vehicle_cruise': (50, 200, 50),
    'vehicle_avoiding': (200, 200, 50),
    'vehicle_emergency': (200, 50, 50),
    'obstacle': (150, 150, 150),
    'sensor_safe': (50, 200, 50, 50),
    'sensor_warning': (200, 200, 50, 50),
    'sensor_danger': (200, 50, 50, 100),
    'text': (255, 255, 255),
}
