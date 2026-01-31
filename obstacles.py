"""
Obstacle classes for autonomous vehicle simulator.
Supports static and moving obstacles with collision detection.
"""

import math
from dataclasses import dataclass
from typing import List, Tuple, Dict, Any
from enum import Enum


class ObstacleType(Enum):
    """Types of obstacles."""
    STATIC = "static"
    LINEAR = "linear"       # moves back and forth on a line
    BOUNCE = "bounce"       # bounces off walls


@dataclass
class CircleObstacle:
    """Circular obstacle (simplest representation)."""
    x: float
    y: float
    radius: float
    obstacle_type: ObstacleType = ObstacleType.STATIC
    
    # For moving obstacles
    velocity: float = 0.0   # units/s (for LINEAR/BOUNCE types)
    direction_angle: float = 0.0  # radians, direction of movement
    
    # Track world bounds for bouncing
    world_width: float = 500.0
    world_height: float = 500.0
    
    def to_dict(self) -> Dict[str, float]:
        """Return dict representation."""
        return {
            'x': self.x,
            'y': self.y,
            'radius': self.radius,
            'type': self.obstacle_type.value
        }
    
    def update(self, dt: float) -> None:
        """
        Update moving obstacle position.
        
        Args:
            dt: time step in seconds
        """
        if self.obstacle_type == ObstacleType.STATIC:
            return
        
        # Move in direction_angle
        self.x += self.velocity * math.cos(self.direction_angle) * dt
        self.y += self.velocity * math.sin(self.direction_angle) * dt
        
        # Handle bouncing off walls
        if self.obstacle_type == ObstacleType.BOUNCE:
            if self.x - self.radius < 0:
                self.x = self.radius
                self.direction_angle = (math.pi - self.direction_angle) % (2 * math.pi)
            elif self.x + self.radius > self.world_width:
                self.x = self.world_width - self.radius
                self.direction_angle = (math.pi - self.direction_angle) % (2 * math.pi)
            
            if self.y - self.radius < 0:
                self.y = self.radius
                self.direction_angle = (2 * math.pi - self.direction_angle) % (2 * math.pi)
            elif self.y + self.radius > self.world_height:
                self.y = self.world_height - self.radius
                self.direction_angle = (2 * math.pi - self.direction_angle) % (2 * math.pi)
    
    def __repr__(self) -> str:
        return f"Obstacle(x={self.x:.1f}, y={self.y:.1f}, r={self.radius:.1f}, type={self.obstacle_type.value})"


class ObstacleManager:
    """Manages a set of obstacles with collision detection."""
    
    def __init__(self, world_config: Dict[str, Any]):
        """
        Initialize obstacle manager.
        
        Args:
            world_config: dict with 'world_width'/'width' and 'world_height'/'height'
        """
        self.obstacles: List[CircleObstacle] = []
        self.world_width = world_config.get('world_width', world_config.get('width', 500))
        self.world_height = world_config.get('world_height', world_config.get('height', 500))
    
    def add_obstacle(self, obstacle: CircleObstacle) -> None:
        """Add obstacle to manager."""
        obstacle.world_width = self.world_width
        obstacle.world_height = self.world_height
        self.obstacles.append(obstacle)
    
    def add_obstacles_from_list(self, obstacle_configs: List[Dict[str, Any]]) -> None:
        """
        Add multiple obstacles from list of config dicts.
        
        Each dict should have:
        - x, y, radius
        - type: "static", "linear", "bounce"
        - velocity (optional): for moving obstacles
        - direction_angle (optional): radians
        """
        for cfg in obstacle_configs:
            obs_type = ObstacleType(cfg.get('type', 'static'))
            obstacle = CircleObstacle(
                x=cfg['x'],
                y=cfg['y'],
                radius=cfg['radius'],
                obstacle_type=obs_type,
                velocity=cfg.get('velocity', 0.0),
                direction_angle=cfg.get('direction_angle', 0.0),
                world_width=self.world_width,
                world_height=self.world_height
            )
            self.add_obstacle(obstacle)
    
    def update(self, dt: float) -> None:
        """Update all moving obstacles."""
        for obs in self.obstacles:
            obs.update(dt)
    
    def get_all(self) -> List[CircleObstacle]:
        """Return all obstacles."""
        return self.obstacles
    
    def clear(self) -> None:
        """Remove all obstacles."""
        self.obstacles.clear()
    
    def check_collision_circle_circle(
        self,
        center1: Tuple[float, float],
        radius1: float,
        center2: Tuple[float, float],
        radius2: float
    ) -> bool:
        """
        Check if two circles overlap.
        
        Returns True if distance between centers < sum of radii.
        """
        dx = center1[0] - center2[0]
        dy = center1[1] - center2[1]
        dist = math.sqrt(dx * dx + dy * dy)
        return dist < (radius1 + radius2)
    
    def check_car_collision(self, car_pos: Tuple[float, float], car_radius: float) -> bool:
        """
        Check if car collides with any obstacle.
        
        Returns True if collision detected.
        """
        for obs in self.obstacles:
            if self.check_collision_circle_circle(
                car_pos,
                car_radius,
                (obs.x, obs.y),
                obs.radius
            ):
                return True
        return False
    
    def get_obstacle_tuples(self) -> List[Tuple[float, float, float]]:
        """
        Return obstacles as (x, y, radius) tuples for sensor raycast.
        
        This adapter prevents backend code from manually converting obstacles.
        
        Returns:
            list of (x, y, radius) tuples
        """
        return [(obs.x, obs.y, obs.radius) for obs in self.obstacles]
    
    def get_obstacles_as_dicts(self) -> List[Dict[str, float]]:
        """Return all obstacles as dicts (for JSON serialization)."""
        return [obs.to_dict() for obs in self.obstacles]
