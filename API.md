# API Documentation

## Backend Server API Reference

Base URL: `http://localhost:5000`

---

## Endpoints

### Simulation Control

#### `POST /api/start`
Start or resume the simulation.

**Request Body:**
```json
{
  "mode": "normal",      // "cautious" | "normal" | "aggressive"
  "scenario": "random"   // "corridor" | "random" | "intersection" | "dense"
}
```

**Response:**
```json
{
  "status": "started",
  "mode": "normal",
  "scenario": "random"
}
```

---

#### `POST /api/pause`
Pause the simulation.

**Response:**
```json
{
  "status": "paused"
}
```

---

#### `POST /api/reset`
Reset the simulation to initial state.

**Request Body:**
```json
{
  "mode": "normal",
  "scenario": "random"
}
```

**Response:**
```json
{
  "status": "reset",
  "mode": "normal",
  "scenario": "random"
}
```

---

### State & Metrics

#### `GET /api/status`
Get current simulation status.

**Response:**
```json
{
  "running": true,
  "mode": "normal",
  "scenario": "random",
  "cycle_count": 150,
  "metrics": {
    "total_collisions": 2,
    "avg_hazard_score": 0.25,
    "state_transitions": 12,
    "emergency_brakes": 3,
    "ttc_interventions": 5
  }
}
```

---

#### `GET /api/state`
Get detailed current simulation state.

**Response:**
```json
{
  "vehicle": {
    "position": [250.5, 300.2],
    "speed": 2.5,
    "heading": 1.57,
    "collisions": 2
  },
  "obstacles": [
    {"x": 100, "y": 100, "radius": 20, "type": "static"},
    ...
  ],
  "sensor_rays": {
    "FL": {"start": [250, 300], "end": [280, 330], "distance": 45.2},
    ...
  },
  "alu_state": "CRUISE",
  "alu_metrics": {
    "hazard_score": 0.15,
    "ttc": 5.2
  }
}
```

---

#### `GET /api/metrics`
Get summary metrics for current simulation.

**Response:**
```json
{
  "mode": "normal",
  "scenario": "random",
  "total_time": 60.0,
  "total_cycles": 600,
  "total_collisions": 2,
  "total_distance": 150.5,
  "avg_speed": 2.51,
  "avg_hazard_score": 0.25,
  "state_transitions": 12,
  "emergency_brakes": 3,
  "ttc_interventions": 5,
  "time_to_first_collision": 15.3
}
```

---

### Data Management

#### `GET /api/logs`
List all available CSV log files.

**Response:**
```json
{
  "logs": [
    {
      "filename": "telemetry_normal_random_20260201_003000.csv",
      "size": 45678,
      "modified": 1738358400.0,
      "path": "logs/telemetry_normal_random_20260201_003000.csv"
    },
    ...
  ]
}
```

---

#### `GET /api/download_log/<filename>`
Download a specific CSV log file.

**Parameters:**
- `filename`: Name of the CSV file to download

**Response:**
- File download (CSV format)
- 404 if file not found

**Example:**
```
GET /api/download_log/telemetry_normal_random_20260201_003000.csv
```

---

#### `POST /api/compare_modes/<scenario>`
Run the same scenario in all 3 modes and return comparison data.

**Parameters:**
- `scenario`: Scenario name ("corridor" | "random" | "intersection" | "dense")

**Response:**
```json
{
  "scenario": "random",
  "comparison": [
    {
      "mode": "cautious",
      "total_collisions": 0,
      "avg_speed": 1.8,
      "avg_hazard_score": 0.15,
      ...
    },
    {
      "mode": "normal",
      "total_collisions": 1,
      "avg_speed": 2.2,
      "avg_hazard_score": 0.25,
      ...
    },
    {
      "mode": "aggressive",
      "total_collisions": 4,
      "avg_speed": 2.8,
      "avg_hazard_score": 0.40,
      ...
    }
  ]
}
```

---

## WebSocket Events

### Connection

**Event:** `connect`

Server emits:
```json
{
  "status": "connected"
}
```

---

### Telemetry Stream

**Event:** `telemetry`

Server emits every 100ms during simulation:
```json
{
  "telemetry": {
    "cycle": 150,
    "timestamp": 15.0,
    "state": "CRUISE",
    "position": [250.5, 300.2],
    "speed": 2.5,
    "heading": 1.57,
    "sensors": {
      "FL": 45.2,
      "FR": 89.1,
      "BL": 100.0,
      "BR": 30.5
    },
    "hazard_score": 0.25,
    "ttc": 5.2,
    "collision": false,
    "total_collisions": 2
  },
  "state": { /* same as /api/state */ },
  "metrics": { /* same as /api/status metrics */ }
}
```

---

## CSV Log Format

Telemetry CSV files contain the following columns:

| Column | Type | Description |
|--------|------|-------------|
| cycle | int | Cycle number (0-indexed) |
| timestamp | float | Time in seconds since start |
| state | string | FSM state (CRUISE, AVOID_LEFT, etc.) |
| x | float | Car X position |
| y | float | Car Y position |
| speed | float | Car speed (m/s) |
| heading | float | Car heading angle (radians) |
| FL | float | Front-left sensor distance |
| FR | float | Front-right sensor distance |
| BL | float | Back-left sensor distance |
| BR | float | Back-right sensor distance |
| hazard_score | float | Computed hazard score (0.0-1.0) |
| ttc | float | Time-to-collision (seconds, 999.0 if infinite) |
| collision | int | 1 if collision occurred this cycle, 0 otherwise |
| total_collisions | int | Cumulative collision count |

---

## Error Responses

All endpoints may return error responses in the format:

```json
{
  "error": "Error message description"
}
```

Common HTTP status codes:
- `200` - Success
- `404` - Resource not found
- `500` - Server error
