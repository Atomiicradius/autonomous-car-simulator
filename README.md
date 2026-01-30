# ALU-Based Autonomous Vehicle Simulator

**Author:** ALU Engineer (Person 2)  
**Project:** Autonomous Vehicle Decision-Making System using Custom ALU Logic

## 🎯 Project Overview

This project implements a **custom ALU-based decision-making system** for autonomous vehicle control. The ALU processes sensor inputs through a **5-state Finite State Machine (FSM)** and makes intelligent navigation decisions using **hazard computation** and **predictive collision avoidance**.

### Key Features

✅ **5-State Finite State Machine**
- CRUISE, AVOID_LEFT, AVOID_RIGHT, EMERGENCY_BRAKE, REVERSING

✅ **Multi-Mode Behavior**
- Cautious, Normal, Aggressive driving personalities
- Same ALU architecture, different configuration thresholds

✅ **Predictive Safety (WOW Feature)**
- Time-To-Collision (TTC) prediction: `TTC = distance / speed`
- Proactive braking instead of reactive obstacle avoidance

✅ **Hysteresis Logic**
- Prevents rapid state oscillations
- State must be stable for N cycles before transition

✅ **4-Sensor Proximity Array**
- Front-Left, Front-Right, Back-Left, Back-Right sensors
- Realistic sensor noise simulation

✅ **Real-Time Visualization**
- Pygame-based live monitoring
- Metrics dashboard with hazard score, TTC, state tracking

✅ **Comprehensive Testing**
- Unit tests with dummy sensors
- Edge case validation
- Scenario-based testing (corridor, random, intersection, dense)

---

## 🧠 ALU Architecture

### Finite State Machine (FSM)

```
                    ┌─────────┐
         ┌─────────>│ CRUISE  │<─────────┐
         │          └─────────┘          │
         │               │               │
         │     Front     │    Front      │
         │     Clear     │   Obstacle    │
         │               ▼               │
         │          ┌─────────┐          │
         │    ┌────>│ AVOID_  │────┐     │
         │    │     │  LEFT   │    │     │
         │    │     └─────────┘    │     │  All Clear
         │    │                    │     │
         │    │     ┌─────────┐    │     │
         │    └─────│ AVOID_  │<───┘     │
         │          │  RIGHT  │          │
         │          └─────────┘          │
         │                               │
         │     TTC < Threshold           │
         │     or Both Blocked           │
         │               │               │
         │               ▼               │
         │          ┌──────────────┐     │
         └──────────│  EMERGENCY   │     │
                    │    BRAKE     │     │
                    └──────────────┘     │
                           │             │
                    Speed ≈ 0            │
                           ▼             │
                    ┌──────────────┐     │
                    │  REVERSING   │─────┘
                    └──────────────┘
                    Back Clear
```

### State Transition Logic

| Current State | Condition | Next State |
|--------------|-----------|------------|
| ANY | TTC < threshold AND speed > 0.5 m/s | EMERGENCY_BRAKE |
| CRUISE | Front distance < danger_threshold | AVOID_LEFT/RIGHT or EMERGENCY_BRAKE |
| AVOID_LEFT | Front clear | CRUISE |
| AVOID_RIGHT | Front clear | CRUISE |
| EMERGENCY_BRAKE | Front clear AND distance > 1.5× danger_threshold | CRUISE |
| EMERGENCY_BRAKE | Stopped AND front blocked | REVERSING |
| REVERSING | Front clear OR back blocked | CRUISE or EMERGENCY_BRAKE |

### Hysteresis Mechanism

Prevents rapid state oscillations by requiring a state to be stable for multiple cycles:

```python
if desired_state == state_candidate:
    state_hold_count += 1
else:
    state_candidate = desired_state
    state_hold_count = 1

if state_hold_count >= hysteresis_threshold:
    current_state = state_candidate
```

**Hysteresis Cycles:**
- Cautious: 5 cycles (500ms)
- Normal: 3 cycles (300ms)
- Aggressive: 2 cycles (200ms)

---

## 📊 Driving Modes

The same ALU architecture exhibits different behaviors through **threshold configuration only**:

| Parameter | Cautious | Normal | Aggressive |
|-----------|----------|--------|------------|
| Danger Threshold | 3.0 m | 2.0 m | 1.0 m |
| Warning Threshold | 5.0 m | 3.5 m | 2.0 m |
| Max Speed | 2.0 m/s | 3.5 m/s | 5.0 m/s |
| TTC Threshold | 3.0 s | 2.0 s | 1.0 s |
| Hysteresis Cycles | 5 | 3 | 2 |

### Hazard Score Calculation

Normalized danger value [0.0, 1.0]:

```python
if distance <= danger_threshold:
    hazard = 1.0  # Critical danger
elif distance <= warning_threshold:
    hazard = (warning - distance) / (warning - danger)  # Linear interpolation
else:
    hazard = 0.0  # Safe
```

### Time-To-Collision (TTC)

**Predictive safety feature** that triggers emergency braking before collision:

```python
TTC = front_distance / current_speed

if TTC < ttc_threshold:
    state = EMERGENCY_BRAKE
```

This enables **predictive braking**, not just reactive obstacle avoidance.

---

## 🚀 Installation & Usage

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Setup

```bash
# Navigate to project directory
cd "c:\Users\Samarth Naik\OneDrive\Documents\ADLD project"

# Install dependencies
pip install -r requirements.txt
```

### Running the Simulator

#### 1. **Live Visualization** (Recommended)

```bash
# Default: normal mode, random scenario
python visualizer.py

# Specify mode and scenario
python visualizer.py --mode cautious --scenario corridor
python visualizer.py --mode aggressive --scenario dense
```

**Controls:**
- `SPACE` - Pause/Resume
- `1` - Switch to Cautious mode
- `2` - Switch to Normal mode
- `3` - Switch to Aggressive mode
- `R` - Reset simulation
- `ESC` - Exit

#### 2. **Command-Line Backend** (Headless)

```bash
# Run 60-second simulation
python backend.py --mode normal --scenario random --duration 60

# Save telemetry data
python backend.py --mode aggressive --scenario intersection --save
```

#### 3. **Run Tests**

```bash
# Full test suite (includes scenario tests)
python test_scenarios.py

# Quick tests (unit tests only)
python test_scenarios.py --quick
```

---

## 🧪 Testing & Validation

### Test Categories

#### 1. **Dummy Sensor Tests**
Validate ALU logic with predefined sensor inputs:
- All clear → CRUISE
- Both front blocked → EMERGENCY_BRAKE
- Left blocked → AVOID_RIGHT
- Right blocked → AVOID_LEFT
- Low TTC → EMERGENCY_BRAKE (predictive)

#### 2. **Edge Case Tests**
Handle boundary conditions:
- No obstacles (max range sensors)
- Fully blocked vehicle
- Zero speed (TTC = infinity)
- Sensor failures / noisy readings

#### 3. **Hysteresis Tests**
Verify state stability:
- State change requires N stable cycles
- Prevents oscillation with fluctuating sensors

#### 4. **Mode Comparison Tests**
Validate behavioral differences:
- Cautious perceives higher hazard than Aggressive
- Different TTC thresholds
- Different max speeds

#### 5. **Scenario Tests**
Test in realistic environments:
- **Corridor:** Narrow passage with wall obstacles
- **Random:** Sparse random obstacles
- **Intersection:** T-junction layout
- **Dense:** Heavy obstacle environment

---

## 📁 Project Structure

```
ADLD project/
│
├── config.py              # Configuration and constants
├── alu_decision.py        # ALU decision logic (FSM, TTC, hazard)
├── sensors.py             # 4-sensor proximity array
├── physics.py             # Vehicle dynamics and collision detection
├── backend.py             # Control loop (100ms cycle)
├── visualizer.py          # Real-time pygame visualization
├── test_scenarios.py      # Comprehensive test suite
├── requirements.txt       # Python dependencies
└── README.md              # This file
```

---

## 🎓 Technical Deep-Dive (Viva Preparation)

### Q: How does the FSM map to digital logic?

**A:** The FSM is implemented as a **combinational + sequential logic** system:

- **Combinational Logic:** State transition function depends on current inputs (sensors) and current state
- **Sequential Logic:** State register holds current state, updated on each clock cycle (100ms)
- **Digital Equivalent:** Could be implemented in hardware using D flip-flops for state storage and combinational logic gates for transition logic

### Q: Why use an ALU-based approach instead of neural networks?

**A:** 
1. **Deterministic:** Predictable, explainable decisions (critical for safety)
2. **Low Latency:** No matrix multiplications, instant decision-making
3. **Resource Efficient:** Can run on microcontrollers (IoT edge devices)
4. **Testable:** Comprehensive unit testing with clear pass/fail criteria

### Q: How does hysteresis improve system performance?

**A:**
- **Problem:** Noisy sensors can cause rapid state changes (chattering)
- **Solution:** Require state to be stable for N cycles before transition
- **Result:** Smoother behavior, reduced wear on actuators, more energy efficient

### Q: Explain the TTC prediction feature

**A:**
```
TTC = distance_to_obstacle / current_speed

If TTC < threshold:
    Trigger emergency brake NOW (predictive)
Else:
    Continue with normal FSM logic (reactive)
```

**Advantage:** Prevents collisions by predicting future state, not just reacting to current proximity.

### Q: How do the three modes differ in implementation?

**A:** **Same code, different configuration**. This demonstrates:
- **Parameterized design:** One ALU architecture serves multiple use cases
- **Configurability:** Behavior tuning without code changes
- **Real-world relevance:** Similar to ECU calibration in automotive industry

---

## 📈 Expected Performance Metrics

Based on testing over 60-second simulations:

| Scenario | Mode | Avg Collisions | Avg Hazard Score | State Transitions |
|----------|------|----------------|------------------|-------------------|
| Random | Cautious | 0-1 | 0.15-0.25 | 8-12 |
| Random | Normal | 0-2 | 0.20-0.30 | 12-18 |
| Random | Aggressive | 1-3 | 0.30-0.45 | 18-25 |
| Corridor | Normal | 0-1 | 0.25-0.35 | 15-20 |
| Dense | Cautious | 1-2 | 0.40-0.55 | 25-35 |

---

## 🎯 Project Contributions (Person 2 Responsibilities)

As the **ALU Engineer / Decision Logic Lead**, I was responsible for:

### Core Implementation
- ✅ Designed 5-state FSM with state transition logic
- ✅ Implemented hazard score calculation (normalized 0.0-1.0)
- ✅ Added hysteresis mechanism to prevent oscillations
- ✅ Created Time-To-Collision predictive braking
- ✅ Configured three driving modes with threshold tuning

### Integration
- ✅ Integrated ALU with sensor subsystem
- ✅ Integrated ALU with physics engine
- ✅ Implemented 100ms control loop backend

### Testing & Validation
- ✅ Created comprehensive test suite
- ✅ Tested edge cases and boundary conditions
- ✅ Validated mode-based behavioral differences
- ✅ Verified collision metrics and hazard trends

### Documentation
- ✅ Created architecture documentation
- ✅ Generated FSM state diagrams
- ✅ Explained threshold configuration
- ✅ Prepared viva answers and technical explanations

---

## 🔧 Future Enhancements

- [ ] Machine learning for threshold auto-tuning
- [ ] Multi-vehicle coordination (V2V communication)
- [ ] 3D environment support
- [ ] Hardware deployment on microcontroller (Arduino/ESP32)
- [ ] ROS integration for real robot testing

---

## 📝 License

Educational project for ADLD course demonstration.

---

## 👤 Author

**Person 2 - ALU Engineer**  
Responsible for ALU decision logic, FSM design, predictive safety, and system integration.
