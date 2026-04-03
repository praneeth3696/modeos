#!/bin/bash

# nightlight.sh
# Usage: ./nightlight.sh <true|false>

if [ -z "$1" ]; then
    echo "Usage: $0 <true|false>"
    exit 1
fi

STATE=$1

if ! command -v redshift &> /dev/null; then
    echo "[WARN] redshift not found. Cannot toggle night light."
    exit 0
fi

if [ "$STATE" = "true" ]; then
    # Kill existing redshift if running to apply new settings
    pkill redshift 2>/dev/null
    # Run redshift in background with a warm color temperature
    # 3500K is a common warm value, 5500K is daylight
    redshift -O 3500 &> /dev/null &
    echo "[SUCCESS] Night light enabled (Redshift 3500K)"
    exit 0
elif [ "$STATE" = "false" ]; then
    # Reset redshift to default values and kill the process
    redshift -x &> /dev/null
    pkill redshift 2>/dev/null
    echo "[SUCCESS] Night light disabled"
    exit 0
else
    echo "[ERROR] Invalid argument. Use 'true' or 'false'."
    exit 1
fi
