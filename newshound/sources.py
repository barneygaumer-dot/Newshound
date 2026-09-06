import json, threading, time
from datetime import datetime, timezone, timedelta
import requests
import websocket

from .config import load_config
from .store import add_event, set_status
from .classify import infer_importance, category


def _tickers(value):
    return list(dict.fromkeys(x.strip().upper() for x in str(value or "").split(",") if x.strip()))


def _unix_iso(value):
    try:
        return datetime.fromtimestamp(int(value), tz=timezone.utc).isoformat()
    except Exception:
        return ""


def _alpha_iso(value):
    s = str(value or "").strip()
    for fmt in ("%Y%m%dT%H%M%S", "%Y%m%dT%H%M"):
        try:
            return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc).isoformat()
        except ValueError:
            pass
    return s


def _alpha_event_tickers(item):
    out = []
    for x in item.get("ticker_sentiment") or []:
        if isinstance(x, dict) and x.get("ticker"):
            out.append(str(x["ticker"]).upper())
    return out


class SourceManager:
    def __init__(self):
        self.stop_event = threading.Event()
        self.threads = []
        self.running = False
        self.sec_seen = {}
        self.finnhub_seen = {}
        # Per-symbol baselines prevent one ticker's Alpha Vantage results from
        # suppressing another ticker during fan-out polling.
        self.alpha_seen = {}
        self.generation = 0
        self._sec_map = {}
        self._sec_map_loaded = 0.0
        # Benzinga dev accounts are sensitive to overlapping WebSocket sessions.
        # Keep the active socket so restart/stop can close it before a replacement
        # connection is launched.
        self._benzinga_ws = None
        self._benzinga_ws_lock = threading.Lock()

    def start(self):
        if self.running:
            return
        self.stop_event.clear()
        self.running = True
        set_status(running=True, started_at=datetime.now(timezone.utc).isoformat())
        cfg = load_config()
        watch = _tickers(cfg.get("watch_tickers"))

        if cfg.get("benzinga_enabled") and cfg.get("benzinga_api_key") and watch:
            self._launch(self._benzinga_loop, "benzinga-ws")
        elif not cfg.get("benzinga_enabled"):
            set_status(benzinga="DISABLED")
        elif not cfg.get("benzinga_api_key"):
            set_status(benzinga="NO KEY")
        else:
            set_status(benzinga="NO WATCHLIST")

        if cfg.get("finnhub_enabled") and cfg.get("finnhub_api_key") and watch:
            self._launch(self._finnhub_loop, "finnhub-poll")
        elif not cfg.get("finnhub_enabled"):
            set_status(finnhub="DISABLED")
        elif not cfg.get("finnhub_api_key"):
            set_status(finnhub="NO KEY")
        else:
            set_status(finnhub="NO WATCHLIST")

        if cfg.get("alphavantage_enabled") and cfg.get("alphavantage_api_key") and watch:
            self._launch(self._alphavantage_loop, "alphavantage-poll")
        elif not cfg.get("alphavantage_enabled"):
            set_status(alphavantage="DISABLED")
        elif not cfg.get("alphavantage_api_key"):
            set_status(alphavantage="NO KEY")
        else:
            set_status(alphavantage="NO WATCHLIST")

        if cfg.get("sec_enabled") and watch:
            self._launch(self._sec_loop, "sec-poll")
        else:
            set_status(sec="DISABLED" if not cfg.get("sec_enabled") else "NO WATCHLIST")

    def _launch(self, target, name):
        generation = self.generation
        t = threading.Thread(target=lambda: target(generation), daemon=True, name=name)
        t.start()
        self.threads.append(t)

    def stop(self):
        self.generation += 1
        self.stop_event.set()

        # IMPORTANT: close Benzinga synchronously before another generation can
        # connect.  Merely setting stop_event does not interrupt run_forever(),
        # which can leave the old WebSocket alive long enough for Benzinga to
        # reject the replacement session with HTTP 429.
        with self._benzinga_ws_lock:
            ws = self._benzinga_ws
        if ws is not None:
            try:
                ws.close()
            except Exception:
                pass

        self.running = False
        set_status(running=False)

    def restart(self):
        self.stop()

        # Give the old Benzinga worker a chance to finish its close handshake
        # before stop_event is cleared by start().  Other source workers are
        # generation-guarded and continue to use the existing restart behavior.
        for t in list(self.threads):
            if t.name == "benzinga-ws" and t.is_alive():
                t.join(timeout=3.0)

        self.threads = []
        self.start()

    def _benzinga_loop(self, generation):
        while not self.stop_event.is_set() and generation == self.generation:
            cfg = load_config()
            key = cfg.get("benzinga_api_key", "").strip()
            tickers = ",".join(_tickers(cfg.get("watch_tickers")))
            if not key:
                set_status(benzinga="NO KEY"); return
            if not tickers:
                set_status(benzinga="NO WATCHLIST"); return
            url = f"wss://api.benzinga.com/api/v1/news/stream?token={key}&tickers={requests.utils.quote(tickers, safe=',')}"
            try:
                set_status(benzinga="CONNECTING")
                def current_generation():
                    return generation == self.generation and not self.stop_event.is_set()
                def on_open(ws):
                    if current_generation():
                        set_status(benzinga="CONNECTED")
                def on_message(ws, message):
                    if not current_generation():
                        return
                    try:
                        envelope = json.loads(message)
                        data = envelope.get("data", {})
                        content = data.get("content", {}) or {}
                        if data.get("action") == "deleted": return
                        stocks = content.get("stocks") or []
                        syms = [s.get("name") for s in stocks if isinstance(s, dict) and s.get("name")]
                        title = content.get("title", "")
                        add_event({"source":"BENZINGA","source_type":"WIRE","source_id":str(content.get("id") or data.get("id") or envelope.get("id")),
                                   "published_at":content.get("created") or data.get("timestamp"),"updated_at":content.get("updated"),
                                   "title":title,"summary":content.get("teaser", ""),"url":content.get("url", ""),"author":content.get("author", ""),
                                   "tickers":syms,"importance":infer_importance(title, content.get("importance")),"category":category(title, content.get("tags")),
                                   "action":data.get("action", "created")})
                    except Exception as e:
                        if current_generation():
                            set_status(benzinga=f"PARSE ERROR: {type(e).__name__}")
                def on_error(ws, err):
                    if current_generation():
                        set_status(benzinga=f"ERROR: {str(err)[:80]}")
                def on_close(ws, code, msg):
                    if current_generation():
                        set_status(benzinga=f"RECONNECTING ({code or '-'})")
                ws = websocket.WebSocketApp(url, on_open=on_open, on_message=on_message, on_error=on_error, on_close=on_close)
                with self._benzinga_ws_lock:
                    self._benzinga_ws = ws
                try:
                    ws.run_forever(ping_interval=20, ping_timeout=10)
                finally:
                    with self._benzinga_ws_lock:
                        if self._benzinga_ws is ws:
                            self._benzinga_ws = None
            except Exception as e:
                set_status(benzinga=f"ERROR: {type(e).__name__}")
            self.stop_event.wait(3)

    def _finnhub_loop(self, generation):
        """Poll Finnhub one symbol at a time.

        A failure/rate-limit on one symbol must not abort the rest of the watchlist.
        Status includes sweep coverage so the UI can distinguish "no news" from
        "was never queried".
        """
        session = requests.Session()
        while not self.stop_event.is_set() and generation == self.generation:
            cfg = load_config()
            key = str(cfg.get("finnhub_api_key", "")).strip()
            symbols = _tickers(cfg.get("watch_tickers"))
            if not key: set_status(finnhub="NO KEY"); return
            if not symbols: set_status(finnhub="NO WATCHLIST"); return

            completed = 0
            errors = 0
            today = datetime.now(timezone.utc).date()
            from_day = (today - timedelta(days=1)).isoformat()
            to_day = today.isoformat()
            set_status(finnhub=f"POLLING 0/{len(symbols)}")

            for symbol in symbols:
                if self.stop_event.is_set() or generation != self.generation:
                    break
                try:
                    r = session.get(
                        "https://finnhub.io/api/v1/company-news",
                        params={"symbol": symbol, "from": from_day, "to": to_day, "token": key},
                        timeout=10,
                    )
                    r.raise_for_status()
                    items = r.json()
                    if not isinstance(items, list):
                        raise ValueError("unexpected Finnhub response")

                    ids = [str(x.get("id")) for x in items if isinstance(x, dict) and x.get("id") is not None]
                    baseline = self.finnhub_seen.get(symbol)
                    if baseline is None:
                        # First observation establishes a no-replay baseline.
                        self.finnhub_seen[symbol] = set(ids[:200])
                    else:
                        for item in reversed(items[:100]):
                            if not isinstance(item, dict): continue
                            sid = str(item.get("id") or "")
                            if not sid or sid in baseline: continue
                            title = str(item.get("headline") or "")
                            related = [x.strip().upper() for x in str(item.get("related") or "").split(",") if x.strip()]
                            # The queried company is always part of this company-news request;
                            # retain Finnhub's related symbols as additional attribution.
                            syms = list(dict.fromkeys([symbol] + related))
                            add_event({"source":"FINNHUB","source_type":"AGGREGATOR","source_id":sid,
                                       "published_at":_unix_iso(item.get("datetime")),"title":title,
                                       "summary":str(item.get("summary") or ""),"url":str(item.get("url") or ""),
                                       "author":str(item.get("source") or ""),"tickers":syms,
                                       "importance":infer_importance(title),"category":category(title)})
                            baseline.add(sid)
                        self.finnhub_seen[symbol] = set(ids[:200])
                    completed += 1
                except requests.HTTPError:
                    errors += 1
                except Exception:
                    errors += 1

                set_status(finnhub=f"POLLING {completed}/{len(symbols)}" + (f" / ERR {errors}" if errors else ""))
                if self.stop_event.wait(.35): break

            if not self.stop_event.is_set() and generation == self.generation:
                if errors:
                    set_status(finnhub=f"CONNECTED {completed}/{len(symbols)} / ERR {errors}")
                else:
                    set_status(finnhub=f"CONNECTED {completed}/{len(symbols)}")
            self.stop_event.wait(max(15.0, min(float(cfg.get("finnhub_poll_seconds", 30.0)), 300.0)))

    def _alphavantage_loop(self, generation):
        """Fan out Alpha Vantage NEWS_SENTIMENT as one ticker per request.

        Alpha's comma-separated ticker filter is not an OR-style watchlist query,
        so Market ISR deliberately polls each symbol independently. Requests are
        paced to avoid a burst, and a provider rate/plan notice ends the current
        sweep rather than manufacturing partial attribution.
        """
        session = requests.Session()
        while not self.stop_event.is_set() and generation == self.generation:
            cfg = load_config()
            key = str(cfg.get("alphavantage_api_key", "")).strip()
            symbols = _tickers(cfg.get("watch_tickers"))
            if not key: set_status(alphavantage="NO KEY"); return
            if not symbols: set_status(alphavantage="NO WATCHLIST"); return

            completed = 0
            errors = 0
            rate_notice = False
            set_status(alphavantage=f"POLLING 0/{len(symbols)}")

            for symbol in symbols:
                if self.stop_event.is_set() or generation != self.generation:
                    break
                try:
                    r = session.get(
                        "https://www.alphavantage.co/query",
                        params={"function":"NEWS_SENTIMENT","tickers":symbol,"sort":"LATEST","limit":200,"apikey":key},
                        timeout=15,
                    )
                    r.raise_for_status()
                    j = r.json()
                    if j.get("Error Message"):
                        raise ValueError("API error")
                    if j.get("Information") and not isinstance(j.get("feed"), list):
                        rate_notice = True
                        set_status(alphavantage=f"RATE/PLAN NOTICE {completed}/{len(symbols)}")
                        break

                    items = j.get("feed") or []
                    if not isinstance(items, list):
                        raise ValueError("unexpected Alpha Vantage response")
                    ids = [str(x.get("url") or "") for x in items if isinstance(x, dict) and x.get("url")]
                    baseline = self.alpha_seen.get(symbol)
                    if baseline is None:
                        self.alpha_seen[symbol] = set(ids[:500])
                    else:
                        for item in reversed(items[:200]):
                            if not isinstance(item, dict): continue
                            sid = str(item.get("url") or "")
                            if not sid or sid in baseline: continue
                            syms = _alpha_event_tickers(item)
                            # Do not stamp the queried symbol onto a generic story. Alpha's
                            # own ticker_sentiment must confirm attribution.
                            if symbol not in syms:
                                baseline.add(sid)
                                continue
                            title = str(item.get("title") or "")
                            add_event({"source":"ALPHAVANTAGE","source_type":"AGGREGATOR","source_id":sid,
                                       "published_at":_alpha_iso(item.get("time_published")),"title":title,
                                       "summary":str(item.get("summary") or ""),"url":sid,
                                       "author":str(item.get("source") or ""),"tickers":syms,
                                       "importance":infer_importance(title),"category":category(title, item.get("topics"))})
                            baseline.add(sid)
                        self.alpha_seen[symbol] = set(ids[:500]) | baseline.intersection(set(ids[:1000]))
                    completed += 1
                except requests.HTTPError:
                    errors += 1
                except Exception:
                    errors += 1

                set_status(alphavantage=f"POLLING {completed}/{len(symbols)}" + (f" / ERR {errors}" if errors else ""))
                # Pace per-symbol fan-out. This is intentionally conservative and
                # provider notices still take precedence for the account's actual plan.
                if self.stop_event.wait(1.0): break

            if not self.stop_event.is_set() and generation == self.generation and not rate_notice:
                if errors:
                    set_status(alphavantage=f"CONNECTED {completed}/{len(symbols)} / ERR {errors}")
                else:
                    set_status(alphavantage=f"CONNECTED {completed}/{len(symbols)}")

            # alphavantage_poll_minutes is the interval between complete sweeps.
            self.stop_event.wait(max(60.0, min(float(cfg.get("alphavantage_poll_minutes",60.0)),1440.0))*60.0)

    def _get_sec_map(self, session, ua):
        if self._sec_map and (time.time() - self._sec_map_loaded) < 21600:
            return self._sec_map
        r = session.get("https://www.sec.gov/files/company_tickers.json", headers={"User-Agent":ua,"Accept-Encoding":"gzip, deflate"}, timeout=10)
        r.raise_for_status(); raw = r.json(); mapping = {}
        for row in raw.values() if isinstance(raw, dict) else []:
            if isinstance(row, dict) and row.get("ticker") and row.get("cik_str") is not None:
                mapping[str(row["ticker"]).upper()] = str(row["cik_str"]).zfill(10)
        self._sec_map = mapping; self._sec_map_loaded = time.time(); return mapping

    def resolve_sec_ciks(self, symbols, ua):
        session = requests.Session(); mapping = self._get_sec_map(session, ua)
        return [(s, mapping.get(s)) for s in symbols if mapping.get(s)]

    def _sec_loop(self, generation):
        session = requests.Session()
        while not self.stop_event.is_set() and generation == self.generation:
            cfg = load_config(); ua = cfg.get("sec_user_agent", "").strip(); symbols = _tickers(cfg.get("watch_tickers"))
            if not ua or "@" not in ua:
                set_status(sec="USER-AGENT NEEDS CONTACT EMAIL"); self.stop_event.wait(5); continue
            if not symbols:
                set_status(sec="NO WATCHLIST"); return
            try:
                set_status(sec="RESOLVING TICKERS")
                mapping = self._get_sec_map(session, ua)
                pairs = [(s, mapping.get(s)) for s in symbols]
                missing = [s for s, cik in pairs if not cik]
                pairs = [(s, cik) for s, cik in pairs if cik]
                if not pairs:
                    set_status(sec="NO SEC TICKER MATCHES"); self.stop_event.wait(30); continue
                set_status(sec="POLLING" + (f" / MISS {','.join(missing[:3])}" if missing else ""))
                for wanted_ticker, cik in pairs:
                    if self.stop_event.is_set(): break
                    r = session.get(f"https://data.sec.gov/submissions/CIK{cik}.json", headers={"User-Agent":ua,"Accept-Encoding":"gzip, deflate"}, timeout=8)
                    r.raise_for_status(); j = r.json(); rec = (j.get("filings") or {}).get("recent") or {}
                    accessions = rec.get("accessionNumber") or []; forms = rec.get("form") or []; dates = rec.get("filingDate") or []
                    docs = rec.get("primaryDocument") or []; accepted = rec.get("acceptanceDateTime") or []; name = j.get("name", "")
                    baseline = self.sec_seen.get(cik)
                    if baseline is None:
                        self.sec_seen[cik] = set(accessions[:50]); continue
                    for i, acc in enumerate(accessions[:25]):
                        if acc in baseline: continue
                        form = forms[i] if i < len(forms) else ""; doc = docs[i] if i < len(docs) else ""; accnodash = acc.replace("-", "")
                        url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accnodash}/{doc}" if doc else ""
                        title = f"{wanted_ticker}: new SEC {form} filing"
                        add_event({"source":"SEC","source_type":"PRIMARY","source_id":acc,
                                   "published_at":accepted[i] if i < len(accepted) else (dates[i] if i < len(dates) else ""),
                                   "title":title,"summary":f"{name} filed Form {form} with the SEC.","url":url,"tickers":[wanted_ticker],
                                   "importance":infer_importance(title),"category":category(title, form=form)})
                        baseline.add(acc)
                    self.sec_seen[cik] = set(accessions[:50]); time.sleep(.12)
                set_status(sec="CONNECTED" + (f" / MISS {','.join(missing[:3])}" if missing else ""))
            except Exception as e:
                set_status(sec=f"ERROR: {type(e).__name__}")
            self.stop_event.wait(max(1.0, float(cfg.get("poll_seconds", 2.0))))
