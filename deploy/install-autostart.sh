#!/usr/bin/env bash
#
# Linux only. Makes YouTube Transcripter start automatically on boot.
#
# Docker already restarts the container by itself (`restart: unless-stopped`).
# All this script really needs to do is make sure the Docker daemon starts at
# boot. The systemd unit it installs is an extra safety net that brings the
# stack back even after a manual `docker compose down`.
#
# CPU or GPU is read from COMPOSE_FILE in .env - switch with ./mode.sh
#
#   ./deploy/install-autostart.sh
#
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UNIT_NAME="youtube-transcripter.service"
TEMPLATE="${PROJECT_DIR}/deploy/${UNIT_NAME}"

if ! command -v systemctl >/dev/null 2>&1; then
    echo "systemd was not found. This script is for Linux only." >&2
    echo "On Windows or macOS, see README section 4." >&2
    exit 1
fi

if [[ ! -f "${PROJECT_DIR}/.env" ]]; then
    echo "==> .env not found, creating it from .env.example"
    cp "${PROJECT_DIR}/.env.example" "${PROJECT_DIR}/.env"
fi

MODE="cpu"
grep -qE '^COMPOSE_FILE=.*gpu' "${PROJECT_DIR}/.env" && MODE="gpu"
echo "==> Mode from .env: ${MODE}"

DOCKER_BIN="$(command -v docker || echo /usr/bin/docker)"

echo "==> Making sure the Docker daemon starts at boot"
sudo systemctl enable docker.service

echo "==> Rendering unit file"
TMP_UNIT="$(mktemp)"
sed -e "s|__PROJECT_DIR__|${PROJECT_DIR}|g" \
    -e "s|/usr/bin/docker|${DOCKER_BIN}|g" \
    "${TEMPLATE}" > "${TMP_UNIT}"

echo "==> Installing /etc/systemd/system/${UNIT_NAME} (needs sudo)"
sudo install -m 644 "${TMP_UNIT}" "/etc/systemd/system/${UNIT_NAME}"
rm -f "${TMP_UNIT}"

echo "==> Enabling and starting ${UNIT_NAME}"
sudo systemctl daemon-reload
sudo systemctl enable --now "${UNIT_NAME}"

echo
echo "Done. The app is available at http://localhost:8501"
echo "Status:  systemctl status ${UNIT_NAME}"
echo "Logs:    docker compose -f ${PROJECT_DIR}/docker-compose.yml logs -f"
