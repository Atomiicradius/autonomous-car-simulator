"""
Physics Engine Module
Author: ALU Engineer (Person 2)

Handles vehicle dynamics, collision detection, and environment simulation.
"""

import math
import random
from config import PHYSICS_CONFIG


class Vehicle:
    """
    2D vehicle with basic physics simulation.
    
    Attributes:
        position: (x, y) in meters
        velocity: (vx, vy) in m/s
        heading: angle in radians (0 = east, π/2 = north)
        speed: scalar speed in m/s
    """
    
    def __init__(self, x=10.0, y=10.0, heading=0.0, theta=None, config=None):
        """Initialize vehicle at given position and heading
        
        Args:
            x, y: Position in meters
            heading: Angle in radians (also accepts 'theta' for backward compatibility)
            config: Optional config dict from tests (ignored but accepted)
        """
        # Support both 'heading' and 'theta' parameter names for compatibility
        if theta is not None:
            heading = theta
            
        self.position = [x, y]
        self.velocity = [0.0, 0.0]
        self.heading = heading
        self.speed = 0.0
        self.radius = PHYSICS_CONFIG['vehicle_radius']
        
        # Compatibility attributes for Day 1 tests
        self.x = x
        self.y = y
        self.theta = heading
        self.v = 0.0
        
        # Physics parameters
        self.max_acceleration = PHYSICS_CONFIG['acceleration']
        self.max_brake = PHYSICS_CONFIG['brake_deceleration']
        self.friction = PHYSICS_CONFIG['friction']
        
        # Collision tracking
        self.collision_count = 0
        self.in_collision = False
    
    def apply_control(self, control_output, dt, max_speed):
        """
        Apply control commands to update vehicle physics.
        
        Args:
            control_output (dict): {throttle, steering, brake}
            dt (float): Time step in seconds
            max_speed (float): Maximum allowed speed
        """
        throttle = control_output.get('throttle', 0.0)
        steering = control_output.get('steering', 0.0)
        brake = control_output.get('brake', 0.0)
        
        # Calculate acceleration
        if brake > 0:
            # Braking
            accel = -self.max_brake * brake
        else:
            # Throttle (positive or negative for reverse)
            accel = self.max_acceleration * throttle
        
        # Apply friction
        if abs(self.speed) > 0.01:
            friction_force = -self.friction * (self.speed / abs(self.speed))
        else:
            friction_force = 0
            if abs(accel) < self.friction:
                accel = 0
        
        # Update speed
        self.speed += (accel + friction_force) * dt
        self.speed = max(-max_speed * 0.5, min(self.speed, max_speed))
        
        # Update heading based on steering (only when moving)
        if abs(self.speed) > 0.1:
            turn_rate = steering * 2.0  # radians per second
            self.heading += turn_rate * dt
            self.heading = self._normalize_angle(self.heading)
        
        # Update velocity components
        self.velocity[0] = self.speed * math.cos(self.heading)
        self.velocity[1] = self.speed * math.sin(self.heading)
        
        # Update position
        self.position[0] += self.velocity[0] * dt
        self.position[1] += self.velocity[1] * dt
        
        # Boundary checking
        self._enforce_boundaries()
    
    def _normalize_angle(self, angle):
        """Normalize angle to [0, 2π]"""
        while angle < 0:
            angle += 2 * math.pi
        while angle >= 2 * math.pi:
            angle -= 2 * math.pi
        return angle
    
    def _enforce_boundaries(self):
        """Keep vehicle within world bounds"""
        max_x = PHYSICS_CONFIG['world_width']
        max_y = PHYSICS_CONFIG['world_height']
        
        self.position[0] = max(self.radius, min(self.position[0], max_x - self.radius))
        self.position[1] = max(self.radius, min(self.position[1], max_y - self.radius))
    
    def check_collision(self, obstacles):
        """
        Check for collisions with obstacles.
        
        Args:
            obstacles (list): List of obstacle dictionaries
        
        Returns:
            bool: True if collision detected
        """
        was_in_collision = self.in_collision
        self.in_collision = False
        
        for obstacle in obstacles:
            ox, oy = obstacle['pos']
            obstacle_radius = obstacle.get('radius', 0.5)
            
            dx = self.position[0] - ox
            dy = self.position[1] - oy
            distance = math.sqrt(dx*dx + dy*dy)
            
            if distance < (self.radius + obstacle_radius):
                self.in_collision = True
                if not was_in_collision:
                    self.collision_count += 1
                return True
        
        return False
    
    def get_state(self):
        """Get current vehicle state"""
        return {
            'position': tuple(self.position),
            'velocity': tuple(self.velocity),
            'heading': self.heading,
            'speed': self.speed,
            'collisions': self.collision_count,
        }
    
    # ========================================================================
    # BACKWARD COMPATIBILITY METHODS (for Day 1-2 tests)
    # ========================================================================
    def accelerate(self, accel_magnitude, dt=0.1, max_speed=3.0):
        """Accelerate in current heading direction (backward compatible method)"""
        control = {'throttle': accel_magnitude, 'steering': 0.0, 'brake': 0.0}
        self.apply_control(control, dt, max_speed)
        # Update compatibility attributes
        self.x = self.position[0]
        self.y = self.position[1]
        self.v = self.speed
        self.theta = self.heading
    
    def turn(self, steering_angle, dt=0.1, max_speed=3.0):
        """Turn at current speed (backward compatible method)"""
        control = {'throttle': 0.0, 'steering': steering_angle, 'brake': 0.0}
        self.apply_control(control, dt, max_speed)
        # Update compatibility attributes
        self.x = self.position[0]
        self.y = self.position[1]
        self.v = self.speed
        self.theta = self.heading
    
    def brake(self, brake_magnitude, dt=0.1, max_speed=3.0):
        """Apply braking (backward compatible method)"""
        control = {'throttle': 0.0, 'steering': 0.0, 'brake': brake_magnitude}
        self.apply_control(control, dt, max_speed)
        # Update compatibility attributes
        self.x = self.position[0]
        self.y = self.position[1]
        self.v = self.speed
        self.theta = self.heading


class Environment:
    """
    Simulates the physical environment with obstacles.
    """
    
    def __init__(self, scenario='random'):
        """
        Initialize environment with obstacles.
        
        Args:
            scenario (str): Obstacle layout - 'random', 'corridor', 'intersection', 'dense'
        """
        self.scenario = scenario
        self.obstacles = []
        self.world_width = PHYSICS_CONFIG['world_width']
        self.world_height = PHYSICS_CONFIG['world_height']
        
        self._generate_obstacles(scenario)
    
    def _generate_obstacles(self, scenario):
        """Generate obstacles based on scenario type"""
        if scenario == 'corridor':
            # Narrow corridor with obstacles
            for i in range(5):
                # Left wall obstacles
                self.obstacles.append({
                    'pos': (5 + i * 2, 5),
                    'radius': 0.8,
                })
                # Right wall obstacles
                self.obstacles.append({
                    'pos': (5 + i * 2, 15),
                    'radius': 0.8,
                })
        
        elif scenario == 'intersection':
            # T-intersection layout
            # Vertical road obstacles
            for y in range(5, 16, 2):
                self.obstacles.append({'pos': (8, y), 'radius': 0.7})
                self.obstacles.append({'pos': (12, y), 'radius': 0.7})
            
            # Horizontal road obstacles
            for x in range(5, 16, 2):
                self.obstacles.append({'pos': (x, 8), 'radius': 0.7})
                self.obstacles.append({'pos': (x, 12), 'radius': 0.7})
        
        elif scenario == 'dense':
            # Dense random obstacles
            for _ in range(20):
                self.obstacles.append({
                    'pos': (random.uniform(3, 17), random.uniform(3, 17)),
                    'radius': random.uniform(0.3, 0.8),
                })
        
        elif scenario == 'random':
            # Sparse random obstacles
            for _ in range(8):
                self.obstacles.append({
                    'pos': (random.uniform(3, 17), random.uniform(3, 17)),
                    'radius': random.uniform(0.4, 1.0),
                })
        
        elif scenario == 'empty':
            # No obstacles - for testing cruise mode
            pass
    
    def get_obstacles(self):
        """Get all obstacles in environment"""
        return self.obstacles
    
    def add_obstacle(self, x, y, radius=0.5):
        """Dynamically add an obstacle"""
        self.obstacles.append({'pos': (x, y), 'radius': radius})
    
    def remove_obstacle(self, index):
        """Remove obstacle by index"""
        if 0 <= index < len(self.obstacles):
            self.obstacles.pop(index)


# ============================================================================
# COMPATIBILITY LAYER
# ============================================================================
# For backward compatibility with Day 1-2 tests that expect Car class
Car = Vehicle

# CarState dataclass for tests expecting state representation
from dataclasses import dataclass
from typing import Dict

@dataclass
class CarState:
    """Immutable state snapshot of the car."""
    x: float
    y: float
    theta: float
    v: float
    
    def to_dict(self) -> Dict[str, float]:
        return {
            'x': self.x,
            'y': self.y,
            'theta': self.theta,
            'v': self.v
        }

