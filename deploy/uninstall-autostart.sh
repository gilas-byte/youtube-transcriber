#!/usr/bin/env bash
#
# Linux only. Removes the boot-time service. Container, images and data stay.
#
set -euo pipefail

UNIT_NAME="youtube-transcripter.service"

echo "==> Stopping and disabling ${UNIT_NAME} (needs sudo)"
sudo systemctl disable --now "${UNIT_NAME}" || true
sudo rm -f "/etc/systemd/system/${UNIT_NAME}"
sudo systemctl daemon-reload

echo "Done. Autostart service removed."
echo
echo "NOTE: the container still has restart:unless-stopped, so Docker will keep"
echo "bringing it back on boot. To stop that too, run:  docker compose down"
