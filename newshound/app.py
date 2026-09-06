from flask import Flask, render_template, jsonify, request, send_file
from pathlib import Path
from datetime import datetime, timezone
import os, subprocess, tempfile, zipfile, requests

from . import __version__
from .config import BASE, DATA_DIR, load_config, save_config, public_config, ensure_dirs
from .store import status, get_feed, clear_feed, trim_feed
from .sources import SourceManager, _tickers

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 200 * 1024 * 1024
manager = SourceManager()

@app.get("/")
def index():
    return render_template("index.html", version=__version__)

@app.get("/api/status")
def api_status():
    s = status()
    s["version"] = __version__
    return jsonify(s)

@app.get("/api/feed")
def api_feed():
    cfg = load_config()
    limit = min(int(request.args.get("limit", cfg.get("feed_limit",250))), 500)
    return jsonify(get_feed(limit, request.args.get("ticker",""), request.args.get("source",""), request.args.get("importance","")))

@app.post("/api/feed/clear")
def api_clear_feed():
    clear_feed()
    return jsonify(ok=True)

@app.post("/api/start")
def api_start():
    manager.start()
    return jsonify(ok=True)

@app.post("/api/stop")
def api_stop():
    manager.stop()
    return jsonify(ok=True)

@app.get("/api/setup")
def api_setup():
    return jsonify(public_config())

@app.get("/api/watchlist")
def api_watchlist():
    return jsonify(tickers=_tickers(load_config().get("watch_tickers", "")))

@app.post("/api/watchlist")
def api_save_watchlist():
    p = request.get_json(force=True) or {}
    tickers = _tickers(p.get("tickers", ""))
    save_config({"watch_tickers": ",".join(tickers)})
    manager.restart()
    return jsonify(ok=True, tickers=tickers)

@app.post("/api/setup")
def api_save_setup():
    p = request.get_json(force=True) or {}
    updates = {
        "benzinga_enabled": bool(p.get("benzinga_enabled")),
        "finnhub_enabled": bool(p.get("finnhub_enabled")),
        "finnhub_poll_seconds": max(15.0, min(float(p.get("finnhub_poll_seconds",30)), 300.0)),
        "alphavantage_enabled": bool(p.get("alphavantage_enabled")),
        "alphavantage_poll_minutes": max(60.0, min(float(p.get("alphavantage_poll_minutes",60)), 1440.0)),
        "sec_enabled": bool(p.get("sec_enabled", True)),
        "sec_user_agent": str(p.get("sec_user_agent","")).strip(),
        "poll_seconds": max(1.0, min(float(p.get("poll_seconds",2)), 60.0)),
        "feed_limit": max(25, min(int(p.get("feed_limit",250)), 500)),
    }
    for form_name, cfg_name in (
        ("benzinga_api_key", "benzinga_api_key"),
        ("finnhub_api_key", "finnhub_api_key"),
        ("alphavantage_api_key", "alphavantage_api_key"),
    ):
        key = str(p.get(form_name,"")).strip()
        if key:
            updates[cfg_name] = key
    save_config(updates)
    trim_feed()
    manager.restart()
    return jsonify(ok=True, config=public_config())

@app.post("/api/test/benzinga")
def test_benzinga():
    cfg = load_config()
    key = str((request.get_json(silent=True) or {}).get("benzinga_api_key","")).strip() or cfg.get("benzinga_api_key","")
    if not key:
        return jsonify(ok=False, message="No Benzinga API key configured"), 400
    try:
        r = requests.get("https://api.benzinga.com/api/v2/news",
                         headers={"Authorization":f"token {key}", "Accept":"application/json"},
                         params={"pageSize":1, "displayOutput":"headline"}, timeout=10)
        if r.status_code == 200:
            return jsonify(ok=True, message="Benzinga REST authentication passed")
        return jsonify(ok=False, message=f"Benzinga returned HTTP {r.status_code}"), 400
    except Exception as e:
        return jsonify(ok=False, message=f"{type(e).__name__}: {e}"), 400

@app.post("/api/test/finnhub")
def test_finnhub():
    cfg = load_config()
    p = request.get_json(silent=True) or {}
    key = str(p.get("finnhub_api_key","")).strip() or cfg.get("finnhub_api_key","")
    symbols = _tickers(cfg.get("watch_tickers"))
    if not key:
        return jsonify(ok=False, message="No Finnhub API key configured"), 400
    if not symbols:
        return jsonify(ok=False, message="Add at least one ticker to the main watchlist"), 400
    today = datetime.now(timezone.utc).date().isoformat()
    try:
        r = requests.get("https://finnhub.io/api/v1/company-news",
                         params={"symbol":symbols[0], "from":today, "to":today, "token":key}, timeout=10)
        if r.status_code == 200 and isinstance(r.json(), list):
            return jsonify(ok=True, message=f"Finnhub access passed for {symbols[0]}")
        return jsonify(ok=False, message=f"Finnhub returned HTTP {r.status_code}"), 400
    except Exception as e:
        return jsonify(ok=False, message=f"{type(e).__name__}: {e}"), 400

@app.post("/api/test/alphavantage")
def test_alphavantage():
    cfg = load_config()
    p = request.get_json(silent=True) or {}
    key = str(p.get("alphavantage_api_key","")).strip() or cfg.get("alphavantage_api_key","")
    if not key:
        return jsonify(ok=False, message="No Alpha Vantage API key configured"), 400
    try:
        r = requests.get("https://www.alphavantage.co/query",
                         params={"function":"NEWS_SENTIMENT", "sort":"LATEST", "limit":1, "apikey":key}, timeout=12)
        j = r.json() if r.status_code == 200 else {}
        if r.status_code != 200:
            return jsonify(ok=False, message=f"Alpha Vantage returned HTTP {r.status_code}"), 400
        if j.get("Error Message"):
            return jsonify(ok=False, message="Alpha Vantage rejected the request"), 400
        if j.get("Information") and not isinstance(j.get("feed"), list):
            return jsonify(ok=False, message=str(j.get("Information"))[:180]), 400
        if isinstance(j.get("feed"), list):
            return jsonify(ok=True, message="Alpha Vantage NEWS_SENTIMENT access passed")
        return jsonify(ok=False, message="Unexpected Alpha Vantage response"), 400
    except Exception as e:
        return jsonify(ok=False, message=f"{type(e).__name__}: {e}"), 400

@app.post("/api/test/sec")
def test_sec():
    cfg = load_config()
    p = request.get_json(silent=True) or {}
    ua = str(p.get("sec_user_agent", "")).strip() or cfg.get("sec_user_agent", "")
    symbols = _tickers(cfg.get("watch_tickers"))
    if not symbols:
        return jsonify(ok=False, message="Add at least one ticker to the main watchlist"), 400
    if "@" not in ua:
        return jsonify(ok=False, message="SEC User-Agent should identify app and contact email"), 400
    try:
        pairs = manager.resolve_sec_ciks(symbols, ua)
        if not pairs:
            return jsonify(ok=False, message="No selected tickers resolved in SEC company_tickers.json"), 400
        symbol, cik = pairs[0]
        r = requests.get(f"https://data.sec.gov/submissions/CIK{cik}.json",
                         headers={"User-Agent":ua, "Accept-Encoding":"gzip, deflate"}, timeout=10)
        if r.status_code == 200:
            return jsonify(ok=True, message=f"SEC access passed: {symbol} → CIK {cik}")
        return jsonify(ok=False, message=f"SEC returned HTTP {r.status_code}"), 400
    except Exception as e:
        return jsonify(ok=False, message=f"{type(e).__name__}: {e}"), 400

@app.get("/api/evidence/download")
def evidence_download():
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    p = DATA_DIR/"evidence"/f"newshound-{day}.jsonl"
    if not p.exists():
        return jsonify(ok=False, message="No evidence file for today yet"), 404
    return send_file(p, as_attachment=True, download_name=p.name)

def _safe_zip(z):
    for info in z.infolist():
        name = info.filename.replace("\\","/")
        if name.startswith("/") or ".." in Path(name).parts:
            raise ValueError(f"Unsafe ZIP path: {name}")
        if info.is_dir(): continue
        mode = (info.external_attr >> 16) & 0o170000
        if mode == 0o120000:
            raise ValueError(f"Symlink not allowed: {name}")

@app.post("/api/update")
def api_update():
    f = request.files.get("package")
    if not f or not f.filename.lower().endswith(".zip"):
        return jsonify(ok=False, message="Select a NewsHound ZIP package"), 400
    ensure_dirs()
    fd, tmppath = tempfile.mkstemp(prefix="newshound-update-", suffix=".zip")
    os.close(fd)
    f.save(tmppath)
    try:
        with zipfile.ZipFile(tmppath) as z:
            _safe_zip(z)
            names = [n.replace("\\","/") for n in z.namelist()]
            versions = [n for n in names if n.endswith("/VERSION") or n == "VERSION"]
            if not versions:
                raise ValueError("Package has no VERSION file")
            version = z.read(versions[0]).decode().strip()
            if not version:
                raise ValueError("Empty VERSION")
        updater = BASE/"upgrade-to-1.0.sh"
        if not updater.exists():
            raise ValueError("Updater is missing from installed application")
        subprocess.Popen([str(updater), tmppath], start_new_session=True,
                         stdout=open(BASE/"logs"/"update.log","a"), stderr=subprocess.STDOUT)
        return jsonify(ok=True, message=f"Update {version} accepted; NewsHound will restart.")
    except Exception as e:
        try: os.unlink(tmppath)
        except OSError: pass
        return jsonify(ok=False, message=str(e)), 400

if __name__ == "__main__":
    ensure_dirs()
    manager.start()
    app.run(host="0.0.0.0", port=int(os.environ.get("NEWSHOUND_PORT","8091")), threaded=True)
