<p align="center">
  <img src="https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" alt="Streamlit">
  <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Tests-232%20passing-22c55e?style=for-the-badge" alt="Tests">
  <img src="https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge" alt="License">
</p>

<h1 align="center">SicherGleis Railway Dashboard</h1>
<p align="center"><strong>Platform Screen Door (PSD) Monitoring · Predictive Maintenance · SaaS Analytics</strong></p>

<p align="center">Real-time railway platform monitoring across <strong>25 stations</strong> with anomaly detection,
predictive maintenance, customer intelligence, and SaaS financial modeling —
built for <strong>hyper-growth startup scale</strong>.</p>

<br>

---

## Migration: Flat → Monorepo

This project was restructured from a flat root layout into a clean monorepo with dedicated `streamlit/` and `nextjs/` applications.

### Before (Flat)

```
railway_dashboard/
├── core/               # Business logic at root
├── data/               # Data layer at root
├── utils/              # Utilities at root
├── reports/            # Reports at root
├── tests/              # Tests at root
├── main.py             # Single 11K-line entry point
├── pyproject.toml      # Root-level config
├── .streamlit/         # Root-level Streamlit config
├── stations.csv        # Data at root
├── stations.parquet    # Data at root
├── report.md           # Documentation at root
└── requirements.txt    # Root deps
```

### After (Monorepo)

```
railway_dashboard/
├── streamlit/           # Streamlit app (migrated under one roof)
├── nextjs/              # NEW: Next.js 15 + FastAPI app
├── .github/workflows/   # CI pipeline
├── requirements.txt     # Root → forwards to streamlit/
├── packages.txt         # System deps
├── .gitignore
├── LICENSE
└── README.md
```

### What Changed

| Change | Detail |
|--------|--------|
| **Restructured** | `core/`, `data/`, `utils/`, `reports/`, `tests/` moved into `streamlit/` |
| **Removed** | Root `main.py` (11K lines), `stations.csv`, `stations.parquet`, `report.md` |
| **Added** | `nextjs/` — full Next.js 15 dashboard + FastAPI backend |
| **Added** | `.github/workflows/ci.yml` — 3-job CI pipeline |
| **Added** | `streamlit/assets/css/` — 18-file design token system |
| **Expanded** | Tests: ~40 files → 85+ files |
| **Modernized** | README with team section, commands table, inline SVG avatars |

### PR: The Merge

```
Commit  : 29e5dd0
Branch  : New-Features
Files   : 206 changed (53,010 insertions / 13,494 deletions)
```

<br>

---

## Quick Start

```bash
# ── Clone ──────────────────────────────────────────────
git clone https://github.com/sichergleis/railway-dashboard.git
cd railway_dashboard

# ── Environment ─────────────────────────────────────────
python -m venv venv
source venv/bin/activate            # Linux / macOS
# venv\Scripts\activate             # Windows

# ── Install ─────────────────────────────────────────────
pip install --upgrade pip
pip install -r requirements.txt

# ── Run ─────────────────────────────────────────────────
streamlit run streamlit/app.py
```

> **Deploy to Streamlit Cloud:** Set main file to `streamlit/app.py`, requirements to `requirements.txt`, Python 3.11.

<br>

---

## All Commands

| Category | Command |
|----------|---------|
| **Run** | `streamlit run streamlit/app.py` |
| **Tests** | `pytest streamlit/tests/ -v` |
| **Coverage** | `pytest streamlit/tests/ -v --cov streamlit/core --cov-report=term-missing --cov-report=xml:coverage.xml` |
| **Lint** | `ruff check streamlit/` |
| **Format** | `ruff format streamlit/` |
| **Type check** | `mypy streamlit/ --ignore-missing-imports` |
| **Security** | `bandit -r streamlit/ -x streamlit/tests` |
| **Deps audit** | `pip audit` |
| **Clean caches** | `find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null` |
| **Build docs** | `cd streamlit && mkdocs build` (requires `mkdocs`) |

<br>

---

## Project Structure

```
railway_dashboard/
│
├── streamlit/                        # Streamlit application (deployed)
│   ├── app.py                        # Entry point — 11K+ lines
│   ├── core/                         # Business logic & analytics engine
│   │   ├── logic.py                  #   Core analytics, simulation engine
│   │   ├── narrative_html.py         #   Ticker carousel, banners, org tree
│   │   ├── budget_tracker.py         #   ROI calculator, CAPEX forecasts
│   │   ├── visualization_engine.py   #   Chart builders
│   │   ├── anomaly_ranking.py        #   Incident severity ranking
│   │   ├── totalvision.py            #   Wall display engine
│   │   └── tv_renderer.py            #   Wall display renderer
│   ├── data/                         # Data layer & sample datasets
│   │   ├── sample_data.py            #   25 stations, 25 customers
│   │   ├── budget_data.py            #   15 stations, EUR 5M-28M CAPEX
│   │   ├── stations.csv              #   Station metadata
│   │   ├── stations.parquet           #   Station metadata (Parquet)
│   │   └── loader.py                 #   Data loading & transforms
│   ├── utils/                        # Utilities
│   │   ├── helpers.py                #   Formatting utilities
│   │   ├── exceptions.py             #   Custom exception classes
│   │   ├── logging_config.py         #   Structured logging
│   │   └── simulation_db.py          #   Local SQLite simulation DB
│   ├── reports/                      # PDF report generation
│   │   └── pdf_generator.py          #   ReportLab PDF builder
│   ├── tests/                        # Test suite — 232+ tests
│   │   ├── test_narrative_html.py    #   Ticker/banner tests
│   │   ├── test_narrative_html_gaps.py
│   │   ├── test_logic.py
│   │   ├── test_data.py
│   │   ├── test_anomaly_ranking.py
│   │   ├── test_loader.py
│   │   └── test_pdf_generator.py
│   ├── assets/css/                   # Design system (18 CSS files)
│   │   ├── design-tokens.css         #   Variables, spacing, shadows
│   │   ├── ticker.css                #   KPI carousel ticker
│   │   ├── green-state.css           #   All-clear celebration banner
│   │   ├── animations.css            #   Shared keyframes
│   │   ├── base.css                  #   Reset & typography
│   │   ├── layout.css                #   Narrative bar, panels
│   │   └── responsive.css            #   Breakpoints (1400/1200/1024/768/480)
│   ├── .streamlit/config.toml        # Streamlit Cloud dark theme config
│   ├── requirements.txt              # Python dependencies
│   └── pyproject.toml                # Project metadata, pytest, ruff config
│
├── requirements.txt                  # Root deps → forwards to streamlit/
├── packages.txt                      # System deps for Streamlit Cloud build
├── .gitignore
├── LICENSE                           # MIT
└── README.md
```

<br>

---

## Architecture

| Layer | Stack | Details |
|-------|-------|---------|
| **Frontend** | Streamlit, Plotly, Altair, PyDeck | Interactive charts, maps, carousels |
| **Backend** | Python 3.10+, Pandas, NumPy, Polars | DataFrame engine, simulation |
| **Analytics** | scikit-learn, statsmodels | Isolation forest, z-score, IQR, moving average, decomposition |
| **Reporting** | ReportLab | PDF export with charts & tables |
| **Styling** | CSS custom properties, glassmorphism, GPU animations | 18 CSS files, design token system |
| **Testing** | pytest, pytest-cov, pytest-json-report | 232+ tests, 90%+ coverage |
| **Deploy** | Streamlit Community Cloud | Auto-deploy from GitHub |

<br>

---

## Features & Data

### Operations Dashboard
- **25 stations** monitored in real-time across DACH region
- **Anomaly detection** — 4 methods: z-score, IQR, moving average, isolation forest
- **Severity classification** — critical / warning / info with color-coded indicators
- **KPI carousel ticker** — CSS-powered item-by-item carousel, 4.5s hold per slide
- **Live badge** — emerald pulsing dot with ripple ring animation
- **Wall display mode** — full-screen auto-rotating station overview

### SaaS Financial Model
- **24-month simulation** — 5,000 → 93,921 customers
- **MRR**: EUR 587K → EUR 9.77M (month 24)
- **ARR**: EUR 117M at scale
- **LTV:CAC ratio**: 37:1 at maturity
- **3 scenarios**: optimistic, baseline, conservative
- **Department planning**: 134 FTE by month 24

### Customer Intelligence
- **25 customer operators** across Germany, Austria, Switzerland
- **RFM analysis** — recency, frequency, monetary segmentation
- **Contract health scoring** — multi-factor risk assessment
- **Renewal forecasting** — at-risk account identification
- **Tier system**: Standard, Premium, Gold, Platinum

### Budget & ROI
- **15 stations** with CAPEX ranging EUR 5M – EUR 28M
- **ROI / NPV calculations** with configurable discount rates
- **Scenario projections** — best case / expected / worst case
- **Optimization recommendations** — cost-saving insights

<br>

---

## Test Suite

```
Status    : 232+ tests · all passing
Coverage  : Core 90%+ · Data 95%+ · Utils 95%+ · Reports 88%+
Speed     : Full suite in ~20 seconds
Framework : pytest · pytest-cov · pytest-json-report · ruff
Config    : fail_under = 80% (hard threshold in CI)
```

<br>

---

## Dependencies

| Package | Min Version | Purpose |
|---------|-------------|---------|
| streamlit | 1.55.0 | Dashboard framework |
| pandas | 2.2.6 | Data manipulation |
| polars | 1.21.0 | High-performance DataFrames |
| numpy | 2.2.0 | Numerical computing |
| scikit-learn | 1.3.0 | Anomaly detection |
| plotly | 6.6.0 | Interactive charts |
| altair | 5.0.0 | Statistical visualization |
| pydeck | 0.8.0 | Deck.gl maps |
| reportlab | 4.0.0 | PDF generation |
| Pillow | 10.0.0 | Image processing |
| tenacity | 8.0.0 | Retry logic |
| python-dotenv | 1.0.0 | Environment config |

<br>

---

## Team

<table align="center">
  <tr>
    <td align="center" width="160">
      <img src="data:image/svg+xml;charset=utf-8,%3Csvg xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22 width%3D%2280%22 height%3D%2280%22 viewBox%3D%220 0 80 80%22%3E%3Cdefs%3E%3ClinearGradient id%3D%22g%22 x1%3D%220%25%22 y1%3D%220%25%22 x2%3D%22100%25%22 y2%3D%22100%25%22%3E%3Cstop offset%3D%220%25%22 stop-color%3D%22%234F46E5%22%2F%3E%3Cstop offset%3D%22100%25%22 stop-color%3D%22%237C3AED%22%2F%3E%3C%2FlinearGradient%3E%3C%2Fdefs%3E%3Ccircle cx%3D%2240%22 cy%3D%2240%22 r%3D%2240%22 fill%3D%22url(%23g)%22%2F%3E%3Ctext x%3D%2240%22 y%3D%2240%22 text-anchor%3D%22middle%22 dominant-baseline%3D%22central%22 fill%3D%22white%22 font-family%3D%22-apple-system%2CBlinkMacSystemFont%2Csans-serif%22 font-size%3D%2228%22 font-weight%3D%22700%22%3EKS%3C%2Ftext%3E%3C%2Fsvg%3E" width="80" height="80" alt="Kona Shivam Rao">
      <br><strong>Kona Shivam Rao</strong>
      <br><sub>CTO — Systems Engineering & Automation</sub>
      <br><img src="https://img.shields.io/badge/37-commits-4F46E5?style=flat">
    </td>
    <td align="center" width="160">
      <img src="data:image/svg+xml;charset=utf-8,%3Csvg xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22 width%3D%2280%22 height%3D%2280%22 viewBox%3D%220 0 80 80%22%3E%3Cdefs%3E%3ClinearGradient id%3D%22g%22 x1%3D%220%25%22 y1%3D%220%25%22 x2%3D%22100%25%22 y2%3D%22100%25%22%3E%3Cstop offset%3D%220%25%22 stop-color%3D%22%230D9488%22%2F%3E%3Cstop offset%3D%22100%25%22 stop-color%3D%22%23059669%22%2F%3E%3C%2FlinearGradient%3E%3C%2Fdefs%3E%3Ccircle cx%3D%2240%22 cy%3D%2240%22 r%3D%2240%22 fill%3D%22url(%23g)%22%2F%3E%3Ctext x%3D%2240%22 y%3D%2240%22 text-anchor%3D%22middle%22 dominant-baseline%3D%22central%22 fill%3D%22white%22 font-family%3D%22-apple-system%2CBlinkMacSystemFont%2Csans-serif%22 font-size%3D%2228%22 font-weight%3D%22700%22%3ENJ%3C%2Ftext%3E%3C%2Fsvg%3E" width="80" height="80" alt="Namrata Joshi">
      <br><strong>Namrata Joshi</strong>
      <br><sub>COO — Operations & Project Coordination</sub>
      <br><img src="https://img.shields.io/badge/3-commits-0D9488?style=flat">
    </td>
    <td align="center" width="160">
      <img src="data:image/svg+xml;charset=utf-8,%3Csvg xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22 width%3D%2280%22 height%3D%2280%22 viewBox%3D%220 0 80 80%22%3E%3Cdefs%3E%3ClinearGradient id%3D%22g%22 x1%3D%220%25%22 y1%3D%220%25%22 x2%3D%22100%25%22 y2%3D%22100%25%22%3E%3Cstop offset%3D%220%25%22 stop-color%3D%22%237C3AED%22%2F%3E%3Cstop offset%3D%22100%25%22 stop-color%3D%22%23DB2777%22%2F%3E%3C%2FlinearGradient%3E%3C%2Fdefs%3E%3Ccircle cx%3D%2240%22 cy%3D%2240%22 r%3D%2240%22 fill%3D%22url(%23g)%22%2F%3E%3Ctext x%3D%2240%22 y%3D%2240%22 text-anchor%3D%22middle%22 dominant-baseline%3D%22central%22 fill%3D%22white%22 font-family%3D%22-apple-system%2CBlinkMacSystemFont%2Csans-serif%22 font-size%3D%2228%22 font-weight%3D%22700%22%3EKP%3C%2Ftext%3E%3C%2Fsvg%3E" width="80" height="80" alt="Khushboo Patil">
      <br><strong>Khushboo Patil</strong>
      <br><sub>CEO — Business Strategy & Market Expansion</sub>
    </td>
    <td align="center" width="160">
      <img src="data:image/svg+xml;charset=utf-8,%3Csvg xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22 width%3D%2280%22 height%3D%2280%22 viewBox%3D%220 0 80 80%22%3E%3Cdefs%3E%3ClinearGradient id%3D%22g%22 x1%3D%220%25%22 y1%3D%220%25%22 x2%3D%22100%25%22 y2%3D%22100%25%22%3E%3Cstop offset%3D%220%25%22 stop-color%3D%22%23EA580C%22%2F%3E%3Cstop offset%3D%22100%25%22 stop-color%3D%22%23DC2626%22%2F%3E%3C%2FlinearGradient%3E%3C%2Fdefs%3E%3Ccircle cx%3D%2240%22 cy%3D%2240%22 r%3D%2240%22 fill%3D%22url(%23g)%22%2F%3E%3Ctext x%3D%2240%22 y%3D%2240%22 text-anchor%3D%22middle%22 dominant-baseline%3D%22central%22 fill%3D%22white%22 font-family%3D%22-apple-system%2CBlinkMacSystemFont%2Csans-serif%22 font-size%3D%2228%22 font-weight%3D%22700%22%3ESK%3C%2Ftext%3E%3C%2Fsvg%3E" width="80" height="80" alt="Sanika Kale">
      <br><strong>Sanika Kale</strong>
      <br><sub>CPO — Product Innovation & UX Design</sub>
    </td>
    <td align="center" width="160">
      <img src="data:image/svg+xml;charset=utf-8,%3Csvg xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22 width%3D%2280%22 height%3D%2280%22 viewBox%3D%220 0 80 80%22%3E%3Cdefs%3E%3ClinearGradient id%3D%22g%22 x1%3D%220%25%22 y1%3D%220%25%22 x2%3D%22100%25%22 y2%3D%22100%25%22%3E%3Cstop offset%3D%220%25%22 stop-color%3D%22%232563EB%22%2F%3E%3Cstop offset%3D%22100%25%22 stop-color%3D%22%230891B2%22%2F%3E%3C%2FlinearGradient%3E%3C%2Fdefs%3E%3Ccircle cx%3D%2240%22 cy%3D%2240%22 r%3D%2240%22 fill%3D%22url(%23g)%22%2F%3E%3Ctext x%3D%2240%22 y%3D%2240%22 text-anchor%3D%22middle%22 dominant-baseline%3D%22central%22 fill%3D%22white%22 font-family%3D%22-apple-system%2CBlinkMacSystemFont%2Csans-serif%22 font-size%3D%2228%22 font-weight%3D%22700%22%3ENC%3C%2Ftext%3E%3C%2Fsvg%3E" width="80" height="80" alt="Nikhil Chavan">
      <br><strong>Nikhil Chavan</strong>
      <br><sub>CFO — Financial Strategy & Partnerships</sub>
    </td>
  </tr>
</table>

<p align="center"><sub>Commit counts from git logs — Kona Shivam Rao (37), Namrata Joshi (3)</sub></p>

<br>

---

## License

MIT — See [LICENSE](LICENSE)

<br>

---

<p align="center">Built by the SicherGleis Team</p>
