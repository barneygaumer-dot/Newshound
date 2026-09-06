#!/usr/bin/env bash
set -euo pipefail
ZIP="${1:?usage: upgrade-to-1.0.sh package.zip}"
APP_HOME="${NEWSHOUND_HOME:-/opt/wolfpack/newshound}"
STAMP="$(date +%Y%m%d-%H%M%S)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"; rm -f "$ZIP" 2>/dev/null || true' EXIT
python3 - "$ZIP" "$TMP" <<'PY'
import sys, zipfile, pathlib, stat
zpath,out=sys.argv[1],sys.argv[2]
with zipfile.ZipFile(zpath) as z:
    for i in z.infolist():
        p=pathlib.PurePosixPath(i.filename.replace("\\","/"))
        if p.is_absolute() or ".." in p.parts: raise SystemExit("unsafe zip path")
        if stat.S_IFMT((i.external_attr>>16)&0xffff)==stat.S_IFLNK: raise SystemExit("symlink rejected")
    z.extractall(out)
PY
SRC="$(find "$TMP" -type f -name VERSION -print -quit | xargs -r dirname)"
[ -n "$SRC" ] && [ -f "$SRC/run.py" ] || { echo "Invalid NewsHound package"; exit 2; }
mkdir -p "$APP_HOME/backups/$STAMP"
for p in newshound run.py requirements.txt VERSION install.sh upgrade-to-1.0.sh README.md; do
  [ -e "$APP_HOME/$p" ] && cp -a "$APP_HOME/$p" "$APP_HOME/backups/$STAMP/" || true
done
# Persistent directories are intentionally untouched: config data logs backups venv
rm -rf "$APP_HOME/newshound"
cp -a "$SRC/newshound" "$APP_HOME/"
for p in run.py requirements.txt VERSION install.sh upgrade-to-1.0.sh README.md; do
  [ -e "$SRC/$p" ] && cp -a "$SRC/$p" "$APP_HOME/"
done
chmod +x "$APP_HOME/install.sh" "$APP_HOME/upgrade-to-1.0.sh"
"$APP_HOME/venv/bin/pip" install -r "$APP_HOME/requirements.txt" >>"$APP_HOME/logs/update.log" 2>&1
echo "[$(date -Is)] Installed NewsHound $(cat "$APP_HOME/VERSION") backup=$STAMP" >>"$APP_HOME/logs/update.log"
# Parent Flask service will continue until systemd restart; ask systemd via parent termination fallback.
if command -v systemctl >/dev/null 2>&1; then
  sudo -n systemctl restart newshound 2>/dev/null || pkill -TERM -f "$APP_HOME/run.py" || true
else
  pkill -TERM -f "$APP_HOME/run.py" || true
fi
