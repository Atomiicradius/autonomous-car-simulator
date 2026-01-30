"""
Virtual sensor system for autonomous vehicle simulator.
Implements raycast-based proximity sensing with optional noise and filtering.
"""

import math
import random
from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Any
from collections import deque


@dataclass
class SensorReading:
    """A single sensor reading with raw and filtered values."""
    sensor_name: str
    raw_distance: float
    filtered_distance: float
    timestamp: float


class SensorArray:
    """
    4-sensor array (FL, FR, BL, BR) with raycast-based distance measurement.
    
    Sensors are positioned relative to car:
    - FL (Front-Left):  45° relative to heading
    - FR (Front-Right): -45° relative to heading
    - BL (Back-Left):   135° relative to heading
    - BR (Back-Right):  -135° relative to heading
    """
    
    def __init__(self, config: Dict[str, Any], car_radius: float):
        """
        Initialize sensor array.
        
        Args:
            config: dict with keys:
                - max_range: max raycast distance
                - cone_angle: cone width in degrees (unused for now, for future enhancement)
                - positions: list of dicts with 'name' and 'angle_offset'
                - noise_std: Gaussian noise std dev (0 = no noise)
                - filter_size: moving average window size
            car_radius: radius of car (sensors positioned at edge)
        """
        self.max_range = config['max_range']
        self.cone_angle = config['cone_angle']
        self.car_radius = car_radius
        self.noise_std = config.get('noise_std', 0.0)
        self.filter_size = config.get('filter_size', 5)
        
        # Parse sensor positions from config
        self.sensor_offsets: Dict[str, float] = {}  # name -> angle_offset (radians)
        for sensor_cfg in config.get('positions', []):
            name = sensor_cfg['name']
            angle_deg = sensor_cfg['angle_offset']
            angle_rad = math.radians(angle_deg)
            self.sensor_offsets[name] = angle_rad
        
        # History for moving average filter (name -> deque of readings)
        self.filter_history: Dict[str, deque] = {
            name: deque(maxlen=self.filter_size)
            for name in self.sensor_offsets.keys()
        }
        
        # Latest readings
        self.latest_readings: Dict[str, SensorReading] = {}
        self.timestamp = 0.0
        self.noise_enabled = False
        self.filter_enabled = False
    
    def set_noise_enabled(self, enabled: bool) -> None:
        """Enable/disable noise injection."""
        self.noise_enabled = enabled
    
    def set_filter_enabled(self, enabled: bool) -> None:
        """Enable/disable moving average filter."""
        self.filter_enabled = enabled
    
    def raycast(
        self,
        car_x: float,
        car_y: float,
        car_theta: float,
        obstacles: List[Tuple[float, float, float]]
    ) -> Dict[str, float]:
        """
        Perform raycast from car position to all obstacles.
        
        Args:
            car_x, car_y: car center position
            car_theta: car heading (radians)
            obstacles: list of (obs_x, obs_y, obs_radius) tuples
        
        Returns:
            dict mapping sensor name -> distance to nearest obstacle
        """
        readings = {}
        
        for sensor_name, angle_offset in self.sensor_offsets.items():
            # Sensor ray direction (absolute heading)
            ray_angle = car_theta + angle_offset
            ray_dx = math.cos(ray_angle)
            ray_dy = math.sin(ray_angle)
            
            # Find nearest obstacle hit by this ray
            min_distance = self.max_range
            
            for obs_x, obs_y, obs_radius in obstacles:
                dist = self._raycast_circle(
                    car_x, car_y, ray_dx, ray_dy,
                    obs_x, obs_y, obs_radius
                )
                
                if dist < min_distance:
                    min_distance = dist
            
            readings[sensor_name] = min_distance
        
        return readings
    
    def _raycast_circle(
        self,
        ray_start_x: float,
        ray_start_y: float,
        ray_dx: float,
        ray_dy: float,
        circle_x: float,
        circle_y: float,
        circle_radius: float
    ) -> float:
        """
        Check if ray hits circle and return distance to hit point.
        
        Ray parametric form: p(t) = (start_x, start_y) + t * (dx, dy)
        Circle: (x - circle_x)^2 + (y - circle_y)^2 = r^2
        
        Substitute ray into circle equation and solve for t.
        
        Returns:
            distance to intersection (self.max_range if no hit)
        """
        # Vector from ray start to circle center
        fx = ray_start_x - circle_x
        fy = ray_start_y - circle_y
        
        # Quadratic equation: (dx*t + fx)^2 + (dy*t + fy)^2 = r^2
        a = ray_dx * ray_dx + ray_dy * ray_dy
        
        # Guard against degenerate ray (zero-length direction vector)
        if a < 1e-9:
            return self.max_range
        
        b = 2.0 * (fx * ray_dx + fy * ray_dy)
        c = fx * fx + fy * fy - circle_radius * circle_radius
        
        discriminant = b * b - 4 * a * c
        
        # No intersection
        if discriminant < 0:
            return self.max_range
        
        # Solve for t
        sqrt_disc = math.sqrt(discriminant)
        t1 = (-b - sqrt_disc) / (2 * a)
        t2 = (-b + sqrt_disc) / (2 * a)
        
        # Find closest intersection in front of ray (t > 0)
        valid_t = [t for t in [t1, t2] if t > 0.01]  # 0.01 to avoid self-collision
        
        if not valid_t:
            return self.max_range
        
        closest_t = min(valid_t)
        distance = closest_t
        
        # Clamp to max range
        return min(distance, self.max_range)
    
    def update(
        self,
        car_x: float,
        car_y: float,
        car_theta: float,
        obstacles: List[Tuple[float, float, float]],
        timestamp: float = None
    ) -> Dict[str, float]:
        """
        Update all sensors in one call.
        
        Args:
            car_x, car_y: car position
            car_theta: car heading
            obstacles: list of (x, y, radius) tuples
            timestamp: optional timestamp for logging
        
        Returns:
            dict mapping sensor name -> filtered distance
        """
        self.timestamp = timestamp or self.timestamp + 0.1
        
        # Raycast to get raw distances
        raw_distances = self.raycast(car_x, car_y, car_theta, obstacles)
        
        filtered_distances = {}
        
        for sensor_name, raw_dist in raw_distances.items():
            # Apply noise if enabled
            if self.noise_enabled and self.noise_std > 0:
                noisy_dist = raw_dist + random.gauss(0, self.noise_std)
                # Clamp to valid range
                noisy_dist = max(0, min(noisy_dist, self.max_range))
            else:
                noisy_dist = raw_dist
            
            # Apply filter if enabled
            if self.filter_enabled:
                self.filter_history[sensor_name].append(noisy_dist)
                filtered_dist = sum(self.filter_history[sensor_name]) / len(self.filter_history[sensor_name])
            else:
                filtered_dist = noisy_dist
            
            # Store reading
            reading = SensorReading(
                sensor_name=sensor_name,
                raw_distance=raw_dist,
                filtered_distance=filtered_dist,
                timestamp=self.timestamp
            )
            self.latest_readings[sensor_name] = reading
            filtered_distances[sensor_name] = filtered_dist
        
        return filtered_distances
    
    def get_all_readings(self) -> Dict[str, SensorReading]:
        """Return all latest readings."""
        return self.latest_readings
    
    def get_sensor_readings_dict(self, raw: bool = False) -> Dict[str, float]:
        """
        Get all sensor values as simple dict.
        
        Args:
            raw: if True, return raw distances; else return filtered
        
        Returns:
            dict mapping sensor name -> distance
        """
        result = {}
        for name, reading in self.latest_readings.items():
            result[name] = reading.raw_distance if raw else reading.filtered_distance
        return result
    
    def reset_filters(self) -> None:
        """Clear filter history (for new scenario/reset)."""
        for history in self.filter_history.values():
            history.clear()
    
    def __repr__(self) -> str:
        readings = self.get_sensor_readings_dict(raw=False)
        return f"SensorArray({readings})"
