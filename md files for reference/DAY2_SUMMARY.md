# Day 2: Virtual Sensors Implementation ✅

## Summary

Complete virtual sensor system with raycast-based distance measurement, Gaussian noise injection, and moving-average filtering. Fully tested with physics integration and all scenarios.

## Files Created/Updated

| File | Purpose |
|------|---------|
| `sensors.py` | SensorArray class with raycast, noise, filtering |
| `config.json` | Updated with 4 complete scenarios (Corridor, Random, Intersection, Dense) |
| `test_sensors.py` | 13 unit tests for raycast, noise, filtering |
| `test_integration.py` | 3 integration tests combining physics + sensors |
| `debug_sensors.py` | Helper for debugging raycast calculations |

## Key Features Implemented

### Raycast Algorithm (`sensors.py`)
- **4-sensor array**: FL (45°), FR (-45°), BL (135°), BR (-135°) relative to car heading
- **Ray-circle intersection**: solves quadratic equation to find intersection distance
- **Multiple obstacles**: returns distance to nearest obstacle per ray
- **Max range**: clamps distances to 100 units
- **Robust**: handles no intersections, multiple hits, self-collision avoidance (t > 0.01)

### Noise Injection
- **Gaussian noise**: configurable std dev (default 3.0 units)
- **Toggle**: `sensors.set_noise_enabled(True/False)`
- **Realistic**: simulates sensor measurement error, prevents perfect sensing

### Moving-Average Filter
- **Window size**: configurable (default 5 readings)
- **Maintains history**: per-sensor deque of last N readings
- **Smoothing**: averages noisy spikes, stabilizes control input
- **Toggle**: `sensors.set_filter_enabled(True/False)`

### 4 Complete Scenarios

| Scenario | Obstacles | Type | Use Case |
|----------|-----------|------|----------|
| **Corridor** | 6 | 4 static walls + 2 end blocks | Straight-line navigation test |
| **Random** | 6 | All static, scattered | General obstacle avoidance |
| **Intersection** | 6 | 4 static + 2 moving | Dynamic obstacle evasion |
| **Dense** | 14 | Mix of static/moving | Heavy traffic simulation |

## Test Results

### Unit Tests (13/13 ✅)
```
✓ Sensor initialization
✓ Raycast with no obstacles
✓ Raycast hits obstacle
✓ Raycast multiple obstacles
✓ Sensor update cycle
✓ Noise injection (variance check)
✓ Filter smoothing
✓ Reproducibility without noise
✓ Sensor angle verification
✓ Corridor scenario load
✓ Random scenario load
✓ Intersection scenario load
✓ Dense scenario load
```

### Integration Tests (3/3 ✅)
```
✓ Physics + Sensors integration (car moves, sensors report, no collision)
✓ All scenarios load and sensor correctly
✓ Noise & filter effects visible:
  - No noise/filter: 0.00 variance
  - With noise/filter: 3.16 variance
  - Noise alone: 6.28 variance (unfiltered)
```

## How It Works

### Raycast Ray-Circle Intersection
```
Ray: p(t) = start + t * direction
Circle: |p - center| = radius

Substitute → quadratic in t:
  a*t² + b*t + c = 0

Solutions (t > 0) give intersection distances
Return minimum distance (nearest hit)
```

### Noise & Filter Pipeline
```
Raw Distance → (noise) → Noisy Reading → (filter avg) → Filtered Distance

Toggle options:
- Both off: raw raycast distance (noiseless, no lag)
- Noise only: realistic but jumpy readings
- Filter only: smooth noiseless readings (low latency)
- Both on: realistic + smooth (recommended)
```

### Sensor Array Layout
```
Car heading right (θ=0):

        BL(135°)          FL(45°)
         \                 /
          \       ^       /
           \      |      /  ← Car (blue square)
        ---+------+------+---
           /      v      \
          /               \
        BR(-135°)         FR(-45°)

Obstacles show as red circles
Sensor rays visualized as green lines (in frontend)
```

## Integration with Other Modules

### Input from Physics (`physics.py`)
- Car position (x, y)
- Car heading (θ)
- Car radius (for raycast start offset)

### Input from Obstacles (`obstacles.py`)
- Obstacle list: [(x, y, radius), ...]
- Works with static and moving obstacles

### Output for ALU (Person 2)
```python
distances = sensors.update(car_x, car_y, car_theta, obstacles_list)
# Returns dict: {'FL': 45.2, 'FR': 89.1, 'BL': 100.0, 'BR': 30.5}
# Ready for ALU decision logic
```

### Output for Logging (Person 3)
```python
readings = sensors.get_all_readings()
# Dict of SensorReading objects with:
# - sensor_name, raw_distance, filtered_distance, timestamp
# Perfect for CSV logging
```

## API Reference

### Initialize
```python
sensors = SensorArray(config['sensors'], car_radius=10)
```

### Configure
```python
sensors.set_noise_enabled(True)
sensors.set_filter_enabled(True)
```

### Update (main loop)
```python
distances = sensors.update(
    car_x=100, car_y=250, car_theta=0,
    obstacles=[(250, 250, 20), ...]
)
# Returns: {'FL': 95.2, 'FR': 87.3, 'BL': 100.0, 'BR': 42.1}
```

### Query
```python
filtered = sensors.get_sensor_readings_dict(raw=False)
raw = sensors.get_sensor_readings_dict(raw=True)
all_readings = sensors.get_all_readings()  # SensorReading objects
```

### Housekeeping
```python
sensors.reset_filters()  # Clear history for new scenario
```

## Known Behavior

- **All max_range readings**: car is far from all obstacles (common at start)
- **Noise variance**: ~3-6 units with std=3.0 (configurable in config.json)
- **Filter lag**: minimal with window=5 (0.5s at 100ms ticks)
- **No self-collision**: raycast starts at t=0.01 to avoid detecting car itself

## Next Steps (Day 3)

Person 1 will:
- Fine-tune physics parameters based on test results
- Create additional scenarios or variations
- Optimize performance if needed
- Prepare for real-time visualization

Person 2 (ALU) can now:
- Read sensor values from this module
- Implement decision logic
- Test with actual sensor data (not mock)

Person 3 (Backend) can now:
- Integrate sensors into main simulation loop
- Log sensor values to CSV
- Expose `/api/state` with sensor data

Person 4 (Frontend) can now:
- Draw sensor rays as green lines
- Display sensor values numerically
- Show raw vs filtered comparison

---

**Status**: Day 2 complete. Physics + Sensors fully functional and tested. ✅

**Files ready for integration with rest of team.**
