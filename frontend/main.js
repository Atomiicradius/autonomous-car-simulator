// WebSocket connection
const socket = io('http://localhost:5000');

// Canvas setup
const canvas = document.getElementById('simCanvas');
const ctx = canvas.getContext('2d');

// UI Elements
const startBtn = document.getElementById('startBtn');
const pauseBtn = document.getElementById('pauseBtn');
const resetBtn = document.getElementById('resetBtn');
const modeSelect = document.getElementById('modeSelect');
const scenarioSelect = document.getElementById('scenarioSelect');
const connectionStatus = document.getElementById('connectionStatus');

// State colors for FSM
const STATE_COLORS = {
    'CRUISE': '#4caf50',
    'AVOID_LEFT': '#2196f3',
    'AVOID_RIGHT': '#ff9800',
    'EMERGENCY_BRAKE': '#f44336',
    'REVERSING': '#9c27b0',
    'IDLE': '#757575'
};

// WebSocket event handlers
socket.on('connect', () => {
    console.log('Connected to backend');
    connectionStatus.textContent = '🟢 Connected';
    connectionStatus.className = 'status-indicator online';
});

socket.on('disconnect', () => {
    console.log('Disconnected from backend');
    connectionStatus.textContent = '⚫ Disconnected';
    connectionStatus.className = 'status-indicator offline';
});

socket.on('telemetry', (data) => {
    updateMetrics(data);
    renderSimulation(data);
});

// Control button handlers
startBtn.addEventListener('click', async () => {
    const mode = modeSelect.value;
    const scenario = scenarioSelect.value;

    try {
        const response = await fetch('http://localhost:5000/api/start', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mode, scenario })
        });
        const result = await response.json();
        console.log('Simulation started:', result);
    } catch (error) {
        console.error('Error starting simulation:', error);
        alert('Failed to start simulation. Make sure the backend server is running.');
    }
});

pauseBtn.addEventListener('click', async () => {
    try {
        const response = await fetch('http://localhost:5000/api/pause', {
            method: 'POST'
        });
        const result = await response.json();
        console.log('Simulation paused:', result);
    } catch (error) {
        console.error('Error pausing simulation:', error);
    }
});

resetBtn.addEventListener('click', async () => {
    const mode = modeSelect.value;
    const scenario = scenarioSelect.value;

    try {
        const response = await fetch('http://localhost:5000/api/reset', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mode, scenario })
        });
        const result = await response.json();
        console.log('Simulation reset:', result);

        // Clear canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);
    } catch (error) {
        console.error('Error resetting simulation:', error);
    }
});

// Update metrics display
function updateMetrics(data) {
    const { telemetry, state, metrics } = data;

    // FSM State
    const fsmState = document.getElementById('fsmState');
    fsmState.textContent = telemetry.state;
    fsmState.style.color = STATE_COLORS[telemetry.state] || '#ffffff';

    // Speed
    document.getElementById('speed').textContent = telemetry.speed.toFixed(2);

    // Hazard Score
    const hazardScore = telemetry.hazard_score;
    document.getElementById('hazard').textContent = hazardScore.toFixed(2);
    document.getElementById('hazardBar').style.width = `${hazardScore * 100}%`;

    // Time-To-Collision
    const ttcValue = telemetry.ttc === Infinity ? '∞' : telemetry.ttc.toFixed(2);
    document.getElementById('ttc').textContent = ttcValue;

    // Position
    const pos = telemetry.position;
    document.getElementById('position').textContent = `${pos[0].toFixed(1)}, ${pos[1].toFixed(1)}`;

    // Heading
    const headingDeg = (telemetry.heading * 180 / Math.PI).toFixed(0);
    document.getElementById('heading').textContent = `${headingDeg}°`;

    // Session Statistics
    document.getElementById('collisions').textContent = metrics.total_collisions;
    document.getElementById('transitions').textContent = metrics.state_transitions;
    document.getElementById('emergencyBrakes').textContent = metrics.emergency_brakes;
    document.getElementById('cycleCount').textContent = telemetry.cycle;
}

// Render simulation on canvas
function renderSimulation(data) {
    const { state } = data;

    // Clear canvas
    ctx.fillStyle = 'rgba(0, 0, 0, 0.3)';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Scale factor (world coordinates to canvas)
    const scale = 10;
    const offsetX = canvas.width / 2;
    const offsetY = canvas.height / 2;

    // Draw obstacles (BARRIERS) - Much more visible
    if (state.obstacles) {
        state.obstacles.forEach((obstacle, index) => {
            const x = obstacle.x * scale + offsetX;
            const y = -obstacle.y * scale + offsetY;
            const radius = obstacle.radius * scale;

            // Shadow for depth
            ctx.fillStyle = 'rgba(0, 0, 0, 0.3)';
            ctx.beginPath();
            ctx.arc(x + 3, y + 3, radius, 0, Math.PI * 2);
            ctx.fill();

            // Main obstacle - bright red/orange
            ctx.fillStyle = '#ff5722';
            ctx.beginPath();
            ctx.arc(x, y, radius, 0, Math.PI * 2);
            ctx.fill();

            // Border
            ctx.strokeStyle = '#d32f2f';
            ctx.lineWidth = 3;
            ctx.stroke();

            // Label
            ctx.fillStyle = '#ffffff';
            ctx.font = 'bold 12px Inter';
            ctx.textAlign = 'center';
            ctx.fillText('BARRIER', x, y + 5);
        });
    }

    // Draw sensor rays - Color-coded by distance
    if (state.sensor_rays) {
        state.sensor_rays.forEach(ray => {
            const distance = ray.distance || 100;

            // Color based on danger level
            let color;
            if (distance < 3) {
                color = '#ff0000'; // RED - Very close!
            } else if (distance < 5) {
                color = '#ff9800'; // ORANGE - Close
            } else if (distance < 8) {
                color = '#ffeb3b'; // YELLOW - Moderate
            } else {
                color = '#4caf50'; // GREEN - Safe
            }

            ctx.strokeStyle = color;
            ctx.lineWidth = 4; // Thicker rays
            ctx.shadowBlur = 10;
            ctx.shadowColor = color;

            ctx.beginPath();
            ctx.moveTo(ray.start[0] * scale + offsetX, -ray.start[1] * scale + offsetY);
            ctx.lineTo(ray.end[0] * scale + offsetX, -ray.end[1] * scale + offsetY);
            ctx.stroke();

            ctx.shadowBlur = 0; // Reset shadow
        });
    }

    // Draw vehicle - MUCH BIGGER AND CLEARER
    if (state.vehicle) {
        const veh = state.vehicle;
        const x = veh.position[0] * scale + offsetX;
        const y = -veh.position[1] * scale + offsetY;
        const heading = -veh.heading;
        const size = veh.size * scale * 2.5; // Make car 2.5x bigger!

        ctx.save();
        ctx.translate(x, y);
        ctx.rotate(heading);

        // Shadow
        ctx.fillStyle = 'rgba(0, 0, 0, 0.4)';
        ctx.fillRect(-size / 2 + 3, -size / 2 + 3, size, size * 0.6);

        // Vehicle body (color based on state)
        const vehicleColor = STATE_COLORS[state.alu_state] || '#2196f3';
        ctx.fillStyle = vehicleColor;
        ctx.fillRect(-size / 2, -size / 2, size, size * 0.6);

        // Border
        ctx.strokeStyle = '#0d47a1';
        ctx.lineWidth = 3;
        ctx.strokeRect(-size / 2, -size / 2, size, size * 0.6);

        // Direction indicator (front of car)
        ctx.fillStyle = '#ffeb3b';
        ctx.beginPath();
        ctx.moveTo(size / 2, 0);
        ctx.lineTo(size / 3, -size / 4);
        ctx.lineTo(size / 3, size / 4);
        ctx.closePath();
        ctx.fill();

        // "CAR" label
        ctx.fillStyle = '#ffffff';
        ctx.font = 'bold 10px Inter';
        ctx.textAlign = 'center';
        ctx.fillText('CAR', 0, 3);

        ctx.restore();

        // Draw velocity vector
        if (veh.speed > 0.1) {
            ctx.strokeStyle = '#00ff00';
            ctx.lineWidth = 2;
            ctx.beginPath();
            ctx.moveTo(x, y);
            const vx = Math.cos(veh.heading) * veh.speed * scale * 2;
            const vy = Math.sin(veh.heading) * veh.speed * scale * 2;
            ctx.lineTo(x + vx, y - vy);
            ctx.stroke();
        }
    }

    // Draw grid
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
    ctx.lineWidth = 1;
    for (let i = 0; i < canvas.width; i += 50) {
        ctx.beginPath();
        ctx.moveTo(i, 0);
        ctx.lineTo(i, canvas.height);
        ctx.stroke();
    }
    for (let i = 0; i < canvas.height; i += 50) {
        ctx.beginPath();
        ctx.moveTo(0, i);
        ctx.lineTo(canvas.width, i);
        ctx.stroke();
    }

    // Draw center crosshair
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.3)';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(offsetX - 20, offsetY);
    ctx.lineTo(offsetX + 20, offsetY);
    ctx.moveTo(offsetX, offsetY - 20);
    ctx.lineTo(offsetX, offsetY + 20);
    ctx.stroke();

    // Draw legend
    const legendX = 20;
    const legendY = 20;
    ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
    ctx.fillRect(legendX - 10, legendY - 10, 200, 140);

    ctx.font = 'bold 14px Inter';
    ctx.fillStyle = '#ffffff';
    ctx.textAlign = 'left';
    ctx.fillText('LEGEND:', legendX, legendY + 10);

    ctx.font = '12px Inter';

    // Car
    ctx.fillStyle = '#2196f3';
    ctx.fillRect(legendX, legendY + 25, 15, 10);
    ctx.fillStyle = '#ffffff';
    ctx.fillText('= Autonomous Car', legendX + 20, legendY + 33);

    // Barrier
    ctx.fillStyle = '#ff5722';
    ctx.beginPath();
    ctx.arc(legendX + 7, legendY + 50, 7, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#ffffff';
    ctx.fillText('= Barrier (Obstacle)', legendX + 20, legendY + 53);

    // Sensor rays
    ctx.strokeStyle = '#4caf50';
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(legendX, legendY + 70);
    ctx.lineTo(legendX + 15, legendY + 70);
    ctx.stroke();
    ctx.fillStyle = '#ffffff';
    ctx.fillText('= Sensor (Green=Safe)', legendX + 20, legendY + 73);

    ctx.strokeStyle = '#ff0000';
    ctx.beginPath();
    ctx.moveTo(legendX, legendY + 90);
    ctx.lineTo(legendX + 15, legendY + 90);
    ctx.stroke();
    ctx.fillStyle = '#ffffff';
    ctx.fillText('= Sensor (Red=Danger)', legendX + 20, legendY + 93);

    // State indicator
    if (state.alu_state) {
        ctx.fillStyle = '#ffeb3b';
        ctx.fillText('State: ' + state.alu_state, legendX, legendY + 113);
    }
}

// Initial canvas setup
ctx.fillStyle = 'rgba(0, 0, 0, 0.3)';
ctx.fillRect(0, 0, canvas.width, canvas.height);
ctx.fillStyle = '#ffffff';
ctx.font = '20px Inter';
ctx.textAlign = 'center';
ctx.fillText('Click START to begin simulation', canvas.width / 2, canvas.height / 2);
