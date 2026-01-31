"""
Car physics engine for autonomous vehicle simulator.
Handles kinematics, acceleration, turning, and boundary conditions.
"""

import math
import json
from dataclasses import dataclass
from typing import Tuple, Dict, Any


@dataclass
class CarState:
    """Immutable state snapshot of the car."""
    x: float
    y: float
    theta: float  # heading angle in radians [0, 2π)
    v: float     # forward velocity in units/s
    
    def to_dict(self) -> Dict[str, float]:
        return {
            'x': self.x,
            'y': self.y,
            'theta': self.theta,
            'v': self.v
        }


class Car:
    """
    Kinematic car model with friction and boundary handling.
    
    Coordinate system:
    - Origin (0, 0) at bottom-left
    - X increases rightward
    - Y increases upward
    - Theta: 0 = rightward (+X), π/2 = upward (+Y), π = leftward, 3π/2 = downward
    """
    
    def __init__(self, x: float, y: float, theta: float, config: Dict[str, Any]):
        """
        Initialize car at position (x, y) with heading theta.
        
        Args:
            x, y: initial position
            theta: initial heading in radians
            config: dict with keys:
                - max_forward_speed
                - max_reverse_speed
                - acceleration
                - friction
                - turn_rate_per_second
                - car_radius
                - width, height (for boundary, or world_width/world_height)
        """
        self.x = x
        self.y = y
        self.theta = theta
        self.v = 0.0  # velocity (forward if positive)
        
        # Physics parameters
        self.max_forward_speed = config['max_forward_speed']
        self.max_reverse_speed = config['max_reverse_speed']
        self.acceleration = config['acceleration']
        self.friction = config['friction']
        self.turn_rate = config['turn_rate_per_second']  # rad/s
        self.car_radius = config['car_radius']
        # Handle both 'width'/'height' and 'world_width'/'world_height'
        self.world_width = config.get('world_width', config.get('width', 500))
        self.world_height = config.get('world_height', config.get('height', 500))
        
        self.collision_count = 0
    
    def accelerate(self, magnitude: float) -> None:
        """
        Apply throttle/acceleration.
        
        Args:
            magnitude: 1.0 = max forward accel, -1.0 = max reverse accel
        """
        self.v += self.acceleration * magnitude
        # Clamp to max speeds
        if self.v > 0:
            self.v = min(self.v, self.max_forward_speed)
        else:
            self.v = max(self.v, -self.max_reverse_speed)
    
    def brake(self) -> None:
        """Immediate stop (zero velocity)."""
        self.v = 0.0
    
    def turn(self, direction: float) -> None:
        """
        Change heading (turn left/right).
        
        Args:
            direction: 1.0 = max left turn, -1.0 = max right turn
        """
        self.theta += self.turn_rate * direction
        # Normalize theta to [0, 2π)
        self.theta = self.theta % (2 * math.pi)
    
    def update(self, dt: float) -> None:
        """
        Update car state: kinematics + friction + boundaries.
        
        Args:
            dt: time step in seconds (typically 0.1)
        """
        # Kinematics: update position based on velocity and heading
        self.x += self.v * math.cos(self.theta) * dt
        self.y += self.v * math.sin(self.theta) * dt
        
        # Apply friction
        self.v *= (1.0 - self.friction * dt)
        
        # Boundary conditions: bounce off walls
        self._handle_boundaries()
    
    def _handle_boundaries(self) -> None:
        """Bounce car off world boundaries, flipping both velocity and heading."""
        # Left/Right walls: flip velocity and heading angle (reflect across vertical axis)
        if self.x - self.car_radius < 0:
            self.x = self.car_radius
            self.v *= -0.5  # Inelastic bounce
            self.theta = (math.pi - self.theta) % (2 * math.pi)  # Reflect heading
        elif self.x + self.car_radius > self.world_width:
            self.x = self.world_width - self.car_radius
            self.v *= -0.5
            self.theta = (math.pi - self.theta) % (2 * math.pi)  # Reflect heading
        
        # Top/Bottom walls: flip velocity and heading angle (reflect across horizontal axis)
        if self.y - self.car_radius < 0:
            self.y = self.car_radius
            self.v *= -0.5
            self.theta = (2 * math.pi - self.theta) % (2 * math.pi)  # Reflect heading
        elif self.y + self.car_radius > self.world_height:
            self.y = self.world_height - self.car_radius
            self.v *= -0.5
            self.theta = (2 * math.pi - self.theta) % (2 * math.pi)  # Reflect heading
    
    def get_state(self) -> CarState:
        """Return current state."""
        return CarState(self.x, self.y, self.theta, self.v)
    
    def get_position(self) -> Tuple[float, float]:
        """Return (x, y) position."""
        return (self.x, self.y)
    
    def get_heading(self) -> float:
        """Return heading angle in radians."""
        return self.theta
    
    def get_velocity(self) -> float:
        """Return forward velocity."""
        return self.v
    
    def increment_collision(self) -> None:
        """Called when collision is detected."""
        self.collision_count += 1
    
    def reset_collisions(self) -> None:
        """Reset collision counter."""
        self.collision_count = 0
    
    def __repr__(self) -> str:
        return f"Car(x={self.x:.1f}, y={self.y:.1f}, θ={self.theta:.2f}, v={self.v:.1f})"


# ============================================================================
# ENVIRONMENT CLASS for ALU Backend Compatibility
# ============================================================================
class Environment:
    """
    Simulates the physical environment with obstacles.
    Used by ALU backend for scenario simulation.
    """
    
    def __init__(self, scenario='random', world_width=500, world_height=500):
        """Initialize environment with obstacles from scenario"""
        self.world_width = world_width
        self.world_height = world_height
        self.obstacles = []
        self._generate_obstacles(scenario)
    
    def _generate_obstacles(self, scenario):
        """Generate obstacles based on scenario type"""
        if scenario == 'corridor':
            # Narrow corridor with obstacles on sides
            self.obstacles = [
                {'pos': (100, 150), 'radius': 30},
                {'pos': (200, 350), 'radius': 30},
                {'pos': (300, 150), 'radius': 30},
                {'pos': (400, 350), 'radius': 30},
            ]
        elif scenario == 'random':
            # Random obstacle placement
            import random
            self.obstacles = [
                {'pos': (random.randint(50, 450), random.randint(50, 450)), 'radius': 25}
                for _ in range(6)
            ]
        elif scenario == 'intersection':
            # 4-way intersection
            self.obstacles = [
                {'pos': (250, 100), 'radius': 30},
                {'pos': (150, 250), 'radius': 30},
                {'pos': (350, 250), 'radius': 30},
                {'pos': (250, 400), 'radius': 30},
            ]
        elif scenario == 'dense':
            # Heavy obstacle density
            import random
            self.obstacles = [
                {'pos': (random.randint(50, 450), random.randint(50, 450)), 'radius': 20}
                for _ in range(14)
            ]
        else:
            # Default empty
            self.obstacles = []
    
    def get_obstacles(self):
        """Return list of obstacles"""
        return self.obstacles
    
    def add_obstacle(self, x, y, radius=20):
        """Add an obstacle to the environment"""
        self.obstacles.append({'pos': (x, y), 'radius': radius})
    
    def remove_obstacle(self, index):
        """Remove obstacle by index"""
        if 0 <= index < len(self.obstacles):
            self.obstacles.pop(index)


# ============================================================================
# BACKWARD COMPATIBILITY ALIASES
# ============================================================================
# For ALU backend that imports Vehicle instead of Car
Vehicle = Car

