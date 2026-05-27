"""Tests for core/tv_renderer.py — covers render_tv, _render_kpi_row, _chart_info_bar."""
from unittest.mock import MagicMock, patch
import pandas as pd
import pytest

from core.tv_renderer import (
    _chart_info_bar, _render_kpi_row,
    DOMAINS, DOMAIN_META, DOMAIN_COLORS,
)


def _make_mock_tv_data():
    """Create a TotalVisionData-like mock with proper sub-attributes."""
    sec = MagicMock()
    sec.threat_level = 25.0
    sec.incidents_cyber = 3
    sec.avg_response_time = 2.5

    sus = MagicMock()
    sus.energy_kwh = 15000.0
    sus.carbon_tco2e = 12.5
    sus.green_energy_pct = 45.0
    sus.efficiency_score = 65.0

    pas = MagicMock()
    pas.satisfaction_score = 78.0
    pas.crowding_index = 55.0
    pas.dwell_time_avg = 45.0

    ast = MagicMock()
    ast.fleet_rul_pct = 72.0
    ast.backlog_total = 15
    ast.gates_total = 48
    ast.sensor_healthy = 44

    clm = MagicMock()
    clm.resilience_score = 65.0
    clm.flood_risk = 30.0
    clm.adaptation_readiness_pct = 58.0

    tv = MagicMock()
    tv.station = "Berlin Hbf"
    tv.security = sec
    tv.sustainability = sus
    tv.passenger = pas
    tv.asset = ast
    tv.climate = clm

    def _scores_dict():
        return {
            "security": 75.0, "sustain": 65.0,
            "passenger": 78.0, "asset": 72.0, "climate": 65.0,
        }
    def _score(domain):
        return _scores_dict().get(domain, 0.0)

    tv.scores_dict = _scores_dict
    tv.score = _score
    return tv


# ── Helper to build patch mocks ──

def _make_st_mock():
    """Build a complete streamlit mock for render_tv tests."""
    st = MagicMock()
    st.selectbox.return_value = "Berlin Hbf"

    def _columns(*args, **kwargs):
        n = args[0] if args else kwargs.get("n", 1)
        if isinstance(n, (list, tuple)):
            n = len(n)
        return [MagicMock() for _ in range(n)]

    st.columns.side_effect = _columns
    st.slider.return_value = 1.0
    st.button.return_value = False
    st.text_input.return_value = "Test Scenario"
    st.markdown = MagicMock()
    st.plotly_chart = MagicMock()
    st.spinner = MagicMock().__enter__
    st.success = MagicMock()
    st.info = MagicMock()
    st.json = MagicMock()
    st.error = MagicMock()
    return st


# ═══════════════════════════════════════════════════════════
# _chart_info_bar tests (no streamlit mocking needed)
# ═══════════════════════════════════════════════════════════

class TestChartInfoBar:
    """Tests for _chart_info_bar function — pure HTML generation."""

    @pytest.fixture
    def tv(self):
        return _make_mock_tv_data()

    def test_all_domains(self, tv):
        for domain in DOMAINS:
            html = _chart_info_bar(domain, tv)
            assert isinstance(html, str) and len(html) > 0
            assert f'class="tv-chart-info-bar {domain}"' in html

    def test_unknown_domain(self, tv):
        html = _chart_info_bar("unknown_domain", tv)
        assert 'class="tv-chart-info-bar unknown"' in html

    def test_security_threat(self, tv):
        assert "Threat" in _chart_info_bar("security", tv)

    def test_sustain_energy(self, tv):
        assert "Energy" in _chart_info_bar("sustain", tv)

    def test_passenger_satisfaction(self, tv):
        assert "Satisfaction" in _chart_info_bar("passenger", tv)

    def test_asset_rul(self, tv):
        assert "RUL" in _chart_info_bar("asset", tv)

    def test_climate_resilience(self, tv):
        assert "Resilience" in _chart_info_bar("climate", tv)

    def test_each_domain_three_chips(self, tv):
        for domain in DOMAINS:
            assert _chart_info_bar(domain, tv).count("tv-chart-info-chip") == 3


# ═══════════════════════════════════════════════════════════
# _render_kpi_row tests
# ═══════════════════════════════════════════════════════════

class TestRenderKpiRow:
    """Tests for _render_kpi_row — needs streamlit mocked on core.tv_renderer.st."""

    def test_with_varied_scores(self):
        st = _make_st_mock()
        with patch("core.tv_renderer.st", st):
            _render_kpi_row({"security": 80, "sustain": 30, "passenger": 55,
                             "asset": 45, "climate": 90})
            assert st.markdown.called

    def test_with_all_zero(self):
        st = _make_st_mock()
        with patch("core.tv_renderer.st", st):
            _render_kpi_row({d: 0 for d in DOMAINS})
            assert st.markdown.called

    def test_with_all_max(self):
        st = _make_st_mock()
        with patch("core.tv_renderer.st", st):
            _render_kpi_row({d: 100 for d in DOMAINS})
            assert st.markdown.called


# ═══════════════════════════════════════════════════════════
# render_tv tests
# ═══════════════════════════════════════════════════════════

class TestRenderTv:
    """Tests for render_tv — mocked streamlit + engine."""

    def test_with_df(self):
        """Render with a proper DataFrame."""
        df = pd.DataFrame({
            "station": ["Berlin Hbf"], "sync_score": [85], "risk_score": [15],
            "people": [1200], "sensor_temp": [32.5], "sensor_vib": [1.2],
            "door_state": ["open"], "gate_id": ["G001"], "platform": ["1"],
            "maintenance_status": ["OPTIMAL"],
        })
        st = _make_st_mock()
        with patch("core.tv_renderer.st", st):
            from core.tv_renderer import render_tv
            render_tv(df)
            assert st.markdown.called

    def test_without_df(self):
        """Render without DataFrame."""
        st = _make_st_mock()
        with patch("core.tv_renderer.st", st):
            from core.tv_renderer import render_tv
            render_tv(df=None)
            assert st.markdown.called

    def test_with_empty_df(self):
        """Render with empty DataFrame."""
        st = _make_st_mock()
        with patch("core.tv_renderer.st", st):
            from core.tv_renderer import render_tv
            render_tv(pd.DataFrame())
            assert st.markdown.called

    def test_engine_handling(self):
        """Test engine.generate_all is called."""
        st = _make_st_mock()
        with patch("core.tv_renderer.st", st):
            with patch("core.tv_renderer.TotalVisionDataEngine") as eng_cls:
                eng = MagicMock()
                tv = _make_mock_tv_data()
                eng.generate_all.return_value = {"Berlin Hbf": tv}
                eng.correlate.return_value = {"matrix": {}, "findings": []}
                eng.project.return_value = {
                    "projected_scores": {}, "baseline_scores": {},
                    "deltas": {}, "timeline": [], "station_projections": {},
                }
                eng_cls.return_value = eng
                eng_cls.aggregate_scores.return_value = {}
                eng.list_scenarios.return_value = []

                from core.tv_renderer import render_tv
                render_tv(df=pd.DataFrame({"station": ["Berlin Hbf"]}))
                assert eng.generate_all.called

    def test_scenario_project_flow(self):
        """Test what-if scenario projection flow uses eng.project with correct params."""
        st = _make_st_mock()
        st.slider.return_value = 1.0
        with patch("core.tv_renderer.st", st):
            with patch("core.tv_renderer.TotalVisionDataEngine") as eng_cls:
                eng = MagicMock()
                tv = _make_mock_tv_data()
                eng.generate_all.return_value = {"Berlin Hbf": tv}
                eng.correlate.return_value = {"matrix": {}, "findings": []}
                expected_project = {
                    "projected_scores": {}, "baseline_scores": {},
                    "deltas": {}, "timeline": [], "station_projections": {},
                }
                eng.project.return_value = expected_project
                eng_cls.return_value = eng
                eng_cls.aggregate_scores.return_value = {}

                from core.tv_renderer import render_tv
                render_tv(df=pd.DataFrame({"station": ["Berlin Hbf"]}))
                # Verify eng.project was called (what-if scenario path)
                eng.project.assert_called()
                # Verify plotly charts rendered
                assert st.plotly_chart.called

    def test_with_correlation_findings(self):
        """Test correlation findings are rendered."""
        st = _make_st_mock()
        with patch("core.tv_renderer.st", st):
            with patch("core.tv_renderer.TotalVisionDataEngine") as eng_cls:
                eng = MagicMock()
                tv = _make_mock_tv_data()
                eng.generate_all.return_value = {"Berlin Hbf": tv}
                eng.correlate.return_value = {
                    "matrix": {"security": {"sustain": 0.5}},
                    "findings": [{
                        "direction": "positive", "strength": "strong",
                        "story": "Correlation found", "r_value": 0.85,
                        "p_value": 0.01,
                    }],
                }
                eng.project.return_value = {
                    "projected_scores": {}, "baseline_scores": {},
                    "deltas": {}, "timeline": [], "station_projections": {},
                }
                eng_cls.return_value = eng
                eng_cls.aggregate_scores.return_value = {}

                from core.tv_renderer import render_tv
                render_tv(df=pd.DataFrame({"station": ["Berlin Hbf"]}))
                assert st.markdown.called
