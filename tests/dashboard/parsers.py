import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

import pandas as pd


def run_pytest_json() -> dict:
    """Run pytest with JSON output and return results."""
    project_root = Path(__file__).parent.parent.parent
    result_file = project_root / "tests" / "dashboard" / "pytest_results.json"

    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "--tb=no",
        "-v",
        f"--json-report={result_file}",
        "--json-report-indent=2"
    ]

    try:
        subprocess.run(cmd, cwd=project_root, capture_output=True, timeout=120)
    except (subprocess.SubprocessError, subprocess.TimeoutExpired):
        pass

    if result_file.exists():
        with open(result_file, "r") as f:
            return json.load(f)
    return {}


def parse_coverage_data() -> dict:
    """Parse coverage.json file and return coverage statistics."""
    project_root = Path(__file__).parent.parent.parent
    coverage_file = project_root / "coverage.json"

    if not coverage_file.exists():
        return {"error": "No coverage.json found. Run: python -m pytest --cov --cov-report=json"}

    try:
        import json
        with open(coverage_file) as f:
            data = json.load(f)

        totals = data.get("totals", {})
        total_covered = totals.get("covered_lines", 0)
        total_statements = totals.get("num_statements", 0)

        return {
            "covered": total_covered,
            "total": total_statements,
            "percent": round((total_covered / total_statements) * 100, 2) if total_statements > 0 else 0
        }
    except Exception as e:
        return {"error": str(e)}


def get_test_files_summary() -> pd.DataFrame:
    """Get summary of all test files."""
    project_root = Path(__file__).parent.parent.parent
    tests_dir = project_root / "tests"

    data = []
    for test_file in tests_dir.rglob("test_*.py"):
        rel_path = test_file.relative_to(project_root)
        stat = test_file.stat()
        data.append({
            "file": str(rel_path),
            "size_kb": round(stat.st_size / 1024, 2),
            "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
        })

    return pd.DataFrame(data) if data else pd.DataFrame(columns=["file", "size_kb", "modified"])


def get_coverage_report() -> dict:
    """Generate coverage report data from coverage.json."""
    project_root = Path(__file__).parent.parent.parent
    coverage_file = project_root / "coverage.json"

    if not coverage_file.exists():
        return {"error": "No coverage.json found"}

    try:
        import json
        with open(coverage_file) as f:
            data = json.load(f)

        report = {}
        for module in ["core", "data", "utils", "reports"]:
            covered = 0
            total = 0
            for file_path, file_data in data.get("files", {}).items():
                if f"/{module}/" in file_path or file_path.endswith(f"{module}.py"):
                    summary = file_data.get("summary", {})
                    covered += summary.get("covered_lines", 0)
                    total += summary.get("num_statements", 0)

            report[module] = {
                "executed": covered,
                "missing": total - covered,
                "total": total
            }

        return report
    except Exception as e:
        return {"error": str(e)}
