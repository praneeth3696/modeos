#!/bin/bash

# brightness.sh
# Usage: ./brightness.sh <percentage (0-100)>

if [ -z "$1" ]; then
    echo "Usage: $0 <percentage>"
    exit 1
fi

PERCENT=$1

if command -v brightnessctl &> /dev/null; then
    brightnessctl set ${PERCENT}% > /dev/null
    if [ $? -eq 0 ]; then
        echo "[SUCCESS] Brightness set to ${PERCENT}% using brightnessctl"
        exit 0
    else
        echo "[WARN] brightnessctl failed"
    fi
fi

if command -v xrandr &> /dev/null; then
    # Fallback to xrandr, assuming primary display
    # xrandr uses a 0.0 to 1.0 scale
    DECIMAL=$(echo "scale=2; $PERCENT / 100" | bc 2>/dev/null)
    if [ -z "$DECIMAL" ]; then
        # fallback if bc is not installed
        DECIMAL="0.${PERCENT}"
        if [ "$PERCENT" -eq 100 ]; then DECIMAL="1.0"; fi
        if [ "$PERCENT" -lt 10 ]; then DECIMAL="0.0${PERCENT}"; fi
    fi
    DISPLAY_NAME=$(xrandr | grep " connected" | cut -f1 -d " ")
    for disp in $DISPLAY_NAME; do
        xrandr --output $disp --brightness $DECIMAL > /dev/null
    done
    if [ $? -eq 0 ]; then
        echo "[SUCCESS] Brightness set to ${PERCENT}% using xrandr"
        exit 0
    else
        echo "[ERROR] xrandr failed"
        exit 1
    fi
fi

echo "[ERROR] Neither brightnessctl nor xrandr found or both failed."
exit 1
