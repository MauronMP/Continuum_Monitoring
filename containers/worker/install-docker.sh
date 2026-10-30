#!/bin/sh
# Run as root on a fresh Debian/Raspberry Pi OS host. Existing Docker is preserved.
set -eu
if command -v docker >/dev/null 2>&1; then
    docker version
    docker compose version
else
    . /etc/os-release
    case "$ID" in debian|raspbian) ;; *) echo 'Use the official Docker installation instructions for this OS.' >&2; exit 1;; esac
    case "$VERSION_CODENAME" in bookworm|trixie) ;; *) echo 'Supported Debian releases: bookworm and trixie.' >&2; exit 1;; esac
    apt-get update
    apt-get install -y ca-certificates curl
    install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
    chmod a+r /etc/apt/keyrings/docker.asc
    printf 'deb [arch=%s signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian %s stable\n' "$(dpkg --print-architecture)" "$VERSION_CODENAME" > /etc/apt/sources.list.d/continuum-docker.list
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    systemctl enable --now docker
fi
if [ -n "${1:-}" ]; then
    usermod -aG docker "$1"
fi
