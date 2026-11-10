#!/usr/bin/env bash
set -euo pipefail

export DISPLAY=:99

PROJECT="${PROJECT:-01_logic_gates}"
if [ -n "${WAVE_FILE:-}" ]; then
    WAVE="projects/${PROJECT}/build/${WAVE_FILE}"
else
    # Existing testbenches use different dumpfile names; open the latest run.
    WAVE=$(ls -t "projects/${PROJECT}/build/"*.vcd 2>/dev/null | head -n 1 || true)
fi

if [ ! -f "$WAVE" ]; then
    echo "ERROR: Waveform not found: $WAVE"
    echo "Run the simulation first: docker compose run --rm sim make test"
    exit 1
fi

echo "Starting virtual X11 display..."

# Check whether Xvfb is already running
if pgrep -f '[X]vfb :99' > /dev/null; then
    echo "ERROR: Xvfb is already running on display :99"
    exit 1
fi

# Remove stale locks only if no Xvfb is running
rm -f /tmp/.X99-lock

# Remove stale socket only if no Xvfb is running
rm -f /tmp/.X11-unix/X99

# Start Xvfb
Xvfb :99 -screen 0 1920x1080x24 &
XVFB_PID=$!

# Wait until the X11 socket exists and GTK can connect.
READY=0

for i in $(seq 1 30); do
    if ! kill -0 "$XVFB_PID" 2>/dev/null; then
        echo "ERROR: Xvfb exited unexpectedly."
        exit 1
    fi

    if [ -S /tmp/.X11-unix/X99 ] && \
       bash -c 'echo >/dev/tcp/127.0.0.1/6099' 2>/dev/null; then
        READY=1
        break
    fi

    sleep 0.2
done

# X11 Unix socket is the primary readiness check.
if [ "$READY" -ne 1 ] && [ -S /tmp/.X11-unix/X99 ]; then
    READY=1
fi

if [ "$READY" -ne 1 ]; then
    echo "ERROR: Xvfb did not become ready."
    exit 1
fi

echo "Starting VNC server..."

x11vnc \
    -display :99 \
    -forever \
    -shared \
    -nopw \
    -localhost \
    -rfbport 5900 &

echo "Starting noVNC..."

websockify \
    --web=/usr/share/novnc \
    0.0.0.0:6080 \
    localhost:5900 &

echo "Opening GTKWave: $WAVE"

gtkwave "$WAVE"
