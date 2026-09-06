#!/usr/bin/env bash
#
# Switch YouTube Transcripter between CPU and GPU.
#
#   ./mode.sh          show the current mode
#   ./mode.sh cpu      switch to CPU and restart
#   ./mode.sh gpu      switch to NVIDIA GPU and restart
#
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${PROJECT_DIR}/.env"
CPU_VALUE="docker-compose.yml"
GPU_VALUE="docker-compose.yml:docker-compose.gpu.yml"

cd "${PROJECT_DIR}"

if [[ ! -f "${ENV_FILE}" ]]; then
    echo "==> .env not found, creating it from .env.example"
    cp "${PROJECT_DIR}/.env.example" "${ENV_FILE}"
fi

current_mode() {
    if grep -qE '^COMPOSE_FILE=.*gpu' "${ENV_FILE}"; then echo "gpu"; else echo "cpu"; fi
}

TARGET="${1:-status}"

case "${TARGET}" in
    status|"")
        echo "Current mode: $(current_mode)"
        echo "Runtime reported by the app:"
        docker compose exec -T transcripter python -c \
            "import sys; sys.path.insert(0,'/app'); from app.core import transcriber; print('  ' + transcriber.describe_runtime())" \
            2>/dev/null || echo "  (container is not running)"
        exit 0
        ;;
    cpu) NEW_VALUE="${CPU_VALUE}" ;;
    gpu) NEW_VALUE="${GPU_VALUE}" ;;
    -h|--help)
        sed -n '2,8p' "$0" | sed 's/^# \{0,1\}//'
        exit 0
        ;;
    *)
        echo "Unknown mode '${TARGET}'. Use: cpu, gpu or status." >&2
        exit 1
        ;;
esac

if [[ "$(current_mode)" == "${TARGET}" ]]; then
    echo "Already in ${TARGET} mode. Nothing to do."
    exit 0
fi

if [[ "${TARGET}" == "gpu" ]]; then
    if ! command -v nvidia-smi >/dev/null 2>&1; then
        echo "WARNING: nvidia-smi was not found. You probably do not have an"
        echo "         NVIDIA driver installed. See README section 3."
        read -r -p "Continue anyway? [y/N] " reply
        [[ "${reply}" =~ ^[Yy]$ ]] || exit 1
    fi
    echo "NOTE: the first GPU build downloads about 5 GB of CUDA libraries."
fi

echo "==> Switching to ${TARGET} mode"
TMP_ENV="$(mktemp)"
{
    echo "# Run mode - managed by mode.sh. Values: docker-compose.yml"
    echo "#            or docker-compose.yml:docker-compose.gpu.yml"
    echo "COMPOSE_PATH_SEPARATOR=:"
    echo "COMPOSE_FILE=${NEW_VALUE}"
    grep -vE '^[[:space:]]*#?[[:space:]]*(COMPOSE_FILE|COMPOSE_PATH_SEPARATOR)=' "${ENV_FILE}" \
        | grep -vE '^# Run mode - managed by mode\.sh' \
        | grep -vE '^#            or docker-compose\.yml'
} > "${TMP_ENV}"
mv "${TMP_ENV}" "${ENV_FILE}"

echo "==> Rebuilding and restarting"
docker compose up -d --build

echo
echo "Done. Mode is now: $(current_mode)"
echo "Open http://localhost:8501 and check the Runtime line in the sidebar."
