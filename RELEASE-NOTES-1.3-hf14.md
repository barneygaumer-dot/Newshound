# WolfPack NewsHound v1.3-hf14

## AI Thesis Report Archive

NewsHound v1.3-hf14 adds persistent, operator-designated finished intelligence products to the AI Thesis workflow.

An AI Thesis can now be promoted from transient analytical output into paired PDF and JSON artifacts for later review, evidence preservation, and after-action analysis.

## New in hf14

AI Thesis now supports:

- **SAVE REPORT**
- **EXPORT PDF**
- Persistent **Saved Reports**
- Human-readable PDF intelligence products
- Structured JSON evidence/provenance receipts
- Retrieval of archived PDF and JSON artifacts
- Operator-controlled deletion of archived reports

Reports are organized beneath:

```text
reports/YYYY/MM/
```

Working analytical evidence and finished intelligence remain intentionally separate:

```text
data/theses/     working / cached AI Thesis evidence
reports/         operator-designated finished intelligence
```

Generated reports are runtime artifacts and are excluded from source control.

## Evidence and Provenance

Archived reports preserve available analytical context and provenance, including information such as:

- Original story/evidence identity
- Ticker or entity context
- Publisher/source information
- Publication and receipt timestamps
- Analysis timestamp
- Model information
- Source-access/retrieval mode
- Evidence and source URLs
- Working thesis
- Counter-thesis
- Invalidation criteria

The PDF is intended as the human-readable finished intelligence product.

The JSON artifact provides the structured analytical and provenance receipt.

This creates a durable record that can later support after-action review against subsequent PRICE behavior.

## New Dependency

v1.3-hf14 adds **ReportLab** for PDF generation.

Existing installations upgrading from an earlier release should synchronize the installed Python virtual environment with the current requirements:

```bash
cd /opt/wolfpack/newshound
./.venv/bin/pip install -r requirements.txt
```

The dependency set can be verified with:

```bash
./.venv/bin/python -c \
  "import flask, requests, websocket, langdetect, reportlab; print('Dependencies OK')"
```

Then restart and verify NewsHound:

```bash
sudo systemctl restart newshound
sudo systemctl status newshound --no-pager
```

## AI Thesis Capability Retained

hf14 retains the operator-designated AI Thesis workflow, including:

- Novelty analysis
- Expectation-delta analysis
- Economic transmission reasoning
- Materiality and horizon
- Evidence-quality assessment
- Affected-entity reasoning
- Counter-thesis
- Invalidation criteria
- Expected PRICE behavior
- Source-aware evidence retrieval
- Provenance/evidence receipts
- Deliberate reanalysis with fresh evidence

NewsHound remains an intelligence-analysis system.

It does not execute trades.

**PRICE grades the thesis. Human authority is retained.**

## Collector Behavior

Existing provider-specific collection behavior remains intact.

Benzinga reconnect handling uses exponential backoff with jitter and explicit throttling status rather than aggressive reconnect loops.

Finnhub, Alpha Vantage, and SEC remain independent collection paths.

## Upgrade Consideration

The hf14 upgrade path preserves the installed Python virtual environment.

When upgrading across a release that changes `requirements.txt`, operators should synchronize the virtual environment manually before restarting or validating the upgraded application.

Automated dependency preflight and environment synchronization are intentionally deferred to separately tested maintenance work rather than being introduced as an untested change to the known-good hf14 release.

## Documentation

hf14 public documentation includes:

- `README.md` — project overview and architecture
- `HOWTO.md` — installation and operator guide
- `DISCLAIMER.md` — AI, market-risk, third-party-data, and operator-responsibility notice
- `LICENSE` — MIT License
- `RELEASE-NOTES-1.3-hf14.md` — release-specific changes and upgrade considerations

---

**AI RECOMMENDS • EVIDENCE SUBSTANTIATES • W6 AUTHORIZES**

**Semper Preserve The Damn Intelligence. Semper Receipts.**
