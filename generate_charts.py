"""
Chart Generation Tool
Generates visualization charts from telemetry CSV data
"""

import pandas as pd
import matplotlib.pyplot as plt
import os
import glob
import sys

def plot_hazard_vs_time(csv_file, output_file=None):
    """Plot hazard score over time"""
    
    df = pd.read_csv(csv_file)
    
    plt.figure(figsize=(12, 6))
    plt.plot(df['timestamp'], df['hazard_score'], linewidth=2, color='#e74c3c')
    plt.fill_between(df['timestamp'], 0, df['hazard_score'], alpha=0.3, color='#e74c3c')
    
    plt.xlabel('Time (seconds)', fontsize=12)
    plt.ylabel('Hazard Score', fontsize=12)
    plt.title('Hazard Score vs Time', fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3)
    plt.ylim(0, 1.0)
    
    # Add threshold lines
    plt.axhline(y=0.3, color='orange', linestyle='--', alpha=0.5, label='Warning')
    plt.axhline(y=0.7, color='red', linestyle='--', alpha=0.5, label='Danger')
    plt.legend()
    
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"✓ Saved: {output_file}")
    else:
        plt.show()
    
    plt.close()


def plot_speed_vs_time(csv_file, output_file=None):
    """Plot speed over time"""
    
    df = pd.read_csv(csv_file)
    
    plt.figure(figsize=(12, 6))
    plt.plot(df['timestamp'], df['speed'], linewidth=2, color='#3498db')
    
    plt.xlabel('Time (seconds)', fontsize=12)
    plt.ylabel('Speed (m/s)', fontsize=12)
    plt.title('Speed vs Time', fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3)
    
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"✓ Saved: {output_file}")
    else:
        plt.show()
    
    plt.close()


def plot_trajectory(csv_file, output_file=None):
    """Plot vehicle trajectory"""
    
    df = pd.read_csv(csv_file)
    
    plt.figure(figsize=(10, 10))
    
    # Plot trajectory colored by hazard score
    scatter = plt.scatter(df['x'], df['y'], c=df['hazard_score'], 
                         cmap='RdYlGn_r', s=10, alpha=0.6)
    
    # Mark collisions
    collisions = df[df['collision'] == 1]
    if len(collisions) > 0:
        plt.scatter(collisions['x'], collisions['y'], 
                   color='red', s=100, marker='X', 
                   edgecolors='black', linewidths=2,
                   label='Collisions', zorder=5)
    
    plt.colorbar(scatter, label='Hazard Score')
    plt.xlabel('X Position', fontsize=12)
    plt.ylabel('Y Position', fontsize=12)
    plt.title('Vehicle Trajectory', fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3)
    plt.axis('equal')
    plt.legend()
    
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"✓ Saved: {output_file}")
    else:
        plt.show()
    
    plt.close()


def plot_state_timeline(csv_file, output_file=None):
    """Plot FSM state timeline"""
    
    df = pd.read_csv(csv_file)
    
    # Map states to numeric values for plotting
    state_map = {
        'CRUISE': 0,
        'AVOID_LEFT': 1,
        'AVOID_RIGHT': 2,
        'EMERGENCY_BRAKE': 3,
        'REVERSING': 4
    }
    
    df['state_num'] = df['state'].map(state_map)
    
    plt.figure(figsize=(12, 4))
    plt.plot(df['timestamp'], df['state_num'], linewidth=2, color='#9b59b6')
    plt.fill_between(df['timestamp'], 0, df['state_num'], alpha=0.3, color='#9b59b6')
    
    plt.xlabel('Time (seconds)', fontsize=12)
    plt.ylabel('FSM State', fontsize=12)
    plt.title('State Machine Timeline', fontsize=14, fontweight='bold')
    plt.yticks(range(5), ['CRUISE', 'AVOID_LEFT', 'AVOID_RIGHT', 'EMERGENCY_BRAKE', 'REVERSING'])
    plt.grid(True, alpha=0.3, axis='x')
    
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"✓ Saved: {output_file}")
    else:
        plt.show()
    
    plt.close()


def plot_mode_comparison(comparison_csv, output_file=None):
    """Plot comparison bar chart for different modes"""
    
    df = pd.read_csv(comparison_csv)
    
    # Group by mode
    modes = df['mode'].unique()
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Mode Comparison Across All Scenarios', fontsize=16, fontweight='bold')
    
    # Collisions
    ax = axes[0, 0]
    for mode in modes:
        mode_data = df[df['mode'] == mode]
        ax.bar(mode_data['scenario'], mode_data['total_collisions'], 
               label=mode.capitalize(), alpha=0.8)
    ax.set_ylabel('Total Collisions')
    ax.set_title('Collisions by Mode')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    
    # Average Speed
    ax = axes[0, 1]
    for mode in modes:
        mode_data = df[df['mode'] == mode]
        ax.bar(mode_data['scenario'], mode_data['avg_speed'], 
               label=mode.capitalize(), alpha=0.8)
    ax.set_ylabel('Avg Speed (m/s)')
    ax.set_title('Average Speed by Mode')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    
    # Distance Traveled
    ax = axes[1, 0]
    for mode in modes:
        mode_data = df[df['mode'] == mode]
        ax.bar(mode_data['scenario'], mode_data['total_distance'], 
               label=mode.capitalize(), alpha=0.8)
    ax.set_ylabel('Distance (m)')
    ax.set_title('Distance Traveled by Mode')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    
    # Average Hazard
    ax = axes[1, 1]
    for mode in modes:
        mode_data = df[df['mode'] == mode]
        ax.bar(mode_data['scenario'], mode_data['avg_hazard_score'], 
               label=mode.capitalize(), alpha=0.8)
    ax.set_ylabel('Avg Hazard Score')
    ax.set_title('Average Hazard by Mode')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    
    if output_file:
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"✓ Saved: {output_file}")
    else:
        plt.show()
    
    plt.close()


def generate_all_charts(csv_file):
    """Generate all charts for a single telemetry file"""
    
    base_name = os.path.splitext(os.path.basename(csv_file))[0]
    output_dir = 'charts'
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\nGenerating charts for: {csv_file}")
    print("=" * 70)
    
    plot_hazard_vs_time(csv_file, f"{output_dir}/{base_name}_hazard.png")
    plot_speed_vs_time(csv_file, f"{output_dir}/{base_name}_speed.png")
    plot_trajectory(csv_file, f"{output_dir}/{base_name}_trajectory.png")
    plot_state_timeline(csv_file, f"{output_dir}/{base_name}_states.png")
    
    print("=" * 70)
    print(f"✓ All charts saved to {output_dir}/")


if __name__ == '__main__':
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python generate_charts.py <csv_file>           # Generate charts for single file")
        print("  python generate_charts.py --all                # Generate charts for all CSV files in logs/")
        print("  python generate_charts.py --comparison <csv>   # Generate mode comparison chart")
        sys.exit(1)
    
    if sys.argv[1] == '--all':
        csv_files = glob.glob('logs/telemetry_*.csv')
        if not csv_files:
            print("No CSV files found in logs/")
            sys.exit(1)
        
        for csv_file in csv_files:
            generate_all_charts(csv_file)
    
    elif sys.argv[1] == '--comparison':
        if len(sys.argv) < 3:
            print("Error: Please specify comparison CSV file")
            sys.exit(1)
        
        comparison_csv = sys.argv[2]
        if not os.path.exists(comparison_csv):
            print(f"Error: File not found: {comparison_csv}")
            sys.exit(1)
        
        output_dir = 'charts'
        os.makedirs(output_dir, exist_ok=True)
        plot_mode_comparison(comparison_csv, f"{output_dir}/mode_comparison.png")
    
    else:
        csv_file = sys.argv[1]
        if not os.path.exists(csv_file):
            print(f"Error: File not found: {csv_file}")
            sys.exit(1)
        
        generate_all_charts(csv_file)
