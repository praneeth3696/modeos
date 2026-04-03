#!/bin/bash

# volume.sh
# Usage: ./volume.sh <percentage (0-100)>

if [ -z "$1" ]; then
    echo "Usage: $0 <percentage>"
    exit 1
fi

PERCENT=$1

if command -v pactl &> /dev/null; then
    pactl set-sink-volume @DEFAULT_SINK@ ${PERCENT}% > /dev/null
    if [ $? -eq 0 ]; then
        echo "[SUCCESS] Volume set to ${PERCENT}% using pactl"
        exit 0
    else
        echo "[WARN] pactl failed"
    fi
fi

if command -v amixer &> /dev/null; then
    amixer -D pulse sset Master ${PERCENT}% > /dev/null 2>&1 || amixer sset Master ${PERCENT}% > /dev/null
    if [ $? -eq 0 ]; then
        echo "[SUCCESS] Volume set to ${PERCENT}% using amixer"
        exit 0
    else
        echo "[ERROR] amixer failed"
        exit 1
    fi
fi

echo "[ERROR] Neither amixer nor pactl found or both failed."
exit 1
