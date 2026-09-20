# 🐺 WolfPack NewsHound

> **Source-first market intelligence. Evidence before narrative. Human authority retained.**

NewsHound is the strategic market-intelligence / ISR component of the WolfPack suite.

It collects market-moving information from multiple providers, preserves the evidence, classifies what matters, and gives the operator a deliberate AI-assisted workflow for developing a defensible market thesis.

NewsHound does **not** execute trades.

Its job is intelligence.

**Collect the evidence. Designate what matters. Develop the thesis. Preserve the intelligence. Keep the human in command.**

---

## Why NewsHound Exists

Markets produce an enormous amount of information.

Most of it is noise.

NewsHound is designed to help answer a more useful set of questions:

- What actually happened?
- What is genuinely new?
- What did the market probably expect?
- What changed relative to that expectation?
- How could that change affect the business or security?
- Is the information economically material?
- Is the effect likely transient or durable?
- What evidence supports the thesis?
- What evidence contradicts it?
- What would invalidate it?
- What should PRICE do if the thesis is correct?

The objective is not to have AI pronounce something *good* or *bad*.

The objective is to turn preserved evidence into an inspectable working thesis.

---

## Operating Picture

NewsHound follows a simple intelligence lifecycle:

```text
COLLECT
   ↓
PRESERVE
   ↓
CLASSIFY
   ↓
DISPLAY
   ↓
OPERATOR DESIGNATION
   ↓
AI THESIS
   ↓
FINISHED INTELLIGENCE
```

Collectors gather evidence independently.

NewsHound preserves what was received before downstream interpretation wherever practical. Classification and display logic operate on that evidence without redefining what the collector was allowed to see.

The operator decides which story deserves deeper exploitation.

AI assists with reasoning.

The operator retains authority.

---

## Core Features

- Multi-source market-news collection
- SEC filing awareness
- Source-first evidence preservation
- Importance and category classification
- Ticker/watchlist filtering
- Provider-specific configuration
- Benzinga streaming support
- Benzinga reconnect throttling and exponential backoff
- Finnhub collection
- Alpha Vantage collection
- SEC collection
- Operator-designated AI Thesis analysis
- Web-assisted evidence retrieval when configured
- Thesis caching and deliberate reanalysis
- Evidence/provenance receipts
- Persistent finished-intelligence report archive
- Human-readable PDF reports
- Structured JSON report artifacts
- Saved-report retrieval and deletion
- Local browser-based operator interface
- Human authority over every analytical conclusion

---

## AI Thesis

AI Thesis is an operator-designated analytical workflow.

NewsHound does **not** automatically spend AI resources analyzing every incoming story. The operator selects evidence that appears worthy of exploitation and explicitly requests analysis.

The analytical framework asks:

1. **What happened?**
2. **What is actually new?**
3. **What did the market expect?**
4. **What changed relative to expectation?**
5. **What is the economic transmission mechanism?**
6. **How material is the change?**
7. **What is the likely time horizon?**
8. **How durable is the effect?**
9. **How strong is the evidence?**
10. **Who else may be affected?**
11. **What is the counter-thesis?**
12. **What would invalidate the thesis?**
13. **What should PRICE do if the thesis is correct?**
14. **What is the resulting working thesis?**

AI Thesis can also expose analytical metadata such as:

- Bias
- Horizon
- Novelty
- Evidence Quality
- Thesis State
- Confidence
- What to Watch

A thesis is not a trade order.

It is an analytical product to be tested against evidence and subsequent market behavior.

**PRICE grades the thesis.**

---

## Evidence Philosophy

NewsHound is built around evidence engineering.

When deeper analysis is requested, the system can use available provider content, canonical story URLs, public web evidence, SEC material, and other accessible corroborating sources.

If source content cannot be retrieved, that limitation should remain visible rather than being silently replaced with invented certainty.

Useful provenance can include:

- Story ID
- Original URL
- Publisher/source
- Ticker or entity context
- Publication timestamp
- Receipt timestamp
- Analysis timestamp
- Retrieval/source-access path
- Evidence URLs
- Model information
- Working thesis
- Counter-thesis
- Invalidation criteria

The goal is simple:

> **Preserve enough evidence to understand later why the system believed what it believed.**

---

## AI Thesis Report Archive

Beginning with **v1.3-hf14**, an operator can promote a useful AI Thesis into persistent finished intelligence.

Reports are stored beneath:

```text
reports/YYYY/MM/
```

Each archived report consists of paired artifacts:

- **PDF** — human-readable finished intelligence product.
- **JSON** — structured evidence and provenance receipt.

The UI provides:

- **SAVE REPORT**
- **EXPORT PDF**
- **Saved Reports**
- PDF retrieval
- JSON retrieval
- Operator-controlled deletion

Working analytical evidence and finished intelligence remain intentionally separate:

```text
data/theses/     working / cached analytical evidence
reports/         operator-designated finished intelligence
```

That separation is deliberate.

Not every transient analysis deserves permanent promotion. The operator decides what becomes finished intelligence.

This archive also creates a foundation for future after-action review: historical theses can be compared against subsequent PRICE behavior to evaluate what the analysis got right, what it missed, and why.

---

## Installation

NewsHound is designed for Linux with Python 3 and systemd.

A typical installation location is:

```text
/opt/wolfpack/newshound
```

From an unpacked release:

```bash
chmod +x install.sh
./install.sh
```

The installer creates the application environment and supporting service configuration required by NewsHound.

The default local UI is:

```text
http://127.0.0.1:8091
```

Useful service commands:

```bash
sudo systemctl status newshound --no-pager
sudo systemctl restart newshound
sudo journalctl -u newshound -f
```

For complete installation and operating instructions, see [`HOWTO.md`](HOWTO.md).

---

## Upgrade

NewsHound includes an upgrade script:

```bash
chmod +x upgrade-to-1.0.sh
./upgrade-to-1.0.sh
```

The updater preserves persistent runtime material such as configuration, data, logs, backups, reports, and the existing virtual environment while deploying the release files.

### Dependency changes

Because the virtual environment is preserved, a release that changes `requirements.txt` may require the installed environment to be synchronized manually.

For v1.3-hf14:

```bash
cd /opt/wolfpack/newshound
./.venv/bin/pip install -r requirements.txt
sudo systemctl restart newshound
sudo systemctl status newshound --no-pager
```

v1.3-hf14 adds **ReportLab** for PDF report generation.

Automated dependency preflight and environment synchronization are intentionally deferred to separately tested maintenance work rather than being introduced as an untested change to the known-good hf14 release.

See [`HOWTO.md`](HOWTO.md) and [`RELEASE-NOTES-1.3-hf14.md`](RELEASE-NOTES-1.3-hf14.md) for additional upgrade information.

---

## Configuration

Use **SETUP** in the NewsHound UI to configure enabled providers, API credentials, watchlist behavior, and provider-specific options.

AI Thesis requires an OpenAI API key and configured model.

Credentials are intended to remain local and server-side.

**Never commit credentials, API keys, local configuration, or runtime evidence to source control.**

Provider access, entitlements, rate limits, and API behavior remain subject to the respective third-party provider.

---

## Project Layout

```text
newshound/
├── run.py
├── requirements.txt
├── VERSION
├── install.sh
├── upgrade-to-1.0.sh
├── LICENSE
├── DISCLAIMER.md
├── README.md
├── HOWTO.md
├── RELEASE-NOTES-1.3-hf14.md
├── config/
└── newshound/
    ├── __init__.py
    ├── app.py          # Flask/API surface
    ├── classify.py     # importance/category classification
    ├── config.py       # application configuration
    ├── reports.py      # finished-intelligence report archive
    ├── sources.py      # provider collectors
    ├── store.py        # evidence/feed persistence
    ├── thesis.py       # AI Thesis analysis
    ├── static/
    └── templates/
```

Runtime/generated material such as the following should remain outside source control:

```text
data/
logs/
backups/
reports/
.venv/
venv/
credentials.json
```

---

## Architecture in the WolfPack Suite

NewsHound is one component of a larger evidence-driven market-intelligence architecture.

```text
MARKET BATTLESPACE
        │
        ▼
┌─────────────────────┐
│      NEWSHOUND      │
│   Strategic ISR     │
│                     │
│ What happened?      │
│ Why might it matter?│
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ ISR MARKET SCANNER  │
│      "AWACS"        │
│                     │
│ What is moving?     │
│ Where is opportunity│
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│    MARKET REAPER    │
│ Tactical Analysis   │
│                     │
│ Is there a qualified│
│ engagement now?     │
└──────────┬──────────┘
           │
           ▼
      HUMAN AUTHORITY
```

The operating doctrine:

> **RQ-4 hears why. AWACS sees what. Reaper determines when.**

NewsHound develops strategic intelligence.

The ISR Market Scanner surveys the wider market for technical opportunity.

Market Reaper evaluates tactical conditions.

The human operator retains decision authority.

---

## Provider Behavior

NewsHound's collectors are intentionally independent.

Failure, throttling, or loss of entitlement at one provider should not redefine the evidence received from another provider.

### Benzinga

Benzinga streaming support includes reconnect throttling with exponential backoff and jitter.

HTTP/API conditions matter:

- **401** generally indicates an authentication or entitlement problem.
- **429** indicates provider throttling/rate limiting.

NewsHound responds to throttling by backing off rather than hammering the provider with aggressive reconnect attempts.

Benzinga is optional. Provider access may require an appropriate subscription or entitlement.

### Other Sources

NewsHound also supports collection paths for sources including:

- Finnhub
- Alpha Vantage
- SEC

Provider behavior, availability, limits, licensing, and terms remain controlled by those providers.

---

## Built by Curiosity

NewsHound is a WolfPack project from **W6 + Kato**: operator mission intent meeting rapid engineering.

The operating philosophy is straightforward:

- Build useful tools for regular folks.
- Prefer primary sources and preserved evidence over vibes.
- Let AI reason, but make its work inspectable.
- Keep the human in command.
- When something breaks, lift the hood and get receipts.
- Coolness is not optional.

**Semper Tools For Regular Folks. Semper Receipts. Semper Cool Shit. Semper Homies.** 🐺

---

## License, AI Risk, and Financial Disclaimer

NewsHound is released under the **MIT License**. Read [`LICENSE`](LICENSE) before use.

**AI Thesis is experimental and can be wrong.** AI output may be incomplete, stale, inaccurate, misleading, or fabricated.

NewsHound is not a broker or investment adviser and does not provide financial, legal, tax, accounting, or compliance advice. Nothing produced by NewsHound is a recommendation or instruction to buy, sell, hold, or otherwise transact in any security, digital asset, or other financial instrument.

Financial markets involve risk, including possible loss of principal.

Users are responsible for:

- Independently verifying evidence and analytical conclusions
- Their own trading and investment decisions
- Protecting API credentials
- Compliance with applicable laws and regulations
- Compliance with third-party provider terms and licensing

See [`DISCLAIMER.md`](DISCLAIMER.md) for the complete AI, financial-market, third-party-data, evidence, and operator-responsibility notice.

**Use AI Thesis and NewsHound at your own risk.**

---

## Current Release — v1.3-hf14

### AI Thesis Report Archive

v1.3-hf14 adds persistent, operator-designated finished intelligence to the AI Thesis workflow.

A useful live analysis can now be promoted into paired PDF and JSON artifacts beneath:

```text
reports/YYYY/MM/
```

The PDF provides the human-readable finished intelligence product.

The JSON artifact provides the structured analytical and provenance receipt.

The **Saved Reports** interface provides retrieval and management of archived intelligence, while **EXPORT PDF** can archive and immediately produce the human-readable report.

v1.3-hf14 also adds ReportLab as the PDF-generation dependency. Existing installations upgrading across this dependency change must synchronize their preserved Python virtual environment with the current `requirements.txt`.

For complete release information, see [`RELEASE-NOTES-1.3-hf14.md`](RELEASE-NOTES-1.3-hf14.md).

---

## WolfPack Doctrine

**AI RECOMMENDS • EVIDENCE SUBSTANTIATES • W6 AUTHORIZES**

**PRICE grades the thesis. Human authority is retained.**

**Semper Preserve The Damn Intelligence. Semper Receipts. Semper Build Cool Shit.** 🐺
