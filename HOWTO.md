# 🐺 WolfPack NewsHound — Operator HOWTO

> **Collect the evidence. Designate what matters. Develop the thesis. Preserve the intelligence. Keep the human in command.**

NewsHound is the strategic market-intelligence / ISR component of the WolfPack suite.

This guide covers installation, configuration, routine operation, AI Thesis analysis, finished-intelligence reports, upgrades, and basic troubleshooting.

---

## 1. Install

NewsHound is designed for Linux with Python 3 and systemd.

A typical installation location is:

```text
/opt/wolfpack/newshound
```

From an unpacked NewsHound release:

```bash
chmod +x install.sh
./install.sh
```

The installer creates the Python virtual environment, installs required packages, creates the `newshound.service` systemd unit, and starts NewsHound.

The default local UI is:

```text
http://127.0.0.1:8091
```

Useful operator commands:

```bash
sudo systemctl status newshound --no-pager
sudo systemctl restart newshound
sudo journalctl -u newshound -f
```

---

## 2. Configure NewsHound

Open **SETUP** in the NewsHound UI.

Configure only the providers you intend to use.

NewsHound currently supports collection from:

- Benzinga
- Finnhub
- Alpha Vantage
- SEC EDGAR

Provider API keys, plans, entitlements, rate limits, and availability remain the responsibility of the operator and the respective provider.

NewsHound does not require every source to be enabled. A provider can be unavailable or intentionally disabled while the remaining sensors continue operating.

### AI Thesis

To use AI Thesis, configure an OpenAI API key and desired model through NewsHound's setup interface.

Credentials remain server-side.

**Never commit API keys, populated credentials, `.env` files, or local runtime configuration to Git.**

---

## 3. Read the Operating Picture

The main board contains three functional areas:

- **CONTROL / ADMIN** — source health, configuration, watchlist, and operator controls.
- **LIVE INTELLIGENCE FEED** — collected and classified market intelligence.
- **AI THESIS** — deeper analysis of one operator-designated intelligence event.

The normal operating picture emphasizes the live feed.

The AI Thesis workstation remains hidden until the operator designates a story for deeper exploitation.

NewsHound is an intelligence system.

It is not a trade blotter and does not execute orders.

---

## 4. Designate a Story for AI Thesis

Select **ANALYZE** beside a story.

NewsHound opens the AI Thesis workstation and sends the designated evidence to Luna for deeper interrogation.

Only the selected story is analyzed.

This keeps analysis operator-directed instead of indiscriminately spending AI tokens across the entire intelligence feed.

AI Thesis asks questions such as:

1. What happened?
2. What is genuinely new?
3. What did the market expect?
4. What changed relative to that expectation?
5. What is the economic transmission mechanism?
6. How material is the event?
7. What is the relevant time horizon?
8. Is the effect temporary, recurring, or structural?
9. How strong is the evidence?
10. Who else may be affected?
11. What is the strongest counter-thesis?
12. What observable facts would invalidate the working thesis?
13. What PRICE behavior would support or contradict it?

AI Thesis is deliberately not a:

```text
GOOD NEWS = BUY
BAD NEWS  = SELL
```

classifier.

The objective is to develop a falsifiable working thesis from preserved evidence.

---

## 5. Interpret the Thesis

A completed AI Thesis may include:

- Working bias
- Thesis state
- Confidence
- Time horizon
- Novelty
- Evidence quality
- Economic transmission
- Materiality
- Affected entities
- Counter-thesis
- Invalidation conditions
- Expected PRICE behavior
- Watch items
- Retrieval/source-access notes
- Evidence provenance

### Confidence

Confidence describes confidence in the **analysis**.

It is not a probability that a security will rise or fall.

### Source Access

Depending on available evidence, analysis may rely on:

- Provider-supplied evidence
- Original/canonical story content
- Primary sources
- Corroborating public web sources
- Headline-only evidence

If adequate evidence cannot be obtained, AI Thesis should identify insufficient source access rather than invent inaccessible content.

### PRICE Authority

AI Thesis develops intelligence.

It does not command the market.

**PRICE grades the thesis. Indicators and headlines do not command it.**

---

## 6. Reanalyze with Fresh Evidence

AI Thesis results are cached so an operator can revisit an existing analysis without automatically consuming another model request.

When conditions have changed or additional evidence may now exist, use:

**REANALYZE WITH FRESH EVIDENCE**

This deliberately creates a new analytical pass rather than silently replacing the earlier receipt.

Preserving the earlier analysis makes it possible to compare:

```text
WHAT WAS KNOWN THEN
        ↓
WHAT LUNA CONCLUDED
        ↓
WHAT BECAME KNOWN LATER
        ↓
WHAT PRICE ACTUALLY DID
```

That historical chain is useful for later review and after-action analysis.

---

## 7. Preserve Finished Intelligence

NewsHound v1.3-hf14 adds the ability to promote useful AI Thesis analysis from transient analytical output into an operator-designated finished intelligence product.

Use:

**SAVE REPORT**

to archive the current thesis.

NewsHound creates paired report artifacts beneath:

```text
reports/YYYY/MM/
```

The artifacts serve different purposes:

- **PDF** — human-readable finished intelligence product.
- **JSON** — structured evidence and provenance receipt.

The **Saved Reports** area allows archived products to be retrieved and managed from the UI.

Use:

**EXPORT PDF**

when you want to archive the current thesis and immediately obtain its human-readable PDF report.

### Working Evidence vs. Finished Intelligence

NewsHound intentionally separates working analytical evidence from operator-designated finished intelligence:

```text
data/theses/     working / cached AI Thesis evidence

reports/         operator-designated finished intelligence
```

This distinction is important.

A generated thesis may be useful during live analysis without necessarily deserving permanent promotion into the finished-intelligence archive.

The operator makes that designation.

`reports/` contains runtime/operator artifacts and should not be committed to source control.

---

## 8. Evidence and Provenance

NewsHound is built around evidence engineering.

The general flow is:

```text
COLLECT
   ↓
PRESERVE
   ↓
CLASSIFY
   ↓
INTERROGATE
   ↓
SUBSTANTIATE
   ↓
HUMAN DECISION
```

Where practical, evidence is preserved before downstream presentation decisions.

AI Thesis receipts may retain information such as:

- Story/evidence identity
- Original source
- Ticker or entity context
- Publication timestamp
- Receipt timestamp
- Analysis timestamp
- Model information
- Retrieval/source-access path
- Source URLs
- Response identifiers
- Analytical output
- Counter-thesis
- Invalidation criteria
- Input evidence hash

Primary sources should be preferred when available.

Examples include:

- SEC filings
- Company releases
- Regulatory material
- Other authoritative first-party evidence

Multiple copies of the same syndicated claim should not be mistaken for independent corroboration.

---

## 9. Upgrade NewsHound

Use the bundled updater from the installed application directory:

```bash
cd /opt/wolfpack/newshound
./upgrade-to-1.0.sh /path/to/newshound-release.zip
```

The updater preserves persistent runtime directories and creates a timestamped backup before replacing application files.

### Important: Synchronize Python Dependencies

The current hf14 upgrade path preserves the existing Python virtual environment.

If a release changes `requirements.txt`, synchronize the installed environment with the new requirements:

```bash
cd /opt/wolfpack/newshound
./.venv/bin/pip install -r requirements.txt
```

For the hf14 dependency set, verify the required modules:

```bash
./.venv/bin/python -c \
  "import flask, requests, websocket, langdetect, reportlab; print('Dependencies OK')"
```

Expected result:

```text
Dependencies OK
```

Then restart NewsHound:

```bash
sudo systemctl restart newshound
sudo systemctl status newshound --no-pager
```

### Why This Matters

Application code and its Python environment are separate parts of the deployment.

A new application capability may require a Python package that does not exist in an older virtual environment.

For example, v1.3-hf14 adds ReportLab for PDF report generation.

Installing new application code without installing its new dependency can cause NewsHound to fail during startup with an import error.

Synchronize the environment whenever `requirements.txt` changes.

---

## 10. Benzinga Reconnect and Throttling

NewsHound treats provider failures according to the behavior of the individual provider.

Benzinga WebSocket reconnects use exponential backoff with jitter rather than aggressively reconnecting after failures.

The reconnect sequence increases approximately through:

```text
15s → 30s → 60s → 120s → 300s maximum
```

A repeated HTTP `429` response indicates throttling or rate limiting.

It does not necessarily mean NewsHound itself is broken.

An HTTP `401` is an authentication or authorization response and should be investigated separately from throttling.

Check:

- API key validity
- Provider plan
- Provider entitlement
- Concurrent use of the credential
- Provider-side changes

before assuming a collector defect.

---

## 11. Basic Troubleshooting

When NewsHound behaves unexpectedly, collect evidence before changing things.

### Confirm the installed version

```bash
cat /opt/wolfpack/newshound/VERSION
```

### Check service health

```bash
sudo systemctl status newshound --no-pager
```

### Read recent logs

```bash
sudo journalctl -u newshound -n 100 --no-pager
```

### Follow live logs

```bash
sudo journalctl -u newshound -f
```

### Confirm the listener

```bash
sudo ss -lntp | grep ':8091'
```

### Synchronize dependencies

```bash
cd /opt/wolfpack/newshound
./.venv/bin/pip install -r requirements.txt
```

### Verify hf14 imports

```bash
./.venv/bin/python -c \
  "import flask, requests, websocket, langdetect, reportlab; print('Dependencies OK')"
```

### If the Service Will Not Start

Read the traceback before repeatedly restarting the service:

```bash
sudo journalctl -u newshound -n 100 --no-pager
```

A Python traceback often identifies the actual failure immediately.

The WolfPack troubleshooting doctrine is:

```text
OBSERVE
   ↓
COLLECT RECEIPTS
   ↓
ISOLATE
   ↓
REPAIR
   ↓
VERIFY
```

**Don't guess around the black box. Instrument the black box.**

---

## 12. Runtime Data and Source Control

The public repository should contain application source and documentation.

It should not contain an operator's local intelligence, credentials, or runtime environment.

Do not commit:

- API keys
- `credentials.json`
- Populated runtime configuration
- `.env` files
- Private keys
- Virtual environments
- Runtime evidence
- Generated reports
- Logs
- Local backups
- Python cache files

Typical source-control exclusions include:

```text
.venv/
venv/
__pycache__/
data/
logs/
backups/
reports/
credentials.json
.env
*.key
*.pem
*.log
*.bak
```

The boundary is intentional:

```text
APPLICATION SOURCE  → Git

OPERATOR EVIDENCE   → Local runtime

FINISHED INTEL      → Local report archive

CREDENTIALS         → Private
```

---

## 13. Human Authority

NewsHound is an intelligence-analysis system.

It is not a broker, investment adviser, autonomous trading system, or substitute for professional financial, legal, tax, accounting, or compliance advice.

AI output can be:

- Wrong
- Incomplete
- Stale
- Misleading
- Fabricated

Verify important evidence and conclusions independently.

NewsHound develops intelligence.

**The human operator decides what to do with it.**

---

## Quick Reference

```bash
# Status
sudo systemctl status newshound --no-pager

# Restart
sudo systemctl restart newshound

# Live logs
sudo journalctl -u newshound -f

# Recent logs
sudo journalctl -u newshound -n 100 --no-pager

# Listener
sudo ss -lntp | grep ':8091'

# Version
cat /opt/wolfpack/newshound/VERSION

# Update Python environment
cd /opt/wolfpack/newshound
./.venv/bin/pip install -r requirements.txt

# Verify hf14 dependencies
./.venv/bin/python -c \
  "import flask, requests, websocket, langdetect, reportlab; print('Dependencies OK')"
```

---

## WolfPack Doctrine

**Source first.**

**Preserve the evidence.**

**AI develops the thesis.**

**Counter-thesis keeps us intellectually honest.**

**PRICE grades the thesis.**

**Human authority is retained.**

**Semper Preserve The Damn Intelligence. Semper Receipts. Semper Build Cool Shit.** 🐺
