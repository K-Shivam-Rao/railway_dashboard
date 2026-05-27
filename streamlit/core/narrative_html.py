"""
NARRATIVE INTELLIGENCE HTML BUILDERS
=====================================
Builds the green-state banner, KPI ticker strip, mini-ranking card,
and org-tree navigator HTML fragments used in app.py.

Part of the Midnight Express v5 UI/UX upgrade.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════
# GREEN STATE CELEBRATION BANNER
# ═══════════════════════════════════════════════════

def build_green_state_banner(
    station_count: int = 0,
    streak_days: int = 0,
    uptime_pct: float = 99.7,
    last_incident: str = "N/A",
    mtbi: str = "72h",
) -> str:
    """
    Build HTML for the green-state "all clear" celebration banner.
    Shown when zero anomalies are detected across the network.
    """
    return (
        '<div class="green-state-banner slide-down">'
        '<div class="green-state-inner">'
        '<div class="green-state-icon-wrapper">'
        '<div class="green-state-check scale-in" style="animation-delay:0.1s">'
        '<svg width="36" height="36" viewBox="0 0 24 24" fill="none" '
        'stroke="#22c55e" stroke-width="2.5" stroke-linecap="round" '
        'stroke-linejoin="round">'
        '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>'
        '<polyline points="22 4 12 14.01 9 11.01"/></svg></div></div>'
        '<div class="green-state-content">'
        f'<div class="green-state-title fade-in" style="animation-delay:0.2s">'
        f"All {station_count} Stations Operational</div>"
        f'<div class="green-state-subtitle fade-in" style="animation-delay:0.3s">'
        f"Network-wide systems running at peak performance</div>"
        '<div class="green-state-stats">'
        f'<div class="green-stat fade-in" style="animation-delay:0.35s">'
        f'<span class="green-stat-value">{streak_days}</span>'
        f'<span class="green-stat-label">Days Without<br/>Critical Incident</span></div>'
        '<div class="green-stat-divider"></div>'
        f'<div class="green-stat fade-in" style="animation-delay:0.4s">'
        f'<span class="green-stat-value">{uptime_pct}%</span>'
        f'<span class="green-stat-label">System<br/>Uptime</span></div>'
        '<div class="green-stat-divider"></div>'
        f'<div class="green-stat fade-in" style="animation-delay:0.45s">'
        f'<span class="green-stat-value">{mtbi}</span>'
        f'<span class="green-stat-label">Mean Time<br/>Between Incidents</span></div>'
        '<div class="green-stat-divider"></div>'
        f'<div class="green-stat fade-in" style="animation-delay:0.5s">'
        f'<span class="green-stat-value">{last_incident}</span>'
        f'<span class="green-stat-label">Last<br/>Incident</span></div>'
        "</div></div></div></div>"
    )


def build_kpi_ticker(
    incidents=None,
    kpi_items=None,
):
    # type: (Optional[List[Dict]], Optional[List[Dict]]) -> str
    items_html = ""

    if incidents and isinstance(incidents, list):
        for inc in incidents[:8]:
            sev = str(inc.get("severity", "warning")).lower()
            sev_color = "#ef4444" if sev == "critical" else "#f59e0b"
            ts = inc.get("timestamp", "")
            station = inc.get("station", "") or ""
            desc = inc.get("description", "")
            gate = inc.get("gate", "")
            temp = inc.get("temp", 0)
            vib = inc.get("vib", 0)
            risk = inc.get("risk", 0)

            # Per-sensor tooltips — each pill shows only its own value
            temp_tip = f"Temperature: {temp:.1f}\u00b0C" if temp else ""
            vib_tip = f"Vibration: {vib:.1f} mm/s" if vib else ""
            risk_tip = f"Risk Score: {risk:.0f}/100" if risk else ""
            ts_tip = f"Time: {ts}" if ts else ""

            # Legacy tooltip (used on gate and for fallback)
            legacy_tips = []
            if temp: legacy_tips.append(f"TEMP {temp:.1f}\u00b0C")
            if vib:  legacy_tips.append(f"VIB {vib:.1f} mm/s")
            if risk: legacy_tips.append(f"RISK {risk:.0f}")
            if ts:   legacy_tips.append(f"TIME {ts}")
            legacy_tooltip = " | ".join(legacy_tips)

            # Compact format: "G03 | TEMP 48.2C | VIB 5.5 mm/s | RISK 100"
            if " | " in desc:
                parts = desc.split(" | ")
                gate_str = gate or parts[0]
                sensor_pills = ""
                pill_tips = {
                    "temp-pill": temp_tip,
                    "vib-pill": vib_tip,
                    "risk-pill": risk_tip,
                }
                for p in parts[1:]:
                    p = p.strip()
                    p_upper = p.upper()
                    if "TEMP" in p_upper:
                        cls = "temp-pill"
                        tip = temp_tip
                    elif "VIB" in p_upper:
                        cls = "vib-pill"
                        tip = vib_tip
                    elif "RISK" in p_upper:
                        cls = "risk-pill"
                        tip = risk_tip
                    else:
                        cls = ""
                        tip = ""
                    if tip:
                        sensor_pills += (
                            "<span class=\"ticker-sensor-pill " + cls + "\" "
                            "title=\"" + tip + "\">" + p + "</span>"
                        )
                incident_html = (
                    "<div class=\"ticker-item ticker-incident ticker-" + sev + "\" "
                    "style=\"border-left-color:" + sev_color + ";\">"
                    "<span class=\"ticker-incident-dot\" style=\"background:" + sev_color + ";\"></span>"
                    "<span class=\"ticker-incident-text\">"
                    "<strong class=\"ticker-station\" title=\"" + ts_tip + "\">" + station + "</strong>"
                    "<span class=\"ticker-gate\" title=\"Gate ID: " + gate_str + "\">" + gate_str + "</span>"
                    + sensor_pills
                    + "</span>"
                )
                if ts:
                    incident_html += "<span class=\"ticker-timestamp\">" + ts + "</span>"
                incident_html += "</div>"
                items_html += incident_html
            else:
                # Legacy fallback — truncate to 100 chars
                desc_short = desc[:100] + "..." if len(desc) > 100 else desc
                items_html += (
                    "<div class=\"ticker-item ticker-incident ticker-" + sev + "\" "
                    "style=\"border-left-color:" + sev_color + ";\">"
                    "<span class=\"ticker-incident-dot\" style=\"background:" + sev_color + ";\"></span>"
                    "<span class=\"ticker-incident-text\"><strong>" + station + ":</strong> " + desc_short + "</span>"
                    "<span class=\"ticker-timestamp\">" + ts + "</span>"
                    "</div>"
                )

    if kpi_items:
        for kpi in kpi_items:
            label = kpi.get("label", "")
            value = kpi.get("value", "")
            items_html += (
                "<div class=\"ticker-item ticker-kpi\">"
                "<span class=\"ticker-kpi-label\">" + label + ":</span>"
                "<span class=\"ticker-kpi-value\">" + value + "</span>"
                "</div>"
            )

    if not items_html:
        items_html = (
            "<div class=\"ticker-item ticker-kpi\">"
            "<span class=\"ticker-kpi-label\">System:</span>"
            "<span class=\"ticker-kpi-value\">Monitoring active</span>"
            "</div>"
        )

    # Invisible spacer ensures content starts 80px in (past the LIVE badge)
    # while keeping the offset INSIDE the animated content for a seamless loop.
    spacer = "<span class=\"ticker-spacer\"></span>"
    duped = spacer + items_html + spacer + items_html
    return (
        "<div class=\"kpi-ticker-strip\">"
        "<div class=\"ticker-live-badge\">LIVE</div>"
        "<div class=\"ticker-track\">"
        "<div class=\"ticker-content\">" + duped + "</div>"
        "</div></div>"
    )

# ═══════════════════════════════════════════════════
# MINI-RANKING CARD — sidebar incident summary
# ═══════════════════════════════════════════════════

def build_mini_ranking(ranked_anomalies: List[Dict]) -> str:
    """Build a compact mini-ranking card for the sidebar."""
    if not ranked_anomalies:
        return ""
    items = ""
    for a in ranked_anomalies[:3]:
        sev = str(a.get("severity", "WARNING")).upper()
        sev_cls = "critical" if sev == "CRITICAL" else "warning"
        items += (
            '<div class="mini-rank-item">'
            f'<span class="mini-rank-dot {sev_cls}"></span>'
            f'<span class="mini-rank-station">{a.get("station", "?")}</span>'
            f'<span class="mini-rank-gate">{a.get("gate", "?")}</span>'
            f'<span class="mini-rank-sev {sev_cls}">{sev[:4]}</span>'
            f'<span class="mini-rank-score">{a.get("composite_score", 0):.0f}</span>'
            "</div>"
        )
    return (
        '<div class="mini-rank-card">'
        '<div class="mini-rank-header">'
        '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" '
        'stroke="currentColor" stroke-width="2.5" stroke-linecap="round" '
        'stroke-linejoin="round">'
        '<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>'
        f'<span>Active Incidents</span>'
        f'<span class="mini-rank-count">{len(ranked_anomalies)}</span>'
        "</div>"
        f"{items}"
        "</div>"
    )


# ═══════════════════════════════════════════════════
# ORG TREE NAVIGATOR
# ═══════════════════════════════════════════════════

def build_org_tree(customers_data: List[Dict], search_query: str = "") -> str:
    """
    Build HTML for the Customer → Contract → Station org tree navigator.
    """
    if not customers_data:
        return '<div class="org-tree-empty"><span>No operator data available</span></div>'

    sq = search_query.strip().lower()
    if sq:
        filtered = []
        for cust in customers_data:
            cname = cust.get("name", "").lower()
            cmatch = sq in cname
            kept_contracts = []
            for con in cust.get("contracts", []):
                coname = con.get("name", "").lower()
                comatch = sq in coname
                kept_stations = [s for s in con.get("stations", [])
                                 if sq in s.get("name", "").lower() or sq in s.get("region", "").lower()]
                if cmatch or comatch or kept_stations:
                    kept_contracts.append({**con, "stations": con["stations"] if (cmatch or comatch) else kept_stations})
            kept_direct = [s for s in cust.get("stations", [])
                           if sq in s.get("name", "").lower() or sq in s.get("region", "").lower()]
            if cmatch or kept_contracts or kept_direct:
                filtered.append({**cust, "contracts": kept_contracts, "stations": kept_direct if (not kept_contracts and not cmatch) else cust["stations"] if cmatch else kept_direct})
        customers_data = filtered

    html = '<div class="org-tree-container" id="orgTree">'

    def tier_badge(tier):
        if not tier or tier == "Standard":
            return ''
        cls = "platinum" if tier == "Platinum" else ("gold" if tier == "Gold" else "premium")
        return '<span class="org-tree-tier ' + cls + '">' + tier + '</span>'

    for ci, customer in enumerate(customers_data):
        name = customer.get("name", f"Operator {ci+1}")
        health = customer.get("health_score", 50)
        cust_tier = customer.get("tier", "")
        stations_list = customer.get("stations", [])
        contracts = customer.get("contracts", [])
        station_count = len(stations_list)
        contract_count = len(contracts)

        health_cls = "healthy" if health >= 70 else ("warning" if health >= 40 else "critical")
        ccount_str = f", {contract_count} contracts" if contract_count else ""

        has_children = bool(contracts) or bool(stations_list and not contracts)

        if has_children:
            html += '<details class="org-tree-node org-tree-enter" open>'
            html += '<summary class="org-tree-node-row org-tree-l0">'
            html += '<span class="org-tree-chevron">\u25b6</span>'
            html += '<span class="org-tree-icon">\U0001f3e2</span>'
            html += '<span class="org-tree-label customer">' + name + '</span>'
            html += tier_badge(cust_tier)
            html += '<span class="org-tree-count">' + str(station_count) + ' stations' + ccount_str + '</span>'
            html += '<span class="org-tree-health ' + health_cls + '"></span>'
            html += '</summary>'
            html += '<div class="org-tree-children">'
        else:
            html += '<div class="org-tree-node org-tree-enter">'
            html += '<div class="org-tree-node-row org-tree-l0">'
            html += '<span class="org-tree-chevron leaf">\u25b6</span>'
            html += '<span class="org-tree-icon">\U0001f3e2</span>'
            html += '<span class="org-tree-label customer">' + name + '</span>'
            html += tier_badge(cust_tier)
            html += '<span class="org-tree-count">' + str(station_count) + ' stations' + ccount_str + '</span>'
            html += '<span class="org-tree-health ' + health_cls + '"></span>'
            html += '</div>'

        if contracts:
            for j, contract in enumerate(contracts):
                c_name = contract.get("name", f"Contract {j+1}")
                c_value = contract.get("value", 0)
                c_stations = contract.get("stations", [])
                c_count = len(c_stations)
                c_tier = contract.get("tier", "")

                has_stations = bool(c_stations)

                if has_stations:
                    html += '<details class="org-tree-node org-tree-enter">'
                    html += '<summary class="org-tree-node-row org-tree-l1">'
                    html += '<span class="org-tree-chevron">\u25b6</span>'
                    html += '<span class="org-tree-icon">\U0001f4c4</span>'
                    html += '<span class="org-tree-label contract">' + c_name + '</span>'
                    html += tier_badge(c_tier)
                    html += '<span class="org-tree-count">' + str(c_count) + ' stations</span>'
                    html += '<span class="org-tree-value">\u20ac' + f"{c_value:,.0f}" + '</span>'
                    html += '</summary>'
                    html += '<div class="org-tree-children">'
                    for station in c_stations:
                        s_name = station.get("name", "Unknown")
                        s_status = station.get("status", "operational")
                        s_cls = "healthy" if s_status == "operational" else ("warning" if s_status == "warning" else "critical")
                        s_region = station.get("region", "")
                        s_maint = station.get("maint_count", 0)
                        s_tier = station.get("tier", "")
                        html += '<div class="org-tree-node org-tree-enter">'
                        html += '<div class="org-tree-node-row org-tree-l2">'
                        html += '<span class="org-tree-chevron leaf">\u25b6</span>'
                        html += '<span class="org-tree-icon">\U0001f4cd</span>'
                        html += '<span class="org-tree-label station">' + s_name + '</span>'
                        html += '<span class="org-tree-meta">' + s_region + '</span>'
                        if s_tier:
                            html += '<span class="org-tree-tier premium">' + s_tier + '</span>'
                        if s_maint > 0:
                            html += '<span class="org-tree-issues">' + str(s_maint) + ' issues</span>'
                        html += '<span class="org-tree-health ' + s_cls + '"></span>'
                        html += '</div></div>'
                    html += '</div></details>'
                else:
                    html += '<div class="org-tree-node org-tree-enter">'
                    html += '<div class="org-tree-node-row org-tree-l1">'
                    html += '<span class="org-tree-chevron leaf">\u25b6</span>'
                    html += '<span class="org-tree-icon">\U0001f4c4</span>'
                    html += '<span class="org-tree-label contract">' + c_name + '</span>'
                    html += tier_badge(c_tier)
                    html += '<span class="org-tree-count">' + str(c_count) + ' stations</span>'
                    html += '<span class="org-tree-value">\u20ac' + f"{c_value:,.0f}" + '</span>'
                    html += '</div></div>'

        if stations_list and not contracts:
            for station in stations_list:
                s_name = station.get("name", "Unknown")
                s_status = station.get("status", "operational")
                s_cls = "healthy" if s_status == "operational" else ("warning" if s_status == "warning" else "critical")
                s_region = station.get("region", "")
                s_maint = station.get("maint_count", 0)
                s_tier = station.get("tier", "")
                html += '<div class="org-tree-node org-tree-enter">'
                html += '<div class="org-tree-node-row org-tree-l1">'
                html += '<span class="org-tree-chevron leaf">\u25b6</span>'
                html += '<span class="org-tree-icon">\U0001f4cd</span>'
                html += '<span class="org-tree-label station">' + s_name + '</span>'
                html += '<span class="org-tree-meta">' + s_region + '</span>'
                if s_tier:
                    html += '<span class="org-tree-tier premium">' + s_tier + '</span>'
                if s_maint > 0:
                    html += '<span class="org-tree-issues">' + str(s_maint) + ' issues</span>'
                html += '<span class="org-tree-health ' + s_cls + '"></span>'
                html += '</div></div>'

        if has_children:
            html += '</div></details>'
        else:
            html += '</div>'

    html += '</div>'

    return html
