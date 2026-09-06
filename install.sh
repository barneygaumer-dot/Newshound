#!/usr/bin/env bash
set -euo pipefail
APP_HOME="${NEWSHOUND_HOME:-/opt/wolfpack/newshound}"
PORT="${NEWSHOUND_PORT:-8091}"
USER_NAME="${SUDO_USER:-$USER}"
echo "[NewsHound] Installing v1.3-hf5 to $APP_HOME"
sudo mkdir -p "$APP_HOME" "$APP_HOME/config" "$APP_HOME/data/evidence" "$APP_HOME/logs" "$APP_HOME/backups"
sudo chown -R "$USER_NAME":"$(id -gn "$USER_NAME")" "$APP_HOME"
HERE="$(cd "$(dirname "$0")" && pwd)"
cp -a "$HERE"/. "$APP_HOME"/
mkdir -p "$APP_HOME/config" "$APP_HOME/data/evidence" "$APP_HOME/logs" "$APP_HOME/backups"
python3 -m venv "$APP_HOME/venv"
"$APP_HOME/venv/bin/pip" install --upgrade pip
"$APP_HOME/venv/bin/pip" install -r "$APP_HOME/requirements.txt"
chmod +x "$APP_HOME/install.sh" "$APP_HOME/upgrade-to-1.0.sh"
SERVICE="/etc/systemd/system/newshound.service"
sudo tee "$SERVICE" >/dev/null <<EOF
[Unit]
Description=WolfPack NewsHound
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$USER_NAME
WorkingDirectory=$APP_HOME
Environment=NEWSHOUND_HOME=$APP_HOME
Environment=NEWSHOUND_PORT=$PORT
ExecStart=$APP_HOME/venv/bin/python $APP_HOME/run.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
sudo systemctl daemon-reload
sudo systemctl enable --now newshound
echo
echo "[NewsHound] Installed. Open http://127.0.0.1:$PORT"
echo "[NewsHound] LAN access: http://<this-host-ip>:$PORT"
