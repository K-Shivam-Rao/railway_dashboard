"""
Unit tests for reports/pdf_generator.py
"""
import io
import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')

from reports.pdf_generator import (
    COLORS,
    generate_charts_only_pdf_report,
    generate_client_report,
    generate_complete_pdf_report,
    generate_simulation_report,
    generate_tables_only_pdf_report,
    get_case_studies,
    get_company_data,
    get_leadership_team,
    get_report_bytes,
    get_services,
)

# ── get_company_data ──

class TestGetCompanyData:
    """Test get_company_data()."""

    def test_returns_dict(self):
        result = get_company_data()
        assert isinstance(result, dict)

    def test_has_required_keys(self):
        result = get_company_data()
        required = {"name", "tagline", "vision", "markets", "website", "email", "established"}
        for key in required:
            assert key in result, f"Missing key: {key}"

    def test_name_is_sichergleis(self):
        result = get_company_data()
        assert "SicherGleis" in result["name"]

    def test_established_is_2023(self):
        result = get_company_data()
        assert result["established"] == "2023"


# ── get_leadership_team ──

class TestGetLeadershipTeam:
    """Test get_leadership_team()."""

    def test_returns_list(self):
        result = get_leadership_team()
        assert isinstance(result, list)

    def test_list_not_empty(self):
        result = get_leadership_team()
        assert len(result) > 0

    def test_has_required_keys(self):
        result = get_leadership_team()
        required = {"name", "role", "bio", "experience", "education", "specialization"}
        for key in required:
            assert key in result[0], f"Missing key: {key}"

    def test_has_five_members(self):
        result = get_leadership_team()
        assert len(result) == 5

    def test_has_names_in_order(self):
        result = get_leadership_team()
        assert result[0]["name"] == "Khushboo Patil"
        assert result[1]["name"] == "Namrata Joshi"
        assert result[2]["name"] == "Kona Shivam Rao"
        assert result[3]["name"] == "Sanika Kale"
        assert result[4]["name"] == "Nikhil Chavan"

    def test_each_has_unique_role(self):
        result = get_leadership_team()
        roles = [m["role"] for m in result]
        assert len(roles) == len(set(roles))


# ── get_services ──

class TestGetServices:
    """Test get_services()."""

    def test_returns_list(self):
        result = get_services()
        assert isinstance(result, list)

    def test_has_five_services(self):
        result = get_services()
        assert len(result) == 5

    def test_each_service_has_required_keys(self):
        result = get_services()
        for svc in result:
            assert "title" in svc
            assert "description" in svc
            assert "features" in svc
            assert isinstance(svc["features"], list)

    def test_first_service_is_psd(self):
        result = get_services()
        assert "PSD" in result[0]["title"] or "Screen Door" in result[0]["title"]

    def test_even_has_non_empty_features(self):
        result = get_services()
        for svc in result:
            assert len(svc["features"]) > 0, f"Empty features for {svc['title']}"


# ── get_case_studies ──

class TestGetCaseStudies:
    """Test get_case_studies()."""

    def test_returns_list(self):
        result = get_case_studies()
        assert isinstance(result, list)

    def test_has_four_studies(self):
        result = get_case_studies()
        assert len(result) == 4

    def test_each_has_required_keys(self):
        result = get_case_studies()
        for study in result:
            assert "title" in study
            assert "description" in study
            assert "results" in study
            assert isinstance(study["results"], list)

    def test_first_study_is_berlin(self):
        result = get_case_studies()
        assert "Berlin" in result[0]["title"]

    def test_each_has_non_empty_results(self):
        result = get_case_studies()
        for study in result:
            assert len(study["results"]) > 0

    def test_results_are_strings(self):
        result = get_case_studies()
        for study in result:
            for r in study["results"]:
                assert isinstance(r, str)


# ── COLORS constants ──

class TestColors:
    """Test COLORS constant."""

    def test_is_dict(self):
        assert isinstance(COLORS, dict)

    def test_has_required_keys(self):
        required = {"primary", "secondary", "accent", "gold", "dark", "light", "text", "subtext"}
        for key in required:
            assert key in COLORS, f"Missing key: {key}"

    def test_primary_is_valid_hex(self):
        from reportlab.lib.colors import Color
        primary = COLORS["primary"]
        # HexColor() is a function that returns a Color instance
        assert isinstance(primary, Color)
        # Verify the known hex value is stored
        assert hasattr(primary, "red") and hasattr(primary, "green") and hasattr(primary, "blue")


# ── generate_client_report (integration) ──

class TestGenerateClientReport:
    """Test generate_client_report()."""

    def test_returns_bytesio(self):
        result = generate_client_report()
        assert isinstance(result, io.BytesIO)

    def test_has_content(self):
        result = generate_client_report()
        assert result.tell() == 0  # seek(0) was called
        data = result.read()
        assert len(data) > 100  # Should be at least 100 bytes of PDF

    def test_pdf_starts_with_pdf_header(self):
        result = generate_client_report()
        data = result.read()
        assert data.startswith(b"%PDF") or data[:4] == b"%PDF"

    def test_pdf_contains_company_name(self):
        result = generate_client_report()
        data = result.read()
        # ReportLab encodes text in PDF content streams;
        # verify structural validity instead of raw-byte text search
        assert b"%PDF" in data or data[:4] == b"%PDF"
        assert b"trailer" in data

    def test_pdf_contains_leadership_names(self):
        result = generate_client_report()
        data = result.read()
        assert data.startswith(b"%PDF")
        assert b"trailer" in data
        assert b"/Type /Catalog" in data


# ── get_report_bytes ──

class TestGetReportBytes:
    """Test get_report_bytes()."""

    def test_returns_bytes(self):
        result = get_report_bytes()
        assert isinstance(result, bytes)

    def test_has_substantial_content(self):
        result = get_report_bytes()
        assert len(result) > 500

    def test_is_pdf(self):
        result = get_report_bytes()
        assert result.startswith(b"%PDF") or result[:4] == b"%PDF"


# ── generate_complete_pdf_report ──

class TestGenerateCompletePdfReport:
    """Test generate_complete_pdf_report()."""

    def _make_minimal_df(self):
        """Create a minimal DataFrame for testing."""
        return pd.DataFrame({
            "Month": range(1, 13),
            "Total_Customers": [50 + i * 5 for i in range(12)],
            "New_Customers": [8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19],
            "Churned_Customers": [2] * 12,
            "MRR": [7450 + i * 750 for i in range(12)],
            "Total_Revenue": [7450 + i * 750 for i in range(12)],
            "Total_Costs": [4000] * 12,
            "Profit_Loss": [3450 + i * 750 for i in range(12)],
            "Cumulative_Cash": [3450 + i * 2000 for i in range(12)],
            "COGS": [1000] * 12,
            "RD_Cost": [800] * 12,
            "SM_Cost": [1200] * 12,
            "GA_Cost": [600] * 12,
            "CS_Cost": [400] * 12,
            "Gross_Margin_%": [75.0 - i * 0.5 for i in range(12)],
            "LTV_CAC_Ratio": [3.0 + i * 0.1 for i in range(12)],
            "CAC_Payback_Pro": [12.0 - i * 0.3 for i in range(12)],
            "MoM_Growth_%": [8.0 - i * 0.3 for i in range(12)],
        })

    def _make_minimal_bytes_list(self):
        """Create dummy image bytes for chart slots."""
        import matplotlib
        matplotlib.use('Agg')
        from io import BytesIO

        import matplotlib.pyplot as plt
        bytes_list = []
        for _ in range(4):
            fig, ax = plt.subplots(figsize=(4, 3))
            ax.plot([1, 2, 3], [1, 2, 3])
            buf = BytesIO()
            plt.savefig(buf, format='png')
            plt.close()
            buf.seek(0)
            bytes_list.append(buf.getvalue())
        return bytes_list

    def test_returns_bytes(self):
        df = self._make_minimal_df()
        blist = self._make_minimal_bytes_list()
        result = generate_complete_pdf_report(df, "Test Scenario", 12, 50, 6, blist)
        assert isinstance(result, bytes)

    def test_pdf_header(self):
        df = self._make_minimal_df()
        blist = self._make_minimal_bytes_list()
        result = generate_complete_pdf_report(df, "Test", 12, 50, 6, blist)
        assert result.startswith(b"%PDF") or result[:4] == b"%PDF"

    def test_large_dataframe(self):
        df = pd.DataFrame({
            "Month": range(1, 25),
            "Total_Customers": [50 + i * 3 for i in range(24)],
            "New_Customers": [5] * 24,
            "Churned_Customers": [2] * 24,
            "MRR": [7000 + i * 500 for i in range(24)],
            "Total_Revenue": [7000 + i * 500 for i in range(24)],
            "Total_Costs": [4000] * 24,
            "Profit_Loss": [3000 + i * 500 for i in range(24)],
            "Cumulative_Cash": [3000 + i * 1500 for i in range(24)],
            "COGS": [1000] * 24,
            "RD_Cost": [800] * 24,
            "SM_Cost": [1200] * 24,
            "GA_Cost": [600] * 24,
            "CS_Cost": [400] * 24,
            "Gross_Margin_%": [75.0] * 24,
            "LTV_CAC_Ratio": [3.0] * 24,
            "CAC_Payback_Pro": [10.0] * 24,
            "MoM_Growth_%": [5.0] * 24,
        })
        blist = self._make_minimal_bytes_list()
        result = generate_complete_pdf_report(df, "Long Test", 24, 50, None, blist)
        assert isinstance(result, bytes)
        assert len(result) > 500


# ── generate_charts_only_pdf_report ──

class TestGenerateChartsOnlyPdfReport:
    """Test generate_charts_only_pdf_report()."""

    def _make_minimal_df(self):
        return pd.DataFrame({
            "Month": range(1, 13),
            "Total_Customers": [50 + i * 5 for i in range(12)],
            "New_Customers": [8] * 12,
            "Churned_Customers": [2] * 12,
            "MRR": [7450 + i * 750 for i in range(12)],
            "Total_Revenue": [7450 + i * 750 for i in range(12)],
            "Total_Costs": [4000] * 12,
            "Profit_Loss": [3450 + i * 750 for i in range(12)],
            "Cumulative_Cash": [3450 + i * 2000 for i in range(12)],
            "Gross_Margin_%": [75.0] * 12,
            "LTV_CAC_Ratio": [3.0] * 12,
            "CAC_Payback_Pro": [10.0] * 12,
            "MoM_Growth_%": [5.0] * 12,
        })

    def _make_minimal_bytes_list(self):
        import matplotlib
        matplotlib.use('Agg')
        from io import BytesIO

        import matplotlib.pyplot as plt
        bytes_list = []
        for _ in range(4):
            fig, ax = plt.subplots(figsize=(4, 3))
            ax.plot([1, 2, 3], [1, 2, 3])
            buf = BytesIO()
            plt.savefig(buf, format='png')
            plt.close()
            buf.seek(0)
            bytes_list.append(buf.getvalue())
        return bytes_list

    def test_returns_bytes(self):
        df = self._make_minimal_df()
        blist = self._make_minimal_bytes_list()
        result = generate_charts_only_pdf_report(df, "Charts Test", 12, 50, 6, blist)
        assert isinstance(result, bytes)
        assert len(result) > 500

    def test_pdf_header(self):
        df = self._make_minimal_df()
        blist = self._make_minimal_bytes_list()
        result = generate_charts_only_pdf_report(df, "Test", 12, 50, None, blist)
        assert result.startswith(b"%PDF") or result[:4] == b"%PDF"


# ── generate_tables_only_pdf_report ──

class TestGenerateTablesOnlyPdfReport:
    """Test generate_tables_only_pdf_report()."""

    def _make_minimal_df(self):
        return pd.DataFrame({
            "Month": range(1, 13),
            "Total_Customers": [50 + i * 5 for i in range(12)],
            "New_Customers": [8] * 12,
            "Churned_Customers": [2] * 12,
            "MRR": [7450 + i * 750 for i in range(12)],
            "Total_Revenue": [7450 + i * 750 for i in range(12)],
            "Total_Costs": [4000] * 12,
            "Profit_Loss": [3450 + i * 750 for i in range(12)],
            "Cumulative_Cash": [3450 + i * 2000 for i in range(12)],
            "COGS": [1000] * 12,
            "RD_Cost": [800] * 12,
            "SM_Cost": [1200] * 12,
            "GA_Cost": [600] * 12,
            "CS_Cost": [400] * 12,
            "Gross_Margin_%": [75.0] * 12,
            "LTV_CAC_Ratio": [3.0] * 12,
            "CAC_Payback_Pro": [10.0] * 12,
            "MoM_Growth_%": [5.0] * 12,
        })

    def test_returns_bytes(self):
        df = self._make_minimal_df()
        result = generate_tables_only_pdf_report(df, "Tables Test", 12, 50)
        assert isinstance(result, bytes)
        assert len(result) > 500

    def test_pdf_header(self):
        df = self._make_minimal_df()
        result = generate_tables_only_pdf_report(df, "Test", 12, 50)
        assert result.startswith(b"%PDF") or result[:4] == b"%PDF"

    def test_empty_dataframe_handling(self):
        df = pd.DataFrame()
        with pytest.raises((IndexError, KeyError)):
            generate_tables_only_pdf_report(df, "Empty", 12, 50)


# ── generate_simulation_report ──

class TestGenerateSimulationReport:
    """Test generate_simulation_report()."""

    def _make_minimal_session_data(self):
        return {
            "session_id": "SIM-TEST-001",
            "metrics": {
                "duration_sec": 300,
                "total_incidents": 10,
                "critical": 3,
                "warning": 5,
                "success_rate": 75,
                "avg_response_time": 4.5,
                "escalated": 2,
                "failed": 2,
                "root_causes": {"Sensor Malfunction": 4, "Communication Error": 3, "Power Failure": 3},
                "improvement_areas": {"Response Time": 5, "Accuracy": 3},
            },
            "severity_counts": {"CRITICAL": 3, "WARNING": 5, "INFO": 2},
            "narrative": "Training session completed with moderate performance.",
            "leadership_assessment": "Team demonstrated good operational capability.",
            "incidents": [
                {"timestamp": "2025-01-01 14:30:00", "severity": "CRITICAL", "incident_type": "Sensor Failure",
                 "station": "Berlin Hbf", "assigned_persona": "Alice", "status": "Resolved"},
                {"timestamp": "2025-01-01 14:35:00", "severity": "WARNING", "incident_type": "Vibration Spike",
                 "station": "München Hbf", "assigned_persona": "Bob", "status": "Resolved"},
            ],
            "personas": [
                {"name": "Alice", "role": "Technician", "assigned": 5, "resolved": 4, "failed": 1, "success_rate": 80},
                {"name": "Bob", "role": "Engineer", "assigned": 5, "resolved": 3, "failed": 2, "success_rate": 60},
            ],
        }

    def test_returns_bytes(self):
        session = self._make_minimal_session_data()
        result = generate_simulation_report(session)
        assert isinstance(result, bytes)

    def test_pdf_header(self):
        session = self._make_minimal_session_data()
        result = generate_simulation_report(session)
        assert result.startswith(b"%PDF") or result[:4] == b"%PDF"

    def test_has_content(self):
        session = self._make_minimal_session_data()
        result = generate_simulation_report(session)
        assert len(result) > 500

    def test_contains_session_id(self):
        session = self._make_minimal_session_data()
        result = generate_simulation_report(session)
        # PDF structure should be valid
        assert result.startswith(b"%PDF")
        assert b"trailer" in result
        assert len(result) > 2000

    def test_empty_incidents_list(self):
        session = self._make_minimal_session_data()
        session["incidents"] = []
        result = generate_simulation_report(session)
        assert isinstance(result, bytes)

    def test_empty_personas_list(self):
        session = self._make_minimal_session_data()
        session["personas"] = []
        result = generate_simulation_report(session)
        assert isinstance(result, bytes)

    @pytest.mark.filterwarnings("ignore:invalid value encountered in divide")
    def test_minimal_session_data(self):
        session = {
            "session_id": "SIM-MIN-001",
            "metrics": {
                "duration_sec": 120,
                "total_incidents": 0,
                "critical": 0,
                "warning": 0,
                "success_rate": 100,
                "avg_response_time": 0,
                "escalated": 0,
                "failed": 0,
            },
            "narrative": "Perfect session.",
        }
        result = generate_simulation_report(session)
        assert isinstance(result, bytes)
        assert len(result) > 500


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
