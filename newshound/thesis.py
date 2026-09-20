from datetime import datetime, timezone
from pathlib import Path
import hashlib, json, os, re, requests

from .config import DATA_DIR, ensure_dirs, load_config

RESPONSES_URL = "https://api.openai.com/v1/responses"

SYSTEM = """You are Luna, the AI intelligence analyst inside WolfPack NewsHound. Your job is to turn ONE news event into a disciplined, falsifiable market thesis. You are an intelligence analyst, not a trade executor. Never issue an order to buy, sell, long, short, or size a position.

ANALYST INTERROGATION:
1. WHAT HAPPENED? Strip headline language to the new fact.
2. WHAT IS NEW? Separate genuinely new information from known/rumored/previously guided information.
3. WHAT DID THE MARKET EXPECT? State what can be established; if unknown say unknown.
4. EXPECTATION DELTA: Explain the surprise versus prior expectations.
5. ECONOMIC TRANSMISSION: Explain how this could affect revenue, margins, units, pricing, costs, capex, cash flow, balance sheet, competition, regulation, TAM, or cost of capital.
6. MAGNITUDE / MATERIALITY: Normalize impact to the company/sector where possible. Do not invent numbers.
7. TIME HORIZON: Intraday, near-term, quarterly, or long-term.
8. DURABILITY: One-time, temporary, recurring, or structural.
9. EVIDENCE QUALITY: Distinguish primary source, strong secondary, weak secondary, rumor/unverified.
10. WHO ELSE IS AFFECTED? Competitors, suppliers, customers, sector, commodities, rates, currencies when supported.
11. COUNTER-THESIS: Give the strongest evidence-based interpretation against the working thesis.
12. INVALIDATION: State observable facts that would weaken or invalidate the thesis.
13. PRICE EXPECTATION: State what price/volume/structure behavior would SUPPORT the thesis and what behavior would CONTRADICT it. PRICE grades the thesis; indicators do not command it.

RETRIEVAL RULES:
- Start with the supplied NewsHound evidence and original URL.
- If the supplied material is incomplete, use web search to find the original story, primary-source material, and/or reliable corroboration.
- Prefer primary sources (SEC/company/regulator) when available.
- Never fabricate inaccessible article content. If you cannot obtain enough evidence, explicitly say INSUFFICIENT SOURCE ACCESS.
- Treat repeated syndications of the same claim as one evidence lineage, not independent corroboration.
- Distinguish fact, inference, and uncertainty.

Return ONLY valid JSON with these keys:
source_access, retrieval_note, what_happened, what_is_new, market_expectation, expectation_delta, economic_transmission, magnitude_materiality, time_horizon, durability, evidence_quality, affected_entities, counter_thesis, invalidation, price_support, price_contradiction, working_thesis, bias, thesis_state, watch_for, confidence.

Allowed bias: BULLISH, BEARISH, MIXED, NEUTRAL, INSUFFICIENT EVIDENCE.
Allowed thesis_state: DEVELOPING, SUPPORTED, CONTRADICTED, ALREADY PRICED, INSUFFICIENT EVIDENCE.
confidence is an integer 0-100 representing confidence in the analysis, not probability of a price move."""


def _thesis_dir():
    ensure_dirs(); p = DATA_DIR / "theses"; p.mkdir(parents=True, exist_ok=True); return p


def _cache_path(evidence_id):
    safe = re.sub(r"[^A-Za-z0-9_.-]", "", str(evidence_id))[:80]
    return _thesis_dir() / f"{safe}.json"


def get_cached(evidence_id):
    p = _cache_path(evidence_id)
    if not p.exists(): return None
    try: return json.loads(p.read_text(encoding="utf-8"))
    except Exception: return None


def _extract_output_text(resp):
    parts = []
    for item in resp.get("output", []) or []:
        if item.get("type") == "message":
            for c in item.get("content", []) or []:
                if c.get("type") == "output_text" and c.get("text"):
                    parts.append(c["text"])
    return "\n".join(parts).strip()


def _extract_web_sources(resp):
    found = []
    seen = set()
    def add(url, title=""):
        if url and url not in seen:
            seen.add(url); found.append({"url": url, "title": title or url})
    for item in resp.get("output", []) or []:
        if item.get("type") == "web_search_call":
            action = item.get("action") or {}
            for s in action.get("sources", []) or []: add(s.get("url"), s.get("title", ""))
        if item.get("type") == "message":
            for c in item.get("content", []) or []:
                for a in c.get("annotations", []) or []:
                    if a.get("type") == "url_citation": add(a.get("url"), a.get("title", ""))
    return found


def _parse_json(text):
    t = text.strip()
    if t.startswith("```"):
        t = re.sub(r"^```(?:json)?\s*", "", t, flags=re.I); t = re.sub(r"\s*```$", "", t)
    try: return json.loads(t)
    except Exception:
        m = re.search(r"\{.*\}", t, flags=re.S)
        if not m: raise ValueError("AI response was not valid JSON")
        return json.loads(m.group(0))


def analyze_event(event, force=False):
    evidence_id = str(event.get("evidence_id") or "").strip()
    if not evidence_id: raise ValueError("Story has no evidence_id")
    if not force:
        cached = get_cached(evidence_id)
        if cached: return cached

    cfg = load_config()
    api_key = str(cfg.get("openai_api_key") or os.environ.get("OPENAI_API_KEY", "")).strip()
    if not api_key: raise ValueError("No OpenAI API key configured for AI Thesis")
    model = str(cfg.get("openai_model") or "gpt-5.6-luna").strip()

    story = {
        "evidence_id": evidence_id, "source": event.get("source"), "source_id": event.get("source_id"),
        "title": event.get("title"), "summary": event.get("summary"), "url": event.get("url"),
        "tickers": event.get("tickers", []), "category": event.get("category"), "importance": event.get("importance"),
        "published_at": event.get("published_at"), "received_at": event.get("received_at"),
    }
    user = "Analyze this NewsHound event. Use web search when the supplied evidence is not enough to answer the interrogation faithfully.\n\nNEWSHOUND EVIDENCE:\n" + json.dumps(story, ensure_ascii=False, indent=2)
    payload = {"model": model, "instructions": SYSTEM, "input": user, "tools": [{"type":"web_search"}], "store": False}
    r = requests.post(RESPONSES_URL, headers={"Authorization": f"Bearer {api_key}", "Content-Type":"application/json"}, json=payload, timeout=120)
    if r.status_code >= 400:
        try: detail = (r.json().get("error") or {}).get("message") or r.text[:500]
        except Exception: detail = r.text[:500]
        raise RuntimeError(f"OpenAI HTTP {r.status_code}: {detail}")
    raw = r.json(); analysis = _parse_json(_extract_output_text(raw))
    analysis["confidence"] = max(0, min(100, int(analysis.get("confidence", 0) or 0)))
    receipt = {
        "evidence_id": evidence_id, "analyzed_at": datetime.now(timezone.utc).isoformat(), "model": model,
        "story": story, "analysis": analysis, "web_sources": _extract_web_sources(raw),
        "response_id": raw.get("id"), "input_sha256": hashlib.sha256(json.dumps(story, sort_keys=True, ensure_ascii=False).encode()).hexdigest(),
    }
    p = _cache_path(evidence_id); tmp = p.with_suffix(".tmp"); tmp.write_text(json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8"); tmp.replace(p)
    receipts = DATA_DIR / "evidence" / f"thesis-{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.jsonl"
    with receipts.open("a", encoding="utf-8") as f: f.write(json.dumps(receipt, ensure_ascii=False, separators=(",", ":")) + "\n")
    return receipt
