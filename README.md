# 🚆 SicherGleis Railway Dashboard

SicherGleis Pro | BahnSetu - Platform Screen Door (PSD) Monitoring & SaaS Analytics Dashboard

## 📋 Overview

Advanced railway platform screen door monitoring system with real-time operations tracking, predictive maintenance, customer analytics, and SaaS financial modeling. Built with Streamlit, Plotly, and modern Python architecture.

## 🏗️ Project Structure

```
railway_dashboard/
├── main.py                    # Streamlit app entry point
├── pyproject.toml             # Project configuration
├── requirements.txt           # Python dependencies
├── .gitignore                 # Git ignore rules
├── README.md                  # This file
├── LICENSE                    # MIT License
├── .streamlit/
│   └── config.toml            # Streamlit settings
├── core/
│   ├── __init__.py
│   └── logic.py               # Business logic & SaaS simulation (90% coverage)
├── data/
│   ├── __init__.py
│   ├── loader.py              # DataLoader class (71% coverage)
│   ├── sample_data.py         # Sample data generators (99% coverage)
│   └── stations.csv           # Railway station data
├── utils/
│   ├── __init__.py
│   ├── helpers.py             # Formatting utilities
│   ├── exceptions.py          # Custom exceptions
│   └── logging_config.py     # Structured logging
├── reports/
│   ├── __init__.py
│   └── pdf_generator.py      # PDF report generation
└── tests/
    ├── __init__.py
    ├── test_core_logic.py
    ├── test_core_logic_extended.py
    ├── test_core_logic_remaining.py
    ├── test_core_logic_missing_coverage.py
    ├── test_data_loader.py
    ├── test_edge_cases.py
    ├── test_helpers.py
    ├── test_integration.py
    ├── test_main_helpers.py
    ├── test_pdf_generator.py
    ├── test_sample_data.py
    └── dashboard/             # TestVision Pro Dashboard
        ├── __init__.py
        ├── main.py            # Streamlit test dashboard
        ├── parsers.py         # Test data parsers
        └── pytest_results.json
```

## 🚀 Features

### Operations Dashboard
- Real-time PSD gate monitoring
- Station-level metrics & analytics
- Network-wide overview
- Predictive maintenance forecasting
- Incident logging & management
- Passenger flow heatmaps

### SaaS Financial Model
- 24-month financial simulation
- Customer growth & churn analysis
- MRR/ARR tracking
- LTV:CAC ratio monitoring
- Department headcount planning
- Multiple scenario comparison

### Customer Intelligence
- RFM (Recency, Frequency, Monetary) analysis
- Customer segmentation
- Contract health scoring
- Renewal forecasting
- At-risk account identification

### TestVision Pro Dashboard
Beautiful standalone test visualization dashboard:
- Pass/fail rates with animated gauges
- Coverage analysis with polar charts & heatmaps
- Test performance analytics (slowest tests, duration distribution)
- File health check and statistics

Run with: `streamlit run tests/dashboard/main.py`

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| **Sensing** | IoT Sensors (temp, vibration, proximity) |
| **Edge** | PSD Controllers with fail-safe override |
| **Network** | 5G / Fiber (sub-10ms sync) |
| **Backend** | Python 3.10+, Polars, Pandas |
| **Analytics** | ML Pipeline, Predictive Maintenance |
| **Visualization** | Streamlit, Plotly, Matplotlib |
| **Reporting** | ReportLab (PDF generation) |
| **Resilience** | tenacity (retry patterns) |

## 📦 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/sichergleis/railway-dashboard.git
   cd railway_dashboard
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # Mac/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Run the main application**
   ```bash
   streamlit run main.py
   ```

## 🧪 Testing

Run the full test suite:
```bash
# Run all tests with coverage
pytest tests/ -v --cov --cov-report=term-missing

# Generate JSON report for TestVision Dashboard
pytest tests/ --json-report --json-report-file=tests/dashboard/pytest_results.json

# Run with specific coverage output
pytest tests/ --cov --cov-report=json -o "addopts="
```

### Test Results (Latest)
- **Total Tests**: 253
- **Passed**: 253 ✅
- **Failed**: 0
- **Coverage**: 54% overall
  - `core/`: 92.3% (1069 lines, 987 covered)
  - `data/`: 89.4% (568 lines, 508 covered)
  - `utils/`: 84.8% (66 lines, 56 covered)
  - `main.py`: 10.4% (1594 lines, 166 covered — dashboard UI)
  - `reports/`: 11.4% (263 lines, 30 covered — tested via `test_pdf_generator.py`)

### Test Coverage by Module
| Module | Coverage | Missed |
|--------|----------|--------|
| core/logic.py | 90% | 61 lines |
| data/loader.py | 71% | 48 lines |
| data/sample_data.py | 99% | 1 line |
| utils/helpers.py | 82% | 5 lines |
| utils/logging_config.py | 81% | 5 lines |
| tests/test_core_logic.py | 98% | 1 line |
| tests/test_core_logic_extended.py | 97% | 4 lines |
| tests/test_data_loader.py | 82% | 10 lines |
| tests/test_sample_data.py | 99% | 1 line |
| main.py | 10% | 1428 lines (dashboard UI) |
| reports/pdf_generator.py | 11% | 233 lines (tested via test_pdf_generator.py) |
| **Overall** | **54%** | **1819 lines** |

### TestVision Pro Dashboard

Launch the beautiful test visualization dashboard:
```bash
streamlit run tests/dashboard/main.py
```

Then open http://localhost:8502 to see:
- 📈 Overview: Pass rate gauge, distribution charts
- ✅ Test Results: Filterable table with color-coded outcomes
- 📊 Coverage Deep Dive: Module breakdown, polar charts, heatmaps
- ⏱️ Performance: Slowest tests, duration distribution
- 📁 Files: File health check and statistics

## 📊 Logging

Structured logging configuration in `utils/logging_config.py`:
- **File logging**: `app.log` (INFO level)
- **Console logging**: WARNING level
- **Format**: `timestamp - module - level - message`

View logs:
```bash
# Windows
type app.log

# Mac/Linux
tail -f app.log
```

## 🏗️ Architecture Highlights

- **Modular Design**: Clean separation between data, core, utils, reports
- **OOP Implementation**: DataLoader, FinancialModel, StationAnalytics, CustomerSegmenter classes
- **Error Handling**: Custom exceptions (DataLoadError, ConfigurationError, etc.)
- **Comprehensive Testing**: 253 tests across 12 test modules
- **Test Visualization**: Beautiful TestVision Pro dashboard for test analytics

## 👥 Leadership Team

| Name | Role |
|------|------|
| Khushboo Patil | CEO - Business Strategy & Market Expansion |
| Namrata Joshi | COO - Operations & Project Coordination |
| Kona Shivam Rao | CTO - Systems Engineering & Automation |
| Sanika Kale | CPO - Product Innovation & UX Design |
| Nikhil Chavan | CFO - Financial Strategy & Partnerships |

## 📞 License

MIT License - See LICENSE file for details.

## 📧 Contact

- **Website**: www.sicher-gleis.com
- **Email**: contact@sicher-gleis.com
- **Location**: DACH Region (Germany, Austria, Switzerland) + India

---

**Built with ❤️ by the SicherGleis Team**