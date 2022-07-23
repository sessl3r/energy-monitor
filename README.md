# energy-monitor

Simple energy monitor based on AVR using EmonLib.

# Usage

Running make upload runs the build process and uploads the binaries to a
Arduino Nano.

# Service

Copy the energy-poll.service to /etc/systemd/system and start the service.

# Accuracy

The configured values are used in my setup and are calibrated agains the
power meter installed in our house. The difference in the last 6 month were around 0.3%.
This is totally sufficient for me to get a feeling for the power usage.

