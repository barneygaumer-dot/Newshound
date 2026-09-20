from datetime import datetime, timezone
from pathlib import Path
import hashlib, json, re

from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak

from .config import BASE

REPORTS_DIR = BASE / "reports"

FIELDS = [
    ("WHAT HAPPENED", "what_happened"),
    ("WHAT'S NEW", "what_is_new"),
    ("MARKET EXPECTATION", "market_expectation"),
    ("EXPECTATION DELTA", "expectation_delta"),
    ("ECONOMIC TRANSMISSION", "economic_transmission"),
    ("MAGNITUDE / MATERIALITY", "magnitude_materiality"),
    ("TIME HORIZON", "time_horizon"),
    ("DURABILITY", "durability"),
    ("EVIDENCE QUALITY", "evidence_quality"),
    ("WHO ELSE IS AFFECTED", "affected_entities"),
    ("COUNTER-THESIS", "counter_thesis"),
    ("INVALIDATION", "invalidation"),
    ("PRICE WOULD SUPPORT", "price_support"),
    ("PRICE WOULD CONTRADICT", "price_contradiction"),
    ("WORKING THESIS", "working_thesis"),
    ("WATCH FOR", "watch_for"),
]

def _safe(value, fallback="report"):
    value = re.sub(r"[^A-Za-z0-9._-]+", "-", str(value or "").strip()).strip("-._")
    return (value[:80] or fallback)

def _report_dir(now=None):
    now = now or datetime.now(timezone.utc)
    p = REPORTS_DIR / now.strftime("%Y") / now.strftime("%m")
    p.mkdir(parents=True, exist_ok=True)
    return p

def _story_label(receipt):
    s = receipt.get("story") or {}
    tickers = s.get("tickers") or []
    if tickers:
        return "-".join(_safe(x, "TICKER") for x in tickers[:3])
    return _safe(s.get("source") or "NEWS")

def _make_stem(receipt, now=None):
    now = now or datetime.now(timezone.utc)
    return f"{now.strftime('%Y-%m-%d_%H%M%S')}_{_story_label(receipt)}_AI-Thesis"

def _xml(text):
    return (str(text or "—").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            .replace("\n", "<br/>"))

def _build_pdf(path, receipt):
    styles = getSampleStyleSheet()
    title = ParagraphStyle("NHTitle", parent=styles["Title"], fontSize=18, leading=22, spaceAfter=8)
    meta = ParagraphStyle("NHMeta", parent=styles["Normal"], fontSize=8.5, leading=11, textColor="#52616b", spaceAfter=9)
    heading = ParagraphStyle("NHHeading", parent=styles["Heading2"], fontSize=10, leading=13, spaceBefore=9, spaceAfter=4)
    body = ParagraphStyle("NHBody", parent=styles["BodyText"], fontSize=9.5, leading=13, spaceAfter=5)
    footer = ParagraphStyle("NHFooter", parent=styles["Normal"], fontSize=7.5, leading=10, alignment=TA_CENTER, textColor="#66737b")
    story = receipt.get("story") or {}; a = receipt.get("analysis") or {}
    tickers = " · ".join(story.get("tickers") or [])
    headline = story.get("title") or "NewsHound AI Thesis"
    doc = SimpleDocTemplate(str(path), pagesize=letter, rightMargin=.65*inch, leftMargin=.65*inch, topMargin=.6*inch, bottomMargin=.6*inch,
                            title=f"NewsHound AI Thesis - {headline}", author="WolfPack NewsHound")
    flow = [Paragraph("WOLFPACK NEWSHOUND — AI THESIS", title),
            Paragraph(_xml((tickers + " — " if tickers else "") + headline), styles["Heading1"]),
            Paragraph(_xml(f"Source: {story.get('source') or '—'} | Published: {story.get('published_at') or '—'} | Analyzed: {receipt.get('analyzed_at') or '—'} | Model: {receipt.get('model') or '—'} | Evidence ID: {receipt.get('evidence_id') or '—'}"), meta)]
    for label, key in FIELDS:
        flow += [Paragraph(label, heading), Paragraph(_xml(a.get(key)), body)]
    flow += [Spacer(1, 8), Paragraph("ANALYST VERDICT", heading),
             Paragraph(_xml(f"Bias: {a.get('bias','—')} | State: {a.get('thesis_state','—')} | Confidence: {a.get('confidence','—')}% | Source access: {a.get('source_access','—')}"), body),
             Paragraph("RETRIEVAL NOTE", heading), Paragraph(_xml(a.get("retrieval_note")), body)]
    sources = receipt.get("web_sources") or []
    if sources:
        flow.append(Paragraph("WEB EVIDENCE USED", heading))
        for src in sources:
            flow.append(Paragraph(_xml(f"{src.get('title') or src.get('url') or 'Source'} — {src.get('url') or ''}"), body))
    flow += [Spacer(1, 12), Paragraph("NewsHound develops intelligence; it does not place trades. AI output may be incomplete or inaccurate. Verify source evidence before relying on the thesis.", footer)]
    doc.build(flow)

def save_report(receipt):
    now = datetime.now(timezone.utc); directory = _report_dir(now); stem = _make_stem(receipt, now)
    pdf_path = directory / f"{stem}.pdf"; json_path = directory / f"{stem}.json"
    archive = {
        "report_type": "NEWSHOUND_AI_THESIS", "saved_at": now.isoformat(), "report_name": stem,
        "receipt": receipt,
    }
    encoded = json.dumps(archive, indent=2, ensure_ascii=False).encode("utf-8")
    archive["archive_sha256"] = hashlib.sha256(encoded).hexdigest()
    tmp = json_path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(archive, indent=2, ensure_ascii=False), encoding="utf-8"); tmp.replace(json_path)
    _build_pdf(pdf_path, receipt)
    return {"name": stem, "saved_at": archive["saved_at"], "pdf": pdf_path.name, "json": json_path.name}

def list_reports(limit=20):
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    out = []
    for p in REPORTS_DIR.glob("*/*/*.json"):
        try:
            j = json.loads(p.read_text(encoding="utf-8")); receipt = j.get("receipt") or {}; story = receipt.get("story") or {}
            out.append({"name": p.stem, "saved_at": j.get("saved_at"), "title": story.get("title"), "tickers": story.get("tickers") or [], "source": story.get("source"), "year": p.parent.parent.name, "month": p.parent.name})
        except Exception:
            continue
    out.sort(key=lambda x: x.get("saved_at") or "", reverse=True)
    return out[:max(1, min(int(limit), 100))]

def find_report(name, fmt):
    safe = _safe(name)
    if safe != name or fmt not in ("pdf", "json"):
        return None
    matches = list(REPORTS_DIR.glob(f"*/*/{safe}.{fmt}"))
    return matches[0] if len(matches) == 1 else None

def delete_report(name):
    safe = _safe(name)
    if safe != name: return False
    found = False
    for ext in ("pdf", "json"):
        for p in REPORTS_DIR.glob(f"*/*/{safe}.{ext}"):
            p.unlink(missing_ok=True); found = True
    return found
