# 🛡️ SicherGleis Pro - Railway Dashboard

**BahnSetu Platform - Intelligent Railway Operations Dashboard**

---

## 📋 Overview

SicherGleis Pro is a comprehensive real-time monitoring and analytics dashboard for railway station operations. Built with Streamlit, this application provides visualizations and insights into:

- **Platform Screen Door (PSD)** status and operations
- **Predictive maintenance** with risk scoring
- **Passenger flow analytics** and heatmaps
- **Network-wide operational metrics**
- **Incident tracking** and alerts

The dashboard is designed for railway operators, maintenance teams, and station managers to monitor multiple stations, identify potential issues before they become critical, and optimize passenger flow.

---

## ✨ Key Features

### 🚪 Real-Time Gate Monitoring
- Live monitoring of gate states (open, closed, closing, jammed, offline)
- Temperature and vibration sensor readings
- Sync score calculation (penalty-based scoring for anomalies)
- Passenger count per gate

### 🔮 Predictive Maintenance
- **Risk Score** (0-100): Composite metric based on temperature, vibration, and door state
- **Maintenance Status**: OPTIMAL, MONITOR, WARNING, CRITICAL
- **7-day risk forecast** for each station
- Automated **incident log** generation for critical/warning gates

### 📊 Analytics & Visualizations
- **Per-Station Analytics**: Door cycle counts, temperature trends by hour
- **Passenger Flow Heatmap**: 7-day x 12-hour flow matrix
- **Network Summary**: Aggregate statistics across all stations
- **Status Distribution Charts**: Breakdown by maintenance status and door state

### 🎯 Leadership Dashboard
- Executive team information
- Technology stack overview

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Interface** | Streamlit, Plotly |
| **Data Processing** | Pandas, NumPy |
| **Visualization** | Plotly Express, Plotly Graph Objects |
| **Styling** | Custom CSS (Dark theme, Space Grotesk font) |

**Sensing & IoT (production deployment):**
- Temperature, vibration, proximity sensors
- PSD Controllers (real-time gate logic)
- 5G / Fiber network
- BahnSetu Core microservices (99.97% uptime SLA)

---

## 📦 Installation

### Prerequisites
- Python 3.8+
- pip package manager

### Setup

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/SicherGleis_Bahnsetu.git
cd SicherGleis_Bahnsetu/railway_dashboard
```

2. **Create virtual environment (recommended)**
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python -m venv venv
source venv/bin/activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Prepare data**
- Ensure `stations.csv` exists in the project root
- The CSV should contain the following columns:
  - `station` (string): Station name
  - `platform` (string): Platform identifier
  - `gate_id` (string): Unique gate identifier
  - `train` (string): Associated train number (optional)
  - `status` (string): Train status (approaching, arrived, departed, clear)
  - `door_state` (string): Gate state (open, closed, closing, jammed, offline)
  - `sensor_temp` (float): Temperature reading in °C
  - `sensor_vib` (float): Vibration reading
  - `people` (int): Number of people nearby
  - `eta` (int): Estimated time of arrival in minutes

5. **Run the application**
```bash
streamlit run streamlit_app.py
```

6. Open your browser to `http://localhost:8501`

---

## 📁 Project Structure

```
railway_dashboard/
├── streamlit_app.py       # Main Streamlit application
├── data_source.py         # Data loading, transformation, and analytics functions
├── stations.csv           # Station/gate data (sample provided)
├── requirements.txt       # Python dependencies
├── venv/                  # Virtual environment (excluded from git)
└── README.md              # This file
```

---

## 🎯 Usage Guide

### Navigation
- **Sidebar**: Select a station from the dropdown to view detailed analytics
- **Tabs**:
  - **Operations**: Real-time gate monitoring, key metrics, incident log, and network summary
  - **Analytics**: Per-station charts (door cycles, temperature trends, passenger heatmap)
  - **About**: Leadership team and technology stack information

### Key Metrics
- **Station Stats**: Total gates, active gates, total passengers, alerts, average sync score, warnings
- **Network Stats**: Total gates, total passengers, critical/warning counts, network sync score, optimal count

---

## 🔒 .gitignore

The project includes a `.gitignore` that typically excludes:
- `venv/` - Python virtual environment
- `__pycache__/` - Python bytecode cache
- `*.pyc` - Compiled Python files
- `.DS_Store` (macOS)
- IDE configuration files
- Environment files

---

## 🤝 Contributing

We welcome contributions to improve SicherGleis Pro! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

Please ensure code follows PEP 8 style guidelines and includes appropriate comments.

---

## 📄 License

[Specify your license here - e.g., MIT, Apache 2.0, or All Rights Reserved]

---

## 👥 Leadership

| Name | Role | Focus Areas |
|------|------|-------------|
| Khushboo Patil | CEO | Business Strategy, Market Expansion |
| Namrata Joshi | COO | Operations Management, Project Coordination |
| Kona Shivam Rao | CTO | Systems Engineering, Automation |
| Sanika Kale | CPO | Product Innovation, UX Design |
| Nikhil Chavan | CFO | Financial Strategy, Partnerships |

---

## 📧 Contact

For questions, support, or partnership inquiries, please reach out through our official channels.

---

**Built with ❤️ using Streamlit, Python, and Plotly**

*SicherGleis: Safe Tracks, Smart Operations*
