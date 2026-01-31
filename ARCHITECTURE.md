# ALU Architecture Documentation

**Author:** Person 2 (ALU Engineer)  
**Module:** `alu_decision.py`

---

## 1. Overview

The ALU Decision Engine is the brain of the autonomous vehicle, processing sensor inputs and generating control commands through a **5-state Finite State Machine (FSM)**.

### Core Components

```
┌─────────────────────────────────────────────────────────┐
│                 SENSOR INPUTS                           │
│            FL   FR   BL   BR (distances)                │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│              ALU DECISION ENGINE                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │
│  │   Hazard    │  │    TTC      │  │   Hysteresis    │  │
│  │   Score     │  │  Predictor  │  │    Counter      │  │
│  └─────────────┘  └─────────────┘  └─────────────────┘  │
│                       │                                 │
│                       ▼                                 │
│  ┌─────────────────────────────────────────────────┐   │
│  │           5-STATE FSM                            │   │
│  │   CRUISE │ AVOID_L │ AVOID_R │ E_BRAKE │ REVERSE│   │
│  └─────────────────────────────────────────────────┘   │
└──────────────────────┬──────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────┐
│                CONTROL OUTPUT                           │
│          throttle, steering, brake                      │
└─────────────────────────────────────────────────────────┘
```

---

## 2. Finite State Machine (FSM)

### State Diagram

```
                        ┌─────────────┐
           ┌───────────►│   CRUISE    │◄───────────┐
           │            └──────┬──────┘            │
           │                   │                   │
           │          Front    │                   │
           │         Obstacle  │                   │ All Clear
           │                   ▼                   │
           │            ┌─────────────┐            │
           │      ┌────►│  AVOID_LEFT │────┐       │
           │      │     └─────────────┘    │       │
           │      │                        │       │
           │      │     ┌─────────────┐    │       │
           │      └─────│ AVOID_RIGHT │◄───┘       │
           │            └─────────────┘            │
           │                                       │
           │   TTC < Threshold                     │
           │   or Both Blocked                     │
           │                   │                   │
           │                   ▼                   │
           │     ┌─────────────────────────┐       │
           └─────│    EMERGENCY_BRAKE      │       │
                 └───────────┬─────────────┘       │
                             │                     │
                      Speed ≈ 0                    │
                             ▼                     │
                 ┌─────────────────────────┐       │
                 │       REVERSING         │───────┘
                 └─────────────────────────┘
                      Back Clear
```

### States and Their Behavior

| State | Throttle | Steering | Brake | Behavior |
|-------|----------|----------|-------|----------|
| CRUISE | 1.0 | 0.0 | 0.0 | Full forward, no steering |
| AVOID_LEFT | 0.6 | -0.5 | 0.0 | Slow forward, turn left |
| AVOID_RIGHT | 0.6 | 0.5 | 0.0 | Slow forward, turn right |
| EMERGENCY_BRAKE | 0.0 | 0.0 | 1.0 | Full brake |
| REVERSING | -0.3 | 0.0 | 0.0 | Slow reverse |

---

## 3. Key Algorithms

### 3.1 Hazard Score Calculation

Normalized danger value [0.0, 1.0]:

```python
if distance <= danger_threshold:
    hazard = 1.0  # Critical
elif distance <= warning_threshold:
    hazard = (warning - distance) / (warning - danger)
else:
    hazard = 0.0  # Safe
```

### 3.2 Time-To-Collision (TTC)

**WOW Feature** - Predictive braking:

```python
TTC = front_distance / current_speed

if TTC < ttc_threshold and speed > 0.5:
    return EMERGENCY_BRAKE  # Predictive intervention
```

### 3.3 Hysteresis Mechanism

Prevents state oscillation:

```python
if desired_state == state_candidate:
    hold_count += 1
else:
    state_candidate = desired_state
    hold_count = 1

if hold_count >= hysteresis_cycles:
    current_state = state_candidate
```

---

## 4. Driving Modes

Same FSM architecture, different thresholds:

| Parameter | Cautious | Normal | Aggressive |
|-----------|----------|--------|------------|
| Danger Threshold | 3.0 m | 2.0 m | 1.0 m |
| Warning Threshold | 5.0 m | 3.5 m | 2.0 m |
| Max Speed | 2.0 m/s | 3.5 m/s | 5.0 m/s |
| TTC Threshold | 3.0 s | 2.0 s | 1.0 s |
| Hysteresis Cycles | 5 | 3 | 2 |

---

## 5. Digital Logic Mapping

### How FSM Maps to Hardware

| Software | Hardware Equivalent |
|----------|-------------------|
| `current_state` | D Flip-Flops (state register) |
| State transition logic | Combinational logic gates |
| 100ms control cycle | Clock signal (10 Hz) |
| Threshold comparisons | Comparator circuits |
| Hysteresis counter | Binary counter |

### Potential Hardware Implementation

```
┌────────────────────────────────────────────┐
│              State Register                │
│         (3 D Flip-Flops for 5 states)      │
└─────────────────┬──────────────────────────┘
                  │
     ┌────────────┼────────────┐
     │            │            │
     ▼            ▼            ▼
┌─────────┐  ┌─────────┐  ┌─────────┐
│Comparator│  │Comparator│  │Comparator│
│FL<danger │  │FR<danger │  │TTC<thres │
└─────────┘  └─────────┘  └─────────┘
     │            │            │
     └────────────┼────────────┘
                  │
                  ▼
         ┌───────────────┐
         │  Next State   │
         │  Logic (AND,  │
         │  OR, NOT)     │
         └───────────────┘
```

---

## 6. Files Summary

| File | Purpose |
|------|---------|
| `alu_decision.py` | Core FSM implementation |
| `config.py` | Driving modes and thresholds |

---

## 7. Testing

```bash
# Run unit tests
python test_alu_unit.py

# Run scenario tests (quick)
python test_scenarios.py --quick

# Run full scenario tests
python test_scenarios.py
```

All 14 unit tests pass with 100% success rate.
