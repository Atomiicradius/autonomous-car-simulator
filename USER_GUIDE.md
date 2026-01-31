# User Guide - ALU-Based Autonomous Vehicle Simulator

## Quick Start

### 1. Installation

Ensure you have Python 3.8+ installed, then install dependencies:

```bash
cd "c:\Users\Samarth Naik\OneDrive\Documents\ADLD project\organised-codebase"
pip install -r requirements.txt
```

### 2. Start the Backend Server

```bash
python backend_server.py
```

The server will start on `http://localhost:5000`

### 3. Open the Frontend Dashboard

Open your web browser and navigate to:
- `http://localhost:5000` (if server serves static files)
- OR open `frontend/index.html` directly in your browser

---

## Using the Dashboard

### Control Panel

**Driving Mode Selector:**
- 🐢 **Cautious**: Conservative driving, large safety margins, slower speed
- 🚗 **Normal**: Balanced approach, moderate safety margins
- 🏎️ **Aggressive**: Fast driving, minimal safety margins, higher collision risk

**Scenario Selector:**
- 🛣️ **Corridor**: Narrow passage with walls
- 🎲 **Random**: Sparse random obstacles
- 🚦 **Intersection**: T-junction layout
- 🧱 **Dense**: Heavy obstacle environment

**Control Buttons:**
- ▶️ **Start**: Begin simulation
- ⏸️ **Pause**: Pause simulation
- 🔄 **Reset**: Reset to initial state

### Live Simulation Canvas

The canvas shows:
- **Blue rectangle**: The autonomous vehicle
- **Red circles**: Obstacles (static and moving)
- **Green lines**: Sensor rays showing detection range
- **Yellow/Red indicators**: Hazard zones

### Real-Time Metrics Panel

**Current State:**
- **FSM State**: Current decision state (CRUISE, AVOID_LEFT, AVOID_RIGHT, EMERGENCY_BRAKE, REVERSING)
- **Speed**: Current velocity in m/s
- **Hazard Score**: Danger level (0.0 = safe, 1.0 = critical)
- **Time-To-Collision**: Estimated seconds until collision
- **Position**: (x, y) coordinates
- **Heading**: Direction in degrees

**Session Statistics:**
- **Total Collisions**: Number of obstacle hits
- **State Transitions**: How many times FSM changed state
- **Emergency Brakes**: Count of TTC-triggered emergency stops
- **Cycle Count**: Number of 100ms control cycles executed

---

## Running Experiments

### Single Simulation Run

Run a specific configuration from command line:

```bash
# Normal mode, random scenario, 60 seconds
python backend.py --mode normal --scenario random --duration 60 --save

# Cautious mode, corridor scenario, 30 seconds
python backend.py --mode cautious --scenario corridor --duration 30 --save
```

The `--save` flag creates:
- JSON telemetry file in `logs/`
- CSV data file in `logs/`
- Printed summary metrics

### Full Test Matrix

Run all 12 configurations (4 scenarios × 3 modes):

```bash
python run_test_matrix.py
```

This will:
- Run each configuration for 60 seconds
- Save CSV logs for all runs
- Generate comparison results table
- Print summary statistics

**⚠️ Warning**: Takes ~12 minutes to complete

---

## Understanding the Results

### Interpreting Metrics

**Collisions:**
- Lower is better
- Cautious mode typically has 0-1 collisions
- Aggressive mode may have 3-5 collisions

**Average Speed:**
- Higher means more efficient navigation
- Cautious: ~1.5-1.8 m/s
- Normal: ~2.0-2.2 m/s
- Aggressive: ~2.5-2.8 m/s

**Average Hazard Score:**
- Lower is safer
- Cautious: ~0.15-0.25
- Normal: ~0.20-0.30
- Aggressive: ~0.30-0.45

**State Transitions:**
- More transitions = more reactive behavior
- Fewer transitions = smoother driving

### Safety vs Efficiency Tradeoff

The three modes demonstrate a clear tradeoff:

| Mode | Safety | Efficiency | Use Case |
|------|--------|------------|----------|
| Cautious | ⭐⭐⭐⭐⭐ | ⭐⭐ | Hospital transport, elderly passengers |
| Normal | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | General urban driving |
| Aggressive | ⭐⭐ | ⭐⭐⭐⭐⭐ | Emergency response, time-critical |

---

## Analyzing CSV Data

CSV files are saved in `logs/` directory with format:
```
telemetry_<mode>_<scenario>_<timestamp>.csv
```

### Loading in Python

```python
import pandas as pd

df = pd.read_csv('logs/telemetry_normal_random_20260201_003000.csv')

# Plot hazard score over time
import matplotlib.pyplot as plt
plt.plot(df['timestamp'], df['hazard_score'])
plt.xlabel('Time (s)')
plt.ylabel('Hazard Score')
plt.title('Hazard Score vs Time')
plt.show()
```

### Loading in Excel

1. Open Excel
2. File → Open → Select CSV file
3. Data will be automatically parsed into columns
4. Create charts using Insert → Chart

---

## Troubleshooting

### Backend server won't start

**Error:** `Address already in use`

**Solution:** Another process is using port 5000. Kill it or change port:
```python
# In backend_server.py, change last line:
socketio.run(app, host='0.0.0.0', port=5001, debug=False)
```

### Frontend shows "Disconnected"

**Possible causes:**
1. Backend server not running → Start `backend_server.py`
2. CORS issue → Check browser console for errors
3. Wrong URL → Ensure using `http://localhost:5000`

### Simulation runs too fast/slow

The simulation runs at real-time (100ms per cycle). If performance is poor:
1. Close other applications
2. Reduce scenario complexity
3. Check CPU usage

### No CSV files generated

Ensure you're using the `--save` flag:
```bash
python backend.py --mode normal --scenario random --duration 10 --save
```

Or call from Python:
```python
controller.save_telemetry_csv()
```

---

## Advanced Usage

### Custom Scenarios

Edit `config.json` to add custom obstacle layouts:

```json
{
  "scenarios": {
    "my_scenario": {
      "obstacles": [
        {"x": 100, "y": 100, "radius": 20, "type": "static"},
        {"x": 200, "y": 200, "radius": 15, "type": "moving", "vx": 1.0, "vy": 0.5}
      ]
    }
  }
}
```

### Tuning Driving Modes

Edit `config.py` to adjust mode thresholds:

```python
DRIVING_MODES = {
    'my_mode': {
        'danger_threshold': 2.5,
        'warning_threshold': 4.0,
        'max_speed': 3.0,
        'ttc_threshold': 2.5,
        'hysteresis_cycles': 4
    }
}
```

---

## Tips for Best Results

1. **Start with Cautious mode** to understand baseline safe behavior
2. **Use Corridor scenario** for controlled testing
3. **Run multiple trials** to account for randomness
4. **Compare modes on same scenario** for fair evaluation
5. **Save all data** for later analysis

---

## Support

For issues or questions:
1. Check README.md for project overview
2. Review ARCHITECTURE.md for technical details
3. See API.md for endpoint documentation
4. Check test files for usage examples
