# ModeOS Controlled Environment Container
# Ubuntu 24.04 LTS with PulseAudio, Brightness, and FreeDesktop tools
FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV MODEOS_MOCK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    python3-psutil \
    python3-yaml \
    pulseaudio-utils \
    brightnessctl \
    x11-xserver-utils \
    redshift \
    xvfb \
    procps \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy project files
COPY . /app/

# Install ModeOS package in editable mode
RUN pip3 install --no-cache-dir --break-system-packages -e .

# Run test suite as default entrypoint
CMD ["python3", "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"]
