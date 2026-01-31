"""
Real-Time Visualization System
Author: ALU Engineer (Person 2)

Pygame-based visualization for live monitoring of the autonomous vehicle.
NOTE: pygame is imported ONLY when this module is run directly
"""

import math
import sys


def run_visualizer(mode='normal', scenario='random'):
    """Run the visualizer - pygame is imported here to avoid blocking on import"""
    import pygame
    from backend import AutonomousVehicleController
    from config import VISUAL_CONFIG, COLORS, VehicleState, DRIVING_MODES
    
    class VehicleVisualizer:
        """
        Real-time visualization of autonomous vehicle system.
        """
        
        def __init__(self, mode='normal', scenario='random'):
            """Initialize visualization system"""
            pygame.init()
            pygame.font.init()
            
            self.width = VISUAL_CONFIG['window_width']
            self.height = VISUAL_CONFIG['window_height']
            self.screen = pygame.display.set_mode((self.width, self.height))
            pygame.display.set_caption('ALU-Based Autonomous Vehicle Simulator')
            
            self.clock = pygame.time.Clock()
            self.fps = VISUAL_CONFIG['fps']
            self.scale = VISUAL_CONFIG['pixels_per_meter']
            
            # Fonts
            self.font_large = pygame.font.SysFont('Arial', 24, bold=True)
            self.font_medium = pygame.font.SysFont('Arial', 18)
            self.font_small = pygame.font.SysFont('Arial', 14)
            
            # Controller
            self.controller = AutonomousVehicleController(mode=mode, scenario=scenario)
            self.running = True
            self.paused = False
            
            # Visualization area (left side)
            self.vis_area = pygame.Rect(0, 0, 800, 800)
            self.vis_offset = (50, 50)
        
        def world_to_screen(self, world_pos):
            """Convert world coordinates to screen coordinates"""
            x, y = world_pos
            screen_x = self.vis_offset[0] + x * self.scale
            screen_y = self.vis_offset[1] + y * self.scale
            return (int(screen_x), int(screen_y))
        
        def draw_vehicle(self, vehicle_state):
            """Draw the vehicle as a triangle"""
            pos = vehicle_state['position']
            heading = vehicle_state['heading']
            
            # Vehicle triangle points
            size = 15
            points = [
                (size, 0),      # Front
                (-size, size/2),   # Back-left
                (-size, -size/2),  # Back-right
            ]
            
            # Rotate and translate points
            cos_h = math.cos(heading)
            sin_h = math.sin(heading)
            screen_pos = self.world_to_screen(pos)
            
            rotated_points = []
            for px, py in points:
                rx = px * cos_h - py * sin_h
                ry = px * sin_h + py * cos_h
                rotated_points.append((screen_pos[0] + rx, screen_pos[1] + ry))
            
            # Color based on state
            state = self.controller.alu.current_state
            if state == VehicleState.CRUISE:
                color = COLORS['vehicle_cruise']
            elif state == VehicleState.EMERGENCY_BRAKE or state == VehicleState.REVERSING:
                color = COLORS['vehicle_emergency']
            else:
                color = COLORS['vehicle_avoiding']
            
            pygame.draw.polygon(self.screen, color, rotated_points)
            pygame.draw.circle(self.screen, (255, 255, 255), screen_pos, 3)
        
        def draw_obstacles(self, obstacles):
            """Draw all obstacles"""
            for obstacle in obstacles:
                pos = self.world_to_screen(obstacle['pos'])
                radius = int(obstacle['radius'] * self.scale)
                pygame.draw.circle(self.screen, COLORS['obstacle'], pos, radius)
        
        def draw_sensors(self, sensor_rays):
            """Draw sensor rays and detection zones"""
            if not VISUAL_CONFIG['show_sensor_rays']:
                return
            
            danger_threshold = DRIVING_MODES[self.controller.mode]['danger_threshold']
            warning_threshold = DRIVING_MODES[self.controller.mode]['warning_threshold']
            
            for ray in sensor_rays:
                start = self.world_to_screen(ray['start'])
                end = self.world_to_screen(ray['end'])
                distance = ray['distance']
                
                # Color based on danger level
                if distance < danger_threshold:
                    color = (200, 50, 50)
                elif distance < warning_threshold:
                    color = (200, 200, 50)
                else:
                    color = (50, 200, 50)
                
                # Draw line and endpoint
                pygame.draw.line(self.screen, color, start, end, 2)
                pygame.draw.circle(self.screen, color, end, 4)
        
        def draw_metrics_panel(self, state_data):
            """Draw metrics dashboard on the right side"""
            panel_x = 820
            panel_y = 20
            
            vehicle = state_data['vehicle']
            alu_metrics = state_data['alu_metrics']
            
            # Title
            title = self.font_large.render('METRICS DASHBOARD', True, COLORS['text'])
            self.screen.blit(title, (panel_x, panel_y))
            
            y_offset = panel_y + 40
            line_height = 30
            
            # FSM State
            state_text = f"State: {alu_metrics['state']}"
            state_color = self._get_state_color(alu_metrics['state'])
            state_surface = self.font_medium.render(state_text, True, state_color)
            self.screen.blit(state_surface, (panel_x, y_offset))
            y_offset += line_height
            
            # Mode
            mode_text = f"Mode: {alu_metrics['mode'].upper()}"
            mode_surface = self.font_medium.render(mode_text, True, COLORS['text'])
            self.screen.blit(mode_surface, (panel_x, y_offset))
            y_offset += line_height + 10
            
            # Separator
            pygame.draw.line(self.screen, (100, 100, 100), 
                            (panel_x, y_offset), (panel_x + 300, y_offset), 1)
            y_offset += 20
            
            # Speed
            speed_text = f"Speed: {vehicle['speed']:.2f} m/s"
            speed_surface = self.font_medium.render(speed_text, True, COLORS['text'])
            self.screen.blit(speed_surface, (panel_x, y_offset))
            y_offset += line_height
            
            # Hazard Score
            hazard = alu_metrics['hazard_score']
            hazard_text = f"Hazard: {hazard:.2f}"
            hazard_color = self._get_hazard_color(hazard)
            hazard_surface = self.font_medium.render(hazard_text, True, hazard_color)
            self.screen.blit(hazard_surface, (panel_x, y_offset))
            
            # Hazard bar
            bar_x = panel_x + 150
            bar_width = 150
            bar_height = 20
            pygame.draw.rect(self.screen, (50, 50, 50), 
                            (bar_x, y_offset, bar_width, bar_height))
            pygame.draw.rect(self.screen, hazard_color, 
                            (bar_x, y_offset, int(bar_width * hazard), bar_height))
            y_offset += line_height
            
            # TTC
            ttc = alu_metrics['ttc']
            ttc_display = f"{ttc:.1f}s" if ttc < 99 else "∞"
            ttc_text = f"TTC: {ttc_display}"
            ttc_surface = self.font_medium.render(ttc_text, True, COLORS['text'])
            self.screen.blit(ttc_surface, (panel_x, y_offset))
            y_offset += line_height + 10
            
            # Separator
            pygame.draw.line(self.screen, (100, 100, 100), 
                            (panel_x, y_offset), (panel_x + 300, y_offset), 1)
            y_offset += 20
            
            # Collisions
            collision_text = f"Collisions: {vehicle['collisions']}"
            collision_surface = self.font_medium.render(collision_text, True, (255, 100, 100))
            self.screen.blit(collision_surface, (panel_x, y_offset))
            y_offset += line_height
            
            # Metrics
            metrics = self.controller.metrics
            transitions_text = f"State Transitions: {metrics['state_transitions']}"
            transitions_surface = self.font_small.render(transitions_text, True, COLORS['text'])
            self.screen.blit(transitions_surface, (panel_x, y_offset))
            y_offset += line_height - 5
            
            emergency_text = f"Emergency Brakes: {metrics['emergency_brakes']}"
            emergency_surface = self.font_small.render(emergency_text, True, COLORS['text'])
            self.screen.blit(emergency_surface, (panel_x, y_offset))
            y_offset += line_height - 5
            
            # Instructions
            y_offset = 600
            instructions = [
                "CONTROLS:",
                "SPACE - Pause/Resume",
                "1/2/3 - Cautious/Normal/Aggressive",
                "R - Reset Simulation",
                "ESC - Exit",
            ]
            for instruction in instructions:
                inst_surface = self.font_small.render(instruction, True, (150, 150, 150))
                self.screen.blit(inst_surface, (panel_x, y_offset))
                y_offset += 25
        
        def _get_state_color(self, state):
            """Get color for FSM state"""
            if state == VehicleState.CRUISE:
                return (50, 255, 50)
            elif state in [VehicleState.AVOID_LEFT, VehicleState.AVOID_RIGHT]:
                return (255, 255, 50)
            else:
                return (255, 50, 50)
        
        def _get_hazard_color(self, hazard):
            """Get color for hazard level"""
            if hazard < 0.3:
                return (50, 255, 50)
            elif hazard < 0.7:
                return (255, 255, 50)
            else:
                return (255, 50, 50)
        
        def handle_input(self):
            """Handle keyboard input"""
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    
                    elif event.key == pygame.K_SPACE:
                        self.paused = not self.paused
                    
                    elif event.key == pygame.K_1:
                        self.controller.alu.set_mode('cautious')
                        self.controller.mode = 'cautious'
                    
                    elif event.key == pygame.K_2:
                        self.controller.alu.set_mode('normal')
                        self.controller.mode = 'normal'
                    
                    elif event.key == pygame.K_3:
                        self.controller.alu.set_mode('aggressive')
                        self.controller.mode = 'aggressive'
                    
                    elif event.key == pygame.K_r:
                        # Reset simulation
                        scenario = self.controller.scenario
                        mode = self.controller.mode
                        self.controller = AutonomousVehicleController(mode=mode, scenario=scenario)
        
        def run(self):
            """Main visualization loop"""
            while self.running:
                self.handle_input()
                
                # Run simulation step if not paused
                if not self.paused:
                    self.controller.run_cycle()
                
                # Clear screen
                self.screen.fill(COLORS['background'])
                
                # Get current state
                state_data = self.controller.get_current_state()
                
                # Draw world
                self.draw_obstacles(state_data['obstacles'])
                self.draw_sensors(state_data['sensor_rays'])
                self.draw_vehicle(state_data['vehicle'])
                
                # Draw UI
                self.draw_metrics_panel(state_data)
                
                # Update display
                pygame.display.flip()
                self.clock.tick(self.fps)
            
            pygame.quit()
    
    # Run the visualizer
    visualizer = VehicleVisualizer(mode=mode, scenario=scenario)
    visualizer.run()


def main():
    """Command-line interface for visualization"""
    import argparse
    
    parser = argparse.ArgumentParser(description='ALU Vehicle Visualizer')
    parser.add_argument('--mode', choices=['cautious', 'normal', 'aggressive'],
                       default='normal', help='Initial driving mode')
    parser.add_argument('--scenario', choices=['empty', 'random', 'corridor', 'intersection', 'dense'],
                       default='random', help='Obstacle scenario')
    
    args = parser.parse_args()
    run_visualizer(mode=args.mode, scenario=args.scenario)


if __name__ == '__main__':
    main()
