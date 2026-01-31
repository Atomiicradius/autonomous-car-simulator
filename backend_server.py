"""
Web Backend Server for ALU Autonomous Vehicle Simulator
Provides REST API and WebSocket for real-time simulation control and visualization
"""

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import threading
import time
import os
import glob
from backend import AutonomousVehicleController

app = Flask(__name__, static_folder='frontend', static_url_path='')
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Global controller instance
controller = None
simulation_thread = None
is_running = False


def simulation_loop():
    """Background thread for running simulation and emitting telemetry"""
    global controller, is_running
    
    while is_running and controller:
        try:
            telemetry = controller.run_cycle()
            current_state = controller.get_current_state()
            
            # Emit telemetry to all connected clients
            socketio.emit('telemetry', {
                'telemetry': telemetry,
                'state': current_state,
                'metrics': controller.metrics
            })
            
            # Sleep for control cycle time
            time.sleep(controller.dt)
            
        except Exception as e:
            print(f"Error in simulation loop: {e}")
            is_running = False
            break


@app.route('/')
def index():
    """Serve the frontend dashboard"""
    try:
        from flask import send_from_directory
        import os
        frontend_dir = os.path.join(os.path.dirname(__file__), 'frontend')
        return send_from_directory(frontend_dir, 'index.html')
    except Exception as e:
        return jsonify({'error': f'Failed to load frontend: {str(e)}'}), 500


@app.route('/api/status', methods=['GET'])
def get_status():
    """Get current simulation status"""
    if controller:
        return jsonify({
            'running': is_running,
            'mode': controller.mode,
            'scenario': controller.scenario,
            'cycle_count': controller.cycle_count,
            'metrics': controller.metrics
        })
    return jsonify({'running': False})


@app.route('/api/start', methods=['POST'])
def start_simulation():
    """Start or resume simulation"""
    global controller, simulation_thread, is_running
    
    data = request.json or {}
    mode = data.get('mode', 'normal')
    scenario = data.get('scenario', 'random')
    
    # Create new controller if needed
    if not controller or controller.mode != mode or controller.scenario != scenario:
        controller = AutonomousVehicleController(mode=mode, scenario=scenario, test_mode=False)
        controller.start_time = time.time()
    
    # Start simulation thread
    if not is_running:
        is_running = True
        simulation_thread = threading.Thread(target=simulation_loop, daemon=True)
        simulation_thread.start()
    
    return jsonify({'status': 'started', 'mode': mode, 'scenario': scenario})


@app.route('/api/pause', methods=['POST'])
def pause_simulation():
    """Pause simulation"""
    global is_running
    is_running = False
    return jsonify({'status': 'paused'})


@app.route('/api/reset', methods=['POST'])
def reset_simulation():
    """Reset simulation"""
    global controller, is_running
    
    data = request.json or {}
    mode = data.get('mode', 'normal')
    scenario = data.get('scenario', 'random')
    
    is_running = False
    time.sleep(0.2)  # Wait for thread to stop
    
    controller = AutonomousVehicleController(mode=mode, scenario=scenario, test_mode=False)
    controller.start_time = time.time()
    
    return jsonify({'status': 'reset', 'mode': mode, 'scenario': scenario})


@app.route('/api/state', methods=['GET'])
def get_current_state():
    """Get current simulation state"""
    if controller:
        return jsonify(controller.get_current_state())
    return jsonify({'error': 'No active simulation'})


@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    """Get current simulation metrics"""
    if controller:
        return jsonify(controller.get_summary_metrics())
    return jsonify({'error': 'No active simulation'})


@app.route('/api/logs', methods=['GET'])
def list_logs():
    """List available CSV log files"""
    log_files = []
    
    if os.path.exists('logs'):
        csv_files = glob.glob('logs/*.csv')
        for filepath in csv_files:
            filename = os.path.basename(filepath)
            size = os.path.getsize(filepath)
            mtime = os.path.getmtime(filepath)
            
            log_files.append({
                'filename': filename,
                'size': size,
                'modified': mtime,
                'path': filepath
            })
    
    return jsonify({'logs': log_files})


@app.route('/api/download_log/<filename>', methods=['GET'])
def download_log(filename):
    """Download a specific CSV log file"""
    filepath = os.path.join('logs', filename)
    
    if os.path.exists(filepath) and filepath.endswith('.csv'):
        return send_file(filepath, as_attachment=True)
    
    return jsonify({'error': 'File not found'}), 404


@app.route('/api/compare_modes/<scenario>', methods=['POST'])
def compare_modes(scenario):
    """Run same scenario in all 3 modes and return comparison"""
    global is_running
    
    modes = ['cautious', 'normal', 'aggressive']
    results = []
    
    for mode in modes:
        # Create controller
        temp_controller = AutonomousVehicleController(
            mode=mode,
            scenario=scenario,
            test_mode=False
        )
        
        # Run for 30 seconds
        temp_controller.run_simulation(duration=30.0)
        
        # Get metrics
        metrics = temp_controller.get_summary_metrics()
        results.append(metrics)
    
    return jsonify({
        'scenario': scenario,
        'comparison': results
    })


@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print('Client connected')
    emit('connected', {'status': 'connected'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print('Client disconnected')


if __name__ == '__main__':
    print("=" * 60)
    print("ALU Autonomous Vehicle Simulator - Web Backend")
    print("=" * 60)
    print("Server starting on http://localhost:5000")
    print("Open frontend/index.html in your browser to view the dashboard")
    print("=" * 60)
    
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
