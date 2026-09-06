from collections import deque
from datetime import datetime, timezone
import hashlib, json, threading
from .config import DATA_DIR, ensure_dirs, load_config

_lock = threading.RLock()
_feed = deque(maxlen=500)
_seen = set()
_loaded = False
_status = {
    "running": False,
    "benzinga": "DISABLED",
    "finnhub": "DISABLED",
    "alphavantage": "DISABLED",
    "sec": "DISABLED",
    "last_event": None,
    "started_at": None,
}

def _board_path():
    ensure_dirs()
    return DATA_DIR / "live-feed.json"

def _feed_limit():
    try:
        return max(25, min(int(load_config().get("feed_limit", 250)), 500))
    except Exception:
        return 250

def _persist_board_locked():
    ensure_dirs()
    p = _board_path()
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(list(_feed)[:_feed_limit()], ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    tmp.replace(p)

def _bootstrap_from_evidence(limit):
    evidence_dir = DATA_DIR / "evidence"
    events = []
    for p in sorted(evidence_dir.glob("newshound-*.jsonl"), reverse=True):
        try:
            with p.open("r", encoding="utf-8") as f:
                for line in f:
                    try:
                        e = json.loads(line)
                        if isinstance(e, dict): events.append(e)
                    except Exception:
                        continue
        except OSError:
            continue
    events.sort(key=lambda e: str(e.get("received_at", "")), reverse=True)
    return events[:limit]

def _ensure_loaded():
    global _loaded
    with _lock:
        if _loaded:
            return
        ensure_dirs()
        limit = _feed_limit()
        p = _board_path()
        items = []
        if p.exists():
            try:
                raw = json.loads(p.read_text(encoding="utf-8"))
                if isinstance(raw, list): items = [e for e in raw if isinstance(e, dict)][:limit]
            except Exception:
                items = []
        else:
            # First hf2 launch: recover the newest evidence so an upgrade does not blank the board.
            items = _bootstrap_from_evidence(limit)
        for e in items:
            _feed.append(e)
            raw_key = f"{e.get('source')}|{e.get('source_id')}|{e.get('title')}|{e.get('published_at')}"
            _seen.add(hashlib.sha256(raw_key.encode()).hexdigest())
        if items:
            _status["last_event"] = items[0].get("received_at")
        _loaded = True
        _persist_board_locked()

def status():
    _ensure_loaded()
    with _lock:
        return dict(_status)

def set_status(**kwargs):
    with _lock:
        _status.update(kwargs)

def _evidence_path():
    ensure_dirs()
    day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return DATA_DIR/"evidence"/f"newshound-{day}.jsonl"

def add_event(event):
    _ensure_loaded()
    event = dict(event)
    event.setdefault("received_at", datetime.now(timezone.utc).isoformat())
    raw_key = f"{event.get('source')}|{event.get('source_id')}|{event.get('title')}|{event.get('published_at')}"
    key = hashlib.sha256(raw_key.encode()).hexdigest()
    event["evidence_id"] = key[:16]
    with _lock:
        if key in _seen:
            return False
        _seen.add(key)
        _feed.appendleft(event)
        while len(_feed) > _feed_limit():
            _feed.pop()
        _status["last_event"] = event["received_at"]
        with _evidence_path().open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, separators=(",",":"), ensure_ascii=False) + "\n")
        _persist_board_locked()
    return True

def clear_feed():
    _ensure_loaded()
    with _lock:
        _feed.clear()
        _status["last_event"] = None
        _persist_board_locked()
    return True

def trim_feed():
    _ensure_loaded()
    with _lock:
        while len(_feed) > _feed_limit():
            _feed.pop()
        _persist_board_locked()

def get_feed(limit=100, ticker="", source="", importance=""):
    _ensure_loaded()
    ticker = ticker.upper().strip()
    source = source.upper().strip()
    importance = importance.upper().strip()
    with _lock:
        items = list(_feed)
    out = []
    for e in items:
        tickers = [str(x).upper() for x in e.get("tickers", [])]
        if ticker and ticker not in tickers: continue
        if source and str(e.get("source","")).upper() != source: continue
        if importance and str(e.get("importance","")).upper() != importance: continue
        out.append(e)
        if len(out) >= limit: break
    return out
