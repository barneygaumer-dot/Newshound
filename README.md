# 🐺 WolfPack Market ISR — NewsHound

<p align="center">
  <img src="newshound/static/rq4-market-isr.png" alt="WolfPack Market ISR RQ-4" width="700">
</p>

<p align="center">
  <strong>MARKET INTELLIGENCE • EARLY WARNING • TARGET DEVELOPMENT</strong>
</p>

<p align="center">
  <em>ISR finds 'em. Reaper stalks 'em. Evidence calls the shot.</em>
</p>

---

## Mission

**NewsHound** is the market-intelligence and early-warning component of **WolfPack Market ISR**.

Its job is not to trade. Its job is to **watch the battlespace**.

NewsHound collects market-relevant intelligence from multiple sources, associates that intelligence with the active ticker watchlist, preserves supporting evidence, and surfaces emerging activity for analysis and downstream target development.

> **Turn the market information firehose into a smaller set of evidence-supported targets worth investigating.**

```text
        MARKET BATTLESPACE
                |
                v
      +-------------------+
      |     NEWSHOUND     |
      | Market ISR / EW   |
      +---------+---------+
                |
        Intelligence
         + Evidence
                |
                v
      +-------------------+
      | TARGET DEVELOPMENT|
      | Rank / Qualify    |
      +---------+---------+
                |
         Target Package
                |
                v
      +-------------------+
      |   MARKET REAPER   |
      | Engagement Logic  |
      +-------------------+
```

**NewsHound discovers. Market Reaper decides.**

Sometimes the correct target list is empty.

---

## Current Release — v1.3-hf5

NewsHound provides source-aware watchlist collection, persistent evidence, provider health/status visibility, and the WolfPack Market ISR operating picture.

### Intelligence Sources

| Source | Collection Model | Mission |
| --- | --- | --- |
| **Benzinga** | Multi-ticker WebSocket | Low-latency watchlist news |
| **Finnhub** | Per-ticker polling | Company-specific news |
| **Alpha Vantage** | Per-ticker `NEWS_SENTIMENT` | News and sentiment intelligence |
| **SEC EDGAR** | Per-ticker / CIK polling | Primary-source regulatory filings |

Each provider is collected according to its actual API semantics rather than forcing every source into a common polling model.

---

## Source-Aware Collection

### Benzinga
Benzinga supports a multi-ticker watchlist stream. NewsHound uses a single multi-symbol **shotgun collection** model for the active watchlist.

### Finnhub
Finnhub company news is queried one symbol at a time. NewsHound walks the watchlist ticker-by-ticker, isolates individual symbol failures, and reports progress across the collection sweep.

### Alpha Vantage
Alpha Vantage `NEWS_SENTIMENT` multi-ticker queries are not treated as a simple OR-style watchlist. NewsHound polls each ticker independently and requires provider ticker attribution before assigning an article to the queried symbol. Provider rate or subscription limitations are surfaced through source status rather than silently discarded.

### SEC EDGAR
SEC collection resolves the appropriate company identifier and polls filings independently for each configured ticker, providing a primary-source intelligence channel independent of commercial news providers.

---

## Evidence Engineering

NewsHound follows the WolfPack principle:

> **If it influenced the decision, preserve the evidence.**

Collected intelligence can be persisted locally for later review, analysis, troubleshooting, and after-action reconstruction.

Runtime evidence:

```text
data/evidence/
```

Current live-board state:

```text
data/live-feed.json
```

NewsHound records source publication timestamps when supplied and its own receipt timestamps, providing a foundation for source-latency analysis.

Runtime evidence and live state are intentionally excluded from the public repository.

---

## Security

API credentials are **not stored in the public source tree**.

Local configuration is maintained in:

```text
config/config.json
```

Secrets are stored server-side and are not returned to the browser after save. The repository `.gitignore` excludes local configuration, runtime data, logs, backups, virtual environments, environment files, and common credential/key files, including:

```text
config/config.json
data/
logs/
backups/
venv/
.env
.env.*
*.key
*.pem
```

Default source configuration contains empty API-key values.

> **Never commit provider API keys, authentication tokens, credentials, or private evidence to the repository.**

---

## Installation

NewsHound currently targets Ubuntu/Linux with Python 3.

```bash
git clone https://github.com/barneygaumer-dot/Newshound.git
cd Newshound
chmod +x install.sh
./install.sh
```

Default application port: **8091**

Local UI:

```text
http://127.0.0.1:8091
```

LAN access uses the NewsHound host's IP address on TCP port **8091**.

---

## Configuration

Provider configuration is performed locally through the NewsHound **SETUP** interface.

Currently supported intelligence providers:

- Benzinga
- Finnhub
- Alpha Vantage
- SEC EDGAR

The configured ticker watchlist defines the portion of the market battlespace NewsHound is tasked to observe.

Provider availability, polling limits, subscription requirements, and rate limits remain subject to each intelligence provider.

---

## ISR Operating Concept

NewsHound follows a simple intelligence cycle:

**Observe → Collect → Correlate → Preserve → Assess → Nominate**

The system is intended to help answer:

- What changed?
- Which ticker is affected?
- How fresh is the intelligence?
- Which sources support the observation?
- Is the information primary-source or secondary reporting?
- Is the event material enough to warrant deeper analysis?
- What evidence supports the resulting target nomination?

News volume alone does not equal intelligence. A ticker producing large quantities of weak information should not automatically outrank a ticker with one highly material, well-supported event.

---

## Design Principles

**Evidence over intuition** — Important observations should remain traceable to supporting evidence.

**Source awareness** — Each intelligence provider is queried according to its actual API behavior.

**Freshness matters** — Old intelligence should not masquerade as a new event.

**Failure isolation** — A failure involving one ticker or provider should not unnecessarily abort the rest of the collection mission.

**Human authority** — NewsHound provides intelligence and decision support. It does not autonomously execute securities trades.

**Capital preservation** — The system is explicitly allowed to determine that nothing currently deserves engagement.

> **No target is better than a bad target.**

---

## Project Structure

```text
Newshound/
├── newshound/
│   ├── app.py
│   ├── classify.py
│   ├── config.py
│   ├── sources.py
│   ├── store.py
│   ├── static/
│   │   ├── app.js
│   │   ├── rq4-market-isr.png
│   │   └── style.css
│   └── templates/
│       └── index.html
├── install.sh
├── requirements.txt
├── run.py
├── VERSION
└── README.md
```

---

## v1.3-hf5 Highlights

- Source-aware market-news collection
- Benzinga multi-ticker watchlist streaming
- Finnhub per-symbol collection sweeps
- Alpha Vantage per-symbol `NEWS_SENTIMENT` collection
- Per-symbol collection failure isolation
- Provider collection-progress visibility
- Alpha Vantage rate/plan status detection
- SEC EDGAR primary-source collection
- Persistent evidence capture and live intelligence board
- WolfPack Market ISR RQ-4 visual refresh

---

## Scope

NewsHound is an intelligence collection and early-warning service. It does not autonomously trade securities. Market analysis and any engagement decision remain separate downstream functions.

---

## Disclaimer

WolfPack Market ISR / NewsHound is research and decision-support software. It does not provide investment advice and does not guarantee the accuracy, completeness, timeliness, or profitability of information obtained from external providers.

Trading and investing involve risk. Any trading or investment decision remains the responsibility of the operator.

---

## WolfPack

Built as part of the **WolfPack evidence-engineering ecosystem**.

**Semper ISR. Semper Evidence. 🐺**
