# ALU-Based Autonomous Vehicle Simulator

A real-time simulation of a self-driving car that uses a custom decision-making ALU (Arithmetic Logic Unit) to navigate around obstacles, with quantitative performance analysis across different driving modes.

## 🎯 Project Overview

This project demonstrates:
- **Custom ALU design** for IoT microcontroller decision logic
- **5-state finite state machine** for autonomous navigation
- **Virtual proximity sensors** with noise injection and filtering
- **Physics-based car kinematics** with realistic collision detection
- **Performance analysis** across 3 driving modes (Cautious, Normal, Aggressive)
- **4 scenario environments** (Corridor, Random, Intersection, Dense Traffic)

## ✨ Key Features

### Physics Engine
- Realistic car kinematics (acceleration, turning, friction, inertia)
- Boundary collision with velocity/heading reflection
- Static and moving obstacles with circle-based collision detection

### Virtual Sensor System
- 4-sensor array with directional raycast detection
- Configurable range (100 units default) and cone angles
- Optional Gaussian noise injection (realistic sensor error)
- Moving-average filter for signal smoothing

### Decision Logic (ALU)
- Hazard-based risk assessment from sensor inputs
- Time-to-collision (TTC) prediction for emergency braking
- Configurable thresholds for safety vs. speed tradeoff
- Hysteresis to prevent control oscillation

### Testing & Validation
- 30+ unit tests covering physics, sensors, and integration
- Integration tests validating full system behavior
- CSV logging of all simulation data
- Performance metrics (collisions, distance, avg speed, hazard score)

## 🏗️ Architecture

```
Frontend (Web Dashboard)
    ↓
Backend (Flask API) ← physics.py, sensors.py, obstacles.py, alu.py
    ↓
Data Layer (CSV Logs) ← metrics, analysis
```

## 📋 Requirements

- Python 3.8+
- No external dependencies for core simulation (pure Python)
- Optional: Flask + Flask-CORS for backend API (Day 3)
- Optional: numpy for advanced analysis (Day 4)

```bash
pip install flask flask-cors numpy
```

## 🚀 Quick Start

### 1. Verify Installation
```bash
python test_physics.py      # 12 tests
python test_sensors.py      # 14 tests
python test_integration.py  # 3 tests
python test_adapter.py      # 1 test
```

Expected output: **30/30 PASS** ✅

### 2. Run Physics Simulation
```bash
python manual_test.py
```

Shows car moving through Corridor scenario for 100 timesteps with sensor readings.

### 3. Inspect Configuration
```bash
cat config.json
```

Parameters for world, car physics, sensors, driving modes, and scenarios.

## 📁 File Structure

| File | Purpose |
|------|---------|
| `physics.py` | Car kinematics, movement, boundary handling |
| `obstacles.py` | Obstacle management, collision detection |
| `sensors.py` | Raycast-based proximity sensing, noise, filtering |
| `config.json` | All simulation parameters and scenarios |
| `test_*.py` | Unit and integration tests |
| `debug_*.py` | Debugging utilities |
| `docs/` | Documentation (Architecture, API, etc.) |

## 🎮 Scenarios

### Corridor
- **Purpose**: Straight-line navigation test
- **Layout**: 6 obstacles forming narrow walls
- **Difficulty**: Easy (just go straight)

### Random
- **Purpose**: General obstacle avoidance
- **Layout**: 6 obstacles at random positions
- **Difficulty**: Medium (unpredictable patterns)

### Intersection
- **Purpose**: Dynamic obstacle evasion
- **Layout**: 4 static obstacles + 2 moving obstacles
- **Difficulty**: Hard (moving targets)

### Dense
- **Purpose**: Heavy traffic simulation
- **Layout**: 14 obstacles (mix of static/moving)
- **Difficulty**: Hardest (crowded environment)

## 🧠 Driving Modes

| Mode | Danger Threshold | Behavior | Result |
|------|------------------|----------|--------|
| **Cautious** | 30 units | Early reaction, large safety margin | 0-1 collisions, slower (1.5-1.8 m/s) |
| **Normal** | 15 units | Balanced approach | 1-2 collisions, medium (2.0-2.2 m/s) |
| **Aggressive** | 10 units | Close navigation, prioritize speed | 3-5 collisions, faster (2.5-2.8 m/s) |

## 🧪 Testing

### Run All Tests
```bash
python test_physics.py      # Core physics
python test_sensors.py      # Virtual sensors
python test_integration.py  # Full system
python test_adapter.py      # Integration API
```

### Test Coverage
- **Physics**: Car movement, turning, braking, friction, collisions, boundaries
- **Sensors**: Raycast, noise injection, filtering, touching obstacles
- **Integration**: Physics + sensors working together across all scenarios
- **Adapter**: Clean integration point for backend

### Example Test Output
```
RUNNING DAY 1 PHYSICS TESTS
============================================================
✓ Car initialization test passed
✓ Forward movement test passed (moved 0.9 units)
✓ Backward movement test passed (moved 0.5 units)
...
RESULTS: 12 passed, 0 failed
```

## 📊 Performance Metrics

The simulator logs:
- Timestamp, car position (x, y), heading, velocity
- Sensor readings (raw and filtered) for all 4 directions
- ALU decision and current state
- Collision events
- Hazard score (0-100%)

Example CSV output:
```
timestamp,x,y,theta,v,FL_raw,FL_filtered,FR_raw,FR_filtered,...,collisions,hazard
0.0,50.0,250.0,0.0,0.0,100.0,100.0,100.0,100.0,...,0,0.0
0.1,50.1,250.0,0.0,0.98,100.0,100.0,100.0,100.0,...,0,0.0
...
```

## 🔌 API Integration (Day 3)

Backend will expose:
```python
GET  /api/state          # Current car state + sensors
POST /api/reset          # Reset simulation
POST /api/set_mode/<m>   # Change driving mode
GET  /api/metrics        # Performance stats
GET  /api/logs           # List CSV logs
```

## 🛠️ Development Status

- [x] Day 1: Physics engine + collision detection
- [x] Day 2: Virtual sensors + noise/filtering
- [ ] Day 3: Backend API + data logging
- [ ] Day 4: Frontend visualization + analysis
- [ ] Day 5: Full integration + testing + presentation

## 📚 Documentation

- [DAY1_SUMMARY.md](docs/DAY1_SUMMARY.md) - Physics implementation details
- [DAY2_SUMMARY.md](docs/DAY2_SUMMARY.md) - Sensor system and raycast algorithm
- [IMPROVEMENTS_SUMMARY.md](docs/IMPROVEMENTS_SUMMARY.md) - 5 critical improvements
- [FINAL_STATUS.md](docs/FINAL_STATUS.md) - Project readiness assessment

## 🔍 Key Implementation Details

### Raycast Sensor Algorithm
- Ray-circle intersection using quadratic equation
- Parametric ray: `p(t) = start + t * direction`
- Returns distance to nearest obstacle
- Defends against self-collision (t > 0.01)

### State Machine (5 States)
```
CRUISE → AVOID_LEFT/RIGHT → EMERGENCY_BRAKE → REVERSING → CRUISE
```
- Hysteresis prevents oscillation
- TTC-based predictive braking
- Mode-specific thresholds

### Physics
- Kinematic model with velocity/acceleration/friction
- Inelastic boundary bouncing with heading reflection
- Configurable max speed limits and turn rates

## 🐛 Troubleshooting

**Tests failing?**
```bash
python -m pytest test_physics.py -v
```

**Sensor readings all max_range?**
- Check obstacle positions in config.json
- Verify car position is in world bounds

**Car gets stuck?**
- Try "Aggressive" mode (higher thresholds)
- Verify world is large enough (default 500×500)

## 📝 Contributing

1. Run tests to ensure no regressions: `python test_*.py`
2. Add tests for new features
3. Update config.json if adding scenarios
4. Document changes in a comment

## 📄 License

MIT License - See LICENSE file

## 👤 Author

Atomiicradius (2026)

---

**Project Status**: Days 1-2 Complete ✅ | Ready for Days 3-5 Integration

For detailed technical implementation, see [docs/](docs/) folder.
A simulation environment for autonomous vehicle development and testing with realistic physics and traffic scenarios
