"""
Sensor Subsystem Module
Author: ALU Engineer (Person 2)

Simulates proximity sensors for obstacle detection.
Implements 4-sensor array: Front-Left, Front-Right, Back-Left, Back-Right
"""

import math
import random
from config import SENSOR_CONFIG


class ProximitySensor:
    """Individual proximity sensor with configurable range and angle"""
    
    def __init__(self, name, angle, max_range=10.0, field_of_view=60):
        """
        Initialize a proximity sensor.
        
        Args:
            name (str): Sensor identifier (FL, FR, BL, BR)
            angle (float): Sensor orientation in degrees (0 = forward)
            max_range (float): Maximum detection range in meters
            field_of_view (float): Sensor's field of view in degrees
        """
        self.name = name
        self.angle = math.radians(angle)  # Convert to radians
        self.max_range = max_range
        self.fov = math.radians(field_of_view)
        self.last_reading = max_range
    
    def detect_obstacles(self, vehicle_pos, vehicle_heading, obstacles):
        """
        Detect nearest obstacle within sensor's field of view.
        
        Args:
            vehicle_pos (tuple): (x, y) vehicle position
            vehicle_heading (float): Vehicle heading in radians
            obstacles (list): List of obstacle objects with position and radius
        
        Returns:
            float: Distance to nearest obstacle (max_range if none detected)
        """
        vx, vy = vehicle_pos
        
        # Absolute sensor angle (vehicle heading + sensor offset)
        sensor_angle = vehicle_heading + self.angle
        
        min_distance = self.max_range
        
        for obstacle in obstacles:
            ox, oy = obstacle['pos']
            obstacle_radius = obstacle.get('radius', 0.5)
            
            # Vector from vehicle to obstacle
            dx = ox - vx
            dy = oy - vy
            distance = math.sqrt(dx*dx + dy*dy) - obstacle_radius
            
            # Angle to obstacle
            angle_to_obstacle = math.atan2(dy, dx)
            
            # Angular difference between sensor direction and obstacle
            angle_diff = self._normalize_angle(angle_to_obstacle - sensor_angle)
            
            # Check if obstacle is within field of view
            if abs(angle_diff) <= self.fov / 2:
                if distance < min_distance:
                    min_distance = distance
        
        # Add sensor noise for realism
        noise = random.gauss(0, SENSOR_CONFIG['noise_factor'] * min_distance)
        min_distance = max(0.0, min(min_distance + noise, self.max_range))
        
        self.last_reading = min_distance
        return min_distance
    
    def _normalize_angle(self, angle):
        """Normalize angle to [-pi, pi]"""
        while angle > math.pi:
            angle -= 2 * math.pi
        while angle < -math.pi:
            angle += 2 * math.pi
        return angle


class SensorArray:
    """
    4-Sensor proximity array for autonomous vehicle.
    
    Sensor Layout:
    - FL (Front-Left): 45° left of center
    - FR (Front-Right): 45° right of center
    - BL (Back-Left): 135° left of center
    - BR (Back-Right): 135° right of center
    """
    
    def __init__(self):
        """Initialize all four proximity sensors"""
        max_range = SENSOR_CONFIG['max_range']
        fov = SENSOR_CONFIG['field_of_view']
        angles = SENSOR_CONFIG['sensor_angles']
        
        self.sensors = {
            'FL': ProximitySensor('FL', angles['FL'], max_range, fov),
            'FR': ProximitySensor('FR', angles['FR'], max_range, fov),
            'BL': ProximitySensor('BL', angles['BL'], max_range, fov),
            'BR': ProximitySensor('BR', angles['BR'], max_range, fov),
        }
    
    def scan(self, vehicle_pos, vehicle_heading, obstacles):
        """
        Perform a complete sensor scan of all obstacles.
        
        Args:
            vehicle_pos (tuple): (x, y) vehicle position
            vehicle_heading (float): Vehicle heading in radians
            obstacles (list): List of obstacles in environment
        
        Returns:
            dict: Sensor readings {FL: distance, FR: distance, ...}
        """
        readings = {}
        for name, sensor in self.sensors.items():
            readings[name] = sensor.detect_obstacles(
                vehicle_pos, vehicle_heading, obstacles
            )
        return readings
    
    def get_sensor_rays(self, vehicle_pos, vehicle_heading):
        """
        Get visualization data for sensor rays.
        
        Returns:
            list: List of sensor ray endpoints for visualization
        """
        rays = []
        for name, sensor in self.sensors.items():
            sensor_angle = vehicle_heading + sensor.angle
            endpoint_x = vehicle_pos[0] + sensor.last_reading * math.cos(sensor_angle)
            endpoint_y = vehicle_pos[1] + sensor.last_reading * math.sin(sensor_angle)
            
            rays.append({
                'name': name,
                'start': vehicle_pos,
                'end': (endpoint_x, endpoint_y),
                'distance': sensor.last_reading,
                'angle': sensor_angle,
            })
        
        return rays
