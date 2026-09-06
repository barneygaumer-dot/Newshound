from pathlib import Path
import json, os

BASE = Path(os.environ.get("NEWSHOUND_HOME", "/opt/wolfpack/newshound"))
CONFIG_DIR = BASE / "config"
DATA_DIR = BASE / "data"
LOG_DIR = BASE / "logs"
BACKUP_DIR = BASE / "backups"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULTS = {
    "benzinga_enabled": False,
    "benzinga_api_key": "",
        "finnhub_enabled": False,
    "finnhub_api_key": "",
        "finnhub_poll_seconds": 30.0,
    "alphavantage_enabled": False,
    "alphavantage_api_key": "",
        "alphavantage_poll_minutes": 60.0,
    "sec_enabled": True,
        "sec_user_agent": "NewsHound/1.3-hf5 admin@example.com",
    "poll_seconds": 2.0,
    "feed_limit": 250,
    "watch_tickers": ""
}

def ensure_dirs():
    for p in (CONFIG_DIR, DATA_DIR, LOG_DIR, BACKUP_DIR, DATA_DIR/"evidence"):
        p.mkdir(parents=True, exist_ok=True)

def load_config():
    ensure_dirs()
    cfg = DEFAULTS.copy()
    if CONFIG_FILE.exists():
        try:
            cfg.update(json.loads(CONFIG_FILE.read_text()))
        except Exception:
            pass
    # One-time compatibility bridge from v1.0/v1.1 per-source ticker fields.
    if not str(cfg.get("watch_tickers", "")).strip():
        seen = []
        for legacy in ("benzinga_tickers", "finnhub_tickers", "alphavantage_tickers"):
            for raw in str(cfg.get(legacy, "")).split(","):
                ticker = raw.strip().upper()
                if ticker and ticker not in seen:
                    seen.append(ticker)
        if seen:
            cfg["watch_tickers"] = ",".join(seen)
    return cfg

def save_config(updates):
    ensure_dirs()
    cfg = load_config()
    cfg.update(updates)
    tmp = CONFIG_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(cfg, indent=2))
    os.chmod(tmp, 0o600)
    tmp.replace(CONFIG_FILE)
    return cfg

def public_config():
    cfg = load_config()
    return {
        "watch_tickers": cfg.get("watch_tickers", ""),
        "benzinga_enabled": bool(cfg.get("benzinga_enabled")),
        "benzinga_key_set": bool(cfg.get("benzinga_api_key")),
        "finnhub_enabled": bool(cfg.get("finnhub_enabled")),
        "finnhub_key_set": bool(cfg.get("finnhub_api_key")),
        "finnhub_poll_seconds": cfg.get("finnhub_poll_seconds", 30.0),
        "alphavantage_enabled": bool(cfg.get("alphavantage_enabled")),
        "alphavantage_key_set": bool(cfg.get("alphavantage_api_key")),
        "alphavantage_poll_minutes": cfg.get("alphavantage_poll_minutes", 60.0),
        "sec_enabled": bool(cfg.get("sec_enabled")),
        "sec_user_agent": cfg.get("sec_user_agent", ""),
        "poll_seconds": cfg.get("poll_seconds", 2.0),
        "feed_limit": cfg.get("feed_limit", 250),
    }
