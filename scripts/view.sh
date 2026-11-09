#!/usr/bin/env bash
set -e

export DISPLAY=:99

PROJECT="${PROJECT:-01_logic_gates}"
WAVE="projects/${PROJECT}/build/waves.vcd"

if [ ! -f "$WAVE" ]; then
    echo "Waveform not found: $WAVE"
    echo "Run the simulation first."
    exit 1
fi

Xvfb :99 -screen 0 1920x1080x24 &
sleep 2

x11vnc \
    -display :99 \
    -forever \
    -shared \
    -nopw \
    -localhost \
    -rfbport 5900 &

websockify \
    --web=/usr/share/novnc \
    0.0.0.0:6080 \
    localhost:5900 &

echo "Open http://localhost:6080/vnc.html"

gtkwave "$WAVE"