"""Visualization engine for the Architecture Hub tab."""
import random
from dataclasses import dataclass, field

# ── Architecture Topology ──

@dataclass
class ArchitectureNode:
    id: str
    label: str
    icon: str
    type: str
    status: str = "operational"
    metrics: dict = field(default_factory=dict)
    connections: list[str] = field(default_factory=list)

ARCHITECTURE_NODES = [
    ArchitectureNode("stations", "Rail Stations", "🚉", "station",
                     connections=["sensors", "mobile_edge"]),
    ArchitectureNode("sensors", "Gate Sensors", "📡", "sensor",
                     connections=["cloud_api"]),
    ArchitectureNode("mobile_edge", "Mobile Gateway", "📱", "edge",
                     connections=["cloud_api"]),
    ArchitectureNode("cloud_api", "Cloud API", "☁️", "cloud",
                     connections=["analytics", "database", "ml_engine", "compliance"]),
    ArchitectureNode("ml_engine", "ML Anomaly Engine", "🤖", "ml",
                     connections=["analytics", "notifications"]),
    ArchitectureNode("analytics", "Analytics Engine", "📊", "analytics",
                     connections=["dashboard", "maintenance"]),
    ArchitectureNode("maintenance", "Maintenance Scheduler", "🔧", "scheduler",
                     connections=["notifications"]),
    ArchitectureNode("notifications", "Notification Engine", "🔔", "service",
                     connections=["dashboard", "mobile_edge"]),
    ArchitectureNode("compliance", "Compliance & Audit", "📋", "compliance",
                     connections=[]),
    ArchitectureNode("database", "Database Cluster", "🗄️", "database",
                     connections=["dashboard"]),
    ArchitectureNode("dashboard", "Live Dashboard", "📈", "dashboard",
                     connections=["team"]),
    ArchitectureNode("team", "Response Team", "👥", "team",
                     connections=[]),
]

ARCHITECTURE_EDGES = [
    ("stations", "sensors"),
    ("stations", "mobile_edge"),
    ("sensors", "cloud_api"),
    ("mobile_edge", "cloud_api"),
    ("cloud_api", "analytics"),
    ("cloud_api", "database"),
    ("cloud_api", "ml_engine"),
    ("cloud_api", "compliance"),
    ("ml_engine", "analytics"),
    ("ml_engine", "notifications"),
    ("analytics", "dashboard"),
    ("analytics", "maintenance"),
    ("maintenance", "notifications"),
    ("database", "dashboard"),
    ("notifications", "dashboard"),
    ("notifications", "mobile_edge"),
    ("dashboard", "team"),
]


def generate_live_metrics() -> dict[str, dict]:
    """Generate simulated real-time metrics for each component."""
    uptime_base = 99.97
    return {
        "stations": {
            "total": 15, "online": random.randint(13, 15),
            "avg_latency_ms": round(random.uniform(2, 8), 1),
            "uptime": round(uptime_base - random.uniform(0, 0.5), 2),
        },
        "sensors": {
            "total": 750, "active": random.randint(710, 750),
            "data_rate_hz": random.randint(10, 60),
            "uptime": round(uptime_base - random.uniform(0, 0.8), 2),
        },
        "cloud_api": {
            "requests_s": random.randint(800, 1500),
            "p99_latency_ms": round(random.uniform(45, 120), 1),
            "error_rate": round(random.uniform(0.01, 0.15), 2),
            "uptime": round(uptime_base - random.uniform(0, 0.3), 2),
        },
        "analytics": {
            "queries_s": random.randint(120, 400),
            "avg_batch_size": random.randint(500, 2000),
            "uptime": round(uptime_base - random.uniform(0, 0.4), 2),
        },
        "database": {
            "connections": random.randint(40, 90),
            "queries_s": random.randint(3000, 9000),
            "disk_usage_pct": round(random.uniform(45, 78), 1),
            "uptime": round(uptime_base - random.uniform(0, 0.2), 2),
        },
        "dashboard": {
            "active_users": random.randint(3, 12),
            "widgets_loaded": 24,
            "refresh_rate_s": 1,
            "uptime": round(uptime_base - random.uniform(0, 0.1), 2),
        },
        "team": {
            "on_duty": random.randint(4, 8),
            "avg_response_m": round(random.uniform(1.5, 4.5), 1),
            "active_incidents": random.randint(0, 5),
            "uptime": 100.0,
        },
        "mobile_edge": {
            "active_devices": random.randint(20, 45),
            "latency_ms": round(random.uniform(15, 60), 1),
            "uptime": round(uptime_base - random.uniform(0, 0.6), 2),
        },
        "notifications": {
            "p95_delivery_ms": round(random.uniform(80, 250), 0),
            "delivery_rate": round(random.uniform(97, 99.9), 2),
            "queued": random.randint(0, 5),
            "uptime": round(uptime_base - random.uniform(0, 0.15), 2),
        },
        "ml_engine": {
            "inferences_s": random.randint(50, 200),
            "model_version": "v2.4.1",
            "anomalies_flagged": random.randint(0, 8),
            "uptime": round(uptime_base - random.uniform(0, 0.35), 2),
        },
        "compliance": {
            "audit_events_24h": random.randint(1200, 3000),
            "retention_days": 2555,  # 7 years (EU railway)
            "integrity_pct": round(random.uniform(99.9, 100), 3),
            "uptime": 100.0,
        },
        "maintenance": {
            "jobs_scheduled": random.randint(3, 12),
            "jobs_running": random.randint(0, 3),
            "jobs_failed": random.randint(0, 2),
            "uptime": round(uptime_base - random.uniform(0, 0.25), 2),
        },
    }


def _get_status_color(val: float, good: float, warn: float) -> str:
    if val >= good: return "operational"
    if val >= warn: return "degraded"
    return "critical"


def build_architecture_flow_html() -> str:
    """Build a self-contained HTML/JS component showing the architecture as a 3-tier tree.

    Three tier columns (DATA / ANALYTICS / ALERTS) with roots + always-visible
    child nodes.  Pure CSS animations — no JS, no click interactions.
    """
    stages = [
        ("stations",     "Stations",       "🚉", "rgb(59,130,246)"),
        ("mobile_edge",  "Mobile Gateway", "📱", "rgb(99,102,241)"),
        ("sensors",      "Sensors",        "📡", "rgb(6,182,212)"),
        ("cloud_api",    "Cloud API",      "☁️", "rgb(139,92,246)"),
        ("ml_engine",    "ML Anomaly",     "🤖", "rgb(236,72,153)"),
        ("analytics",    "Analytics",      "📊", "rgb(245,158,11)"),
        ("maintenance",  "Maintenance",    "🔧", "rgb(16,185,129)"),
        ("notifications","Notification",   "🔔", "rgb(239,68,68)"),
        ("compliance",   "Compliance",     "📋", "rgb(148,163,184)"),
        ("database",     "Database",       "🗄️", "rgb(0,150,136)"),
        ("dashboard",    "Dashboard",      "📈", "rgb(16,185,129)"),
        ("team",         "Team",           "👥", "rgb(236,72,153)"),
    ]
    stage_ids   = [s[0] for s in stages]
    stages_by_id = {s[0]: s for s in stages}

    _NODE_META = {
        "stations":     ("v1.0", "Gate Stations"),
        "mobile_edge":  ("v1.1", "Field Tablets"),
        "sensors":      ("v1.2", "Gate Sensors"),
        "cloud_api":    ("v2.0", "Cloud API"),
        "ml_engine":    ("v2.1", "ML Engine"),
        "analytics":    ("v2.2", "Analytics"),
        "maintenance":  ("v2.3", "Maintenance"),
        "notifications":("v1.3", "Alerts"),
        "compliance":   ("v1.4", "Compliance"),
        "database":     ("v1.5", "Database"),
        "dashboard":    ("v1.6", "Dashboard"),
        "team":         ("v1.7", "Response Team"),
    }

    # ── 3-tier tree definition ─────────────────────────────────────────────
    _TIERS = [
        {
            "id":       "tier_data", "rootId": "cloud_api",
            "label":    "DATA",  "icon": "🌐",
            "color":    "rgb(139,92,246)",
            "children": ["stations", "mobile_edge", "sensors"],
        },
        {
            "id":       "tier_compute", "rootId": "analytics",
            "label":    "ANALYTICS", "icon": "📊",
            "color":    "rgb(245,158,11)",
            "children": ["ml_engine", "maintenance"],
        },
        {
            "id":       "tier_ops", "rootId": "notifications",
            "label":    "ALERTS", "icon": "🔔",
            "color":    "rgb(239,68,68)",
            "children": ["compliance", "database", "dashboard", "team"],
        },
    ]

    # tier root IDs → 0-based index for cross-canvas particle lanes
    tier_root_ids = [t["rootId"] for t in _TIERS]         # [cloud_api, analytics, notifications]

    # colour keyed by tier_root_idx for each inter-tier lane
    tier_colors = [t["color"] for t in _TIERS]             # [CSS rgb]

    # Cache lookup: node id → _NODE_META (ver, sub_label)
    def _meta(sid): return _NODE_META.get(sid, ("v1.0", sid))

    # ── Build clean horizontal pipeline columns ──────────────────────────────
    n_roots   = len(_TIERS)
    tier_colors = [t["color"] for t in _TIERS]

    pipeline_parts = []
    for ti, t in enumerate(_TIERS):
        root_id = t["rootId"]
        rsid, rlabel, ricon, rcolor = stages_by_id[root_id]
        rver, rsub = _meta(root_id)

        children_rows = []
        for cid in t["children"]:
            csid, clabel, cicon, ccolor = stages_by_id[cid]
            cver, csub = _meta(csid)
            children_rows.append(
                f'''<div class="pipeline-child">
            <span class="child-dot" style="background:{ccolor}"></span>
            <span class="child-icon">{cicon}</span>
            <span class="child-label">{clabel}</span>
            <span class="child-sub">{csub}</span>
          </div>'''
            )
        children_html = "\n".join(children_rows)

        pipeline_parts.append(
            f'''<div class="pipeline-tier">
          <div class="tier-panel" style="border-color:{rcolor}30">
          <div class="tier-header" style="color:{rcolor}">{t['label']}</div>
          <div class="tier-root">
            <span class="root-icon">{ricon}</span>
            <span class="root-label">{rlabel}</span>
          </div>
          <div class="tier-children">
{children_html}
          </div>
        </div>
        </div>'''
        )

        if ti < n_roots - 1:
            connector_color = tier_colors[ti]
            pipeline_parts.append(
                f'''<div class="tier-connector">
          <div class="connector-line" style="background:linear-gradient(90deg,{connector_color},transparent)"></div>
          <div class="connector-dot" style="background:{connector_color};animation-delay:0s"></div>
          <div class="connector-dot" style="background:{connector_color};animation-delay:0.7s"></div>
          <div class="connector-dot" style="background:{connector_color};animation-delay:1.4s"></div>
        </div>'''
            )

    pipeline_body = "\n".join(pipeline_parts)

    html = f"""<!DOCTYPE html>
<html><head><style>
* {{ margin:0;padding:0;box-sizing:border-box; }}
body {{ background:#0b0f1a;font-family:'Inter',-apple-system,sans-serif;overflow:hidden; }}

/* ── Live indicator ── */
.live-indicator {{ display:flex;align-items:center;gap:8px;padding:8px 16px 4px;justify-content:center; }}
.live-dot {{ width:8px;height:8px;border-radius:50%;background:#10b981;animation:live-pulse 1.5s ease-in-out infinite; }}
.live-text {{ font-size:10px;font-weight:500;color:#64748b;text-transform:uppercase;letter-spacing:1.2px; }}
@keyframes live-pulse {{ 0%,100% {{ opacity:1;box-shadow:0 0 0 0 rgba(16,185,129,0.5); }} 50% {{ opacity:0.7;box-shadow:0 0 0 8px rgba(16,185,129,0); }} }}

/* ── Pipeline flow ── */
.pipeline-flow {{ display:flex;align-items:flex-start;justify-content:center;padding:8px 16px;gap:0; }}

/* ── Tier column ── */
.pipeline-tier {{ display:flex;flex-direction:column;align-items:center;animation:tier-enter 0.6s cubic-bezier(0.16,1,0.3,1) both; }}
.pipeline-tier:nth-child(1) {{ animation-delay:0.05s; }}
.pipeline-tier:nth-child(3) {{ animation-delay:0.12s; }}
.pipeline-tier:nth-child(5) {{ animation-delay:0.2s; }}
@keyframes tier-enter {{ from {{ opacity:0;transform:translateY(12px) scale(0.96); }} to {{ opacity:1;transform:translateY(0) scale(1); }} }}

/* ── Tier panel ── */
.tier-panel {{ display:flex;flex-direction:column;align-items:center;padding:10px 14px 10px;border:1px solid;border-radius:14px;background:rgba(255,255,255,0.02);backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px); }}
.tier-header {{ font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:8px;opacity:0.7;text-align:center; }}

/* ── Root node ── */
.tier-root {{ display:flex;flex-direction:column;align-items:center;padding:10px 18px;min-width:110px;background:linear-gradient(145deg,rgba(26,35,50,0.85),rgba(15,23,42,0.92));border:1px solid rgba(148,163,184,0.12);border-left:3px solid;border-left-color:inherit;border-radius:12px;transition:all 0.35s cubic-bezier(0.16,1,0.3,1);position:relative; }}
.tier-root:hover {{ border-color:rgba(59,130,246,0.35);box-shadow:0 0 20px rgba(59,130,246,0.2),0 4px 12px rgba(0,0,0,0.3);transform:translateY(-3px) scale(1.02); }}
.root-icon {{ font-size:22px;line-height:1;text-align:center; }}
.root-label {{ font-size:12px;font-weight:700;color:#e2e8f0;margin-top:3px;text-align:center;letter-spacing:0.2px; }}
.tier-root::after {{ content:'';position:absolute;inset:-2px;border-radius:14px;animation:root-pulse 4s cubic-bezier(0.4,0,0.6,1) infinite;pointer-events:none; }}
@keyframes root-pulse {{ 0%,100% {{ box-shadow:0 0 8px rgba(59,130,246,0.06); }} 50% {{ box-shadow:0 0 22px rgba(59,130,246,0.18); }} }}

/* ── Child nodes ── */
.tier-children {{ display:flex;flex-direction:column;align-items:stretch;gap:5px;margin-top:10px;width:100%; }}
.pipeline-child {{ display:flex;align-items:center;gap:7px;padding:6px 10px;background:rgba(255,255,255,0.025);border:1px solid rgba(148,163,184,0.07);border-radius:8px;transition:all 0.3s cubic-bezier(0.16,1,0.3,1);animation:child-enter 0.4s ease-out both; }}
.pipeline-child:nth-child(1) {{ animation-delay:0.08s; }}
.pipeline-child:nth-child(2) {{ animation-delay:0.14s; }}
.pipeline-child:nth-child(3) {{ animation-delay:0.2s; }}
.pipeline-child:nth-child(4) {{ animation-delay:0.26s; }}
.pipeline-child:hover {{ border-color:rgba(59,130,246,0.3);background:rgba(59,130,246,0.07);transform:translateX(4px) scale(1.02);box-shadow:0 0 12px rgba(59,130,246,0.12); }}
@keyframes child-enter {{ from {{ opacity:0;transform:translateX(-6px); }} to {{ opacity:1;transform:translateX(0); }} }}
.child-dot {{ width:6px;height:6px;border-radius:50%;flex-shrink:0;box-shadow:0 0 6px currentColor; }}
.child-icon {{ font-size:13px;line-height:1;flex-shrink:0; }}
.child-label {{ font-size:9px;font-weight:500;color:#94a3b8; }}
.child-sub {{ font-size:7px;color:#64748b;margin-left:auto;opacity:0.5; }}

/* ── Tier connectors ── */
.tier-connector {{ width:48px;margin-top:54px;position:relative;flex-shrink:0;overflow:visible; }}
.connector-line {{ height:2px;border-radius:2px;width:100%; }}
.connector-dot {{ position:absolute;top:-3px;width:8px;height:8px;border-radius:50%;opacity:0;animation:connector-flow 2.1s cubic-bezier(0.4,0,0.2,1) infinite;box-shadow:0 0 8px currentColor; }}
@keyframes connector-flow {{ 0% {{ left:-4px;opacity:0;transform:scale(0.5); }} 15% {{ opacity:1;transform:scale(1); }} 75% {{ opacity:1;transform:scale(1); }} 100% {{ left:calc(100% - 4px);opacity:0;transform:scale(0.3); }} }}
</style>
</head><body>
<div class="live-indicator"><div class="live-dot"></div><div class="live-text">Data Pipeline Live</div></div>
<div class="pipeline" id="pipeline">
  <div class="pipeline-flow">
{pipeline_body}
  </div>
</div>
</body></html>"""
    return html


# ── Loophole Analysis ──

@dataclass
class Loophole:
    id: str
    type: str  # technical, operational
    severity: str  # critical, high, medium, low
    title: str
    description: str
    impact: str
    suggestion: str
    location: str = ""
    affected_persona: str = ""


TECHNICAL_LOOPHOLES = [
    Loophole("T001", "technical", "high", "No Redundancy at Leipzig Hbf",
             "Leipzig Hbf has a single gate controller with no failover. A hardware failure would disable all PSD operations.",
             "Potential 45+ min service disruption affecting 12 platforms",
             "Deploy secondary gate controller with automatic failover", "Leipzig Hbf", ""),
    Loophole("T002", "technical", "critical", "Sensor Network Latency Spikes",
             "Satellite stations (Bremen, Essen) experience >200ms latency spikes during peak hours, causing delayed telemetry.",
             "Real-time monitoring blindspots of 3-8 seconds during spikes",
             "Upgrade to fiber-optic backbone or deploy edge processing nodes", "Bremen, Essen", ""),
    Loophole("T003", "technical", "medium", "Legacy Protocol Gateway",
             "3 stations still using RS-485 to IP gateways with no encryption or authentication.",
             "Potential for unauthorized access to gate control systems",
             "Replace legacy gateways with TLS 1.3 capable industrial IoT gateways", "Dortmund, Essen, Bremen", ""),
    Loophole("T004", "technical", "medium", "Database Write Bottleneck",
             "Single primary DB node handles all write operations. During cascade events, replication lag exceeds 5s.",
             "Dashboard may show stale data during critical incidents",
             "Implement read replicas and connection pooling", "Cloud Infrastructure", ""),
    Loophole("T005", "technical", "high", "No Cross-Region Disaster Recovery",
             "All infrastructure is in a single region. No DR plan for regional outages.",
             "Complete system unavailability in case of regional cloud failure",
             "Establish active-passive DR in a secondary region", "Cloud Infrastructure", ""),
    Loophole("T006", "technical", "low", "Alert Fatigue — Low Signal-to-Noise",
             "Monitoring generates ~200 alerts/day, of which only ~15% require action. Critical alerts get buried.",
             "Mean time to acknowledge critical alerts is 4.2 min (target: <1 min)",
             "Implement alert deduplication, severity bucketing, and intelligent escalation", "All Stations", ""),
    Loophole("T007", "technical", "critical", "PSD Gate Actuator Commands — No Mutual-TLS Authentication",
             "Platform screen door open/close commands transit the sensor network without mutual-TLS or command signing. Any compromised sensor node can issue gate commands.",
             "An attacker could open or close PSD gates during a train boarding cycle — direct passenger safety hazard and potential fatality",
             "Mandate mutual-TLS between all gate controllers and Cloud API; sign every actuator command with an HMAC derived from a hardware security module (HSM)"),
    Loophole("T008", "technical", "high", "Vendor Remote Access — Shared Static SSH Key, No Jump Host",
             "Gate hardware vendor QSRL uses a shared static private SSH key for remote support. The key is stored in a plain-text config file on 3 workstations and never rotates.",
             "Vendor credential leak grants persistent 3rd-party access to the PSD control network; no session audit trail exists",
             "Replace shared key with one-time SSH certificates via HashiCorp Vault; enforce jump-host bastion with full session recording; rotate quarterly"),
    Loophole("T009", "technical", "high", "Sensor Data at Rest — No Transparent Data Encryption",
             "Gate sensor telemetry stored in PostgreSQL has no Transparent Data Encryption (TDE). A compromised DB file or backup dump exposes 7 years of operational history.",
             "GDPR Article 32 violation; rail audit logs are personal/safety data requiring encryption at rest; fines up to 4% of annual revenue",
             "Enable TDE on all primary and standby clusters; rotate master encryption keys every 90 days; store keys in a cloud KMS with audit logging"),
    Loophole("T010", "technical", "medium", "EN 50128 SIL-4 Audit Trail — Not Yet Implemented",
             "The Compliance & Audit node is newly added. No deterministic, append-only audit log currently exists for every gate actuator decision — a mandatory requirement under EN 50128 for SIL-4 railway safety systems.",
             "Cannot achieve DB Netz / EU railway certification without signed audit trail for all safety-critical gate events; project certification blocked",
             "Implement append-only audit log with hardware-RNG signatures per gate event; minimum 7-year retention; quarterly integrity checks by appointed Compliance Officer"),
]

OPERATIONAL_LOOPHOLES = [
    Loophole("O001", "operational", "critical", "Shift Supervisor Single Point of Failure",
             "Shift Supervisor is assigned to all 'All' type incidents, creating a bottleneck. When overloaded (>3 incidents), response time increases 300%.",
             "Average response time for coordination tasks: 7.2 min (vs 2.1 min baseline)",
             "Implement deputy supervisor rotation and auto-escalation if response > 4 min", "", "Shift Supervisor"),
    Loophole("O002", "operational", "high", "Fatigue-Driven Error Cycle",
             "Team members working >4 consecutive hours show 40% higher error rate. Fatigue >70% leads to cascading failures.",
             "Incidents assigned to fatigued personnel are 2.3x more likely to fail",
             "Enforce mandatory break after 4h. Auto-redirect incidents when fatigue >65%", "", "All Operations"),
    Loophole("O003", "operational", "medium", "Weather Response Protocol Gap",
             "No formalized severe weather escalation protocol. Weather-modified incidents see 35% longer resolution times.",
             "Storm-related gate failures take avg 12 min to resolve (vs 7 min normal)",
             "Create weather severity matrix with pre-assigned response teams and automated trigger thresholds", "", "Safety Officer"),
    Loophole("O004", "operational", "high", "Knowledge Silos — Cross-Training Gap",
             "Gate Technicians are not trained on network issues; Network Controllers lack gate hardware knowledge. Incident reassignment rate: 22%.",
             "22% of incidents require reassignment, adding avg 3.5 min to response time",
             "Implement monthly cross-training rotations and shared incident playbooks", "", "Gate Technician, Network Controller"),
    Loophole("O005", "operational", "medium", "Night Shift Understaffing",
             "Night shifts operate with 40% fewer personnel but handle 30% of all critical incidents. Solo operators lack backup.",
             "Night shift incidents have 28% lower success rate and 45% longer resolution time",
             "Ensure minimum 2-person coverage on night shifts. Implement night shift premium to retain staff", "", "All Operations"),
    Loophole("O006", "operational", "low", "Escalation Path Ambiguity",
             "No clear escalation trigger criteria. 18% of critical incidents are escalated, but 40% of those are escalated incorrectly (too early or too late).",
             "Inappropriate escalations add ~4 min overhead per incident",
             "Define clear escalation criteria: time-based (3 min), severity-based, and cascade-based triggers", "", "All Leadership"),
    Loophole("O010", "operational", "high", "Severe Weather Runbook Absent",
             "No runbook exists for weather-driven escalation. Munich and Cologne show a documented 35% increase in resolution time during snowfall, but no automated trigger or pre-assigned response teams exist.",
             "Delayed weather-response cascades across entire platforms during extreme events; no dependency on DWD or equivalent weather API",
             "Create a 3-level weather matrix (Mild / Severe / Extreme) using DWD Wetterwarnungen API; auto-assign specialist response team per level; integrate into Notification Engine"),
    Loophole("O011", "operational", "medium", "Cross-Language Incident Runbooks",
             "Operations team spans DACH-region (German) and India (English). Incident runbooks are authored and maintained only in German, with no English translation.",
             "Average incident resolution time for India-based engineers is 4.8 min vs 2.1 min for German-based colleagues — a 128% gap driven by language barrier",
             "Translate all runbooks to English as the single source of truth; host on shared Confluence with bilingual search; assign ownership to COO Namrata Joshi"),
    Loophole("O012", "operational", "medium", "Runbook Version Drift — Manual Distribution",
             "Runbooks are updated monthly but distributed via email/WhatsApp. 28% of field staff report working from v2 while central operations team has already deployed v3.",
             "Wrong runbook version causes incorrect escalation chains, adding ~40% to MTTR for affected incidents",
             "Publish runbooks as versioned internal package; pin version per shift roster; trigger a Notification Engine alert when a new version is deployed to any station"),
    Loophole("O013", "operational", "low", "QSRL Vendor SLA — No 24/7 Hardware Support",
             "Gate hardware vendor QSRL only provides support Mon–Fri 09:00–17:00 CET. Incidents at 2–5am wait 6–8 hours for vendor response.",
             "Night-shift hardware incidents cannot be resolved until 9am business hours, leaving gates non-operational overnight",
             "Negotiate 24/7 on-call vendor support SLA; identify a local Hanse-specific on-call contractor; keep spare gate actuator modules on-site at high-traffic stations"),
]


def analyze_loopholes(history: dict | None = None) -> tuple[list[Loophole], list[Loophole]]:
    """Return technical and operational loopholes, optionally filtered by session history."""
    import copy
    tech = copy.deepcopy(TECHNICAL_LOOPHOLES)
    oper = copy.deepcopy(OPERATIONAL_LOOPHOLES)

    if history and history.get("metrics"):
        m = history["metrics"]
        avg_resp = m.get("avg_response_time", 0)
        success_rate = m.get("success_rate", 100)
        escalated = m.get("escalated", 0)
        total = m.get("total_incidents", 1)

        if avg_resp > 5:
            oper.append(Loophole("O007", "operational", "high",
                                 "Slow Average Response Time",
                                 f"Average response time is {avg_resp:.1f}m, exceeding the 3m target. Team may be overloaded or assignment logic inefficient.",
                                 "Delayed response increases risk of cascading failures",
                                 "Review workload distribution and consider adding on-call personnel during peak hours"))
        if success_rate < 75:
            oper.append(Loophole("O008", "operational", "critical",
                                 "Critically Low Resolution Success Rate",
                                 f"Only {success_rate:.0f}% of incidents are resolved successfully. Team capability gaps need urgent attention.",
                                 "Low success rate erodes system reliability and customer trust",
                                 "Immediate targeted retraining and review of incident assignment matching"))
        if escalated / total > 0.25:
            oper.append(Loophole("O009", "operational", "medium",
                                 "High Escalation Rate",
                                 f"{escalated}/{total} incidents ({escalated/total*100:.0f}%) required escalation. Indicates insufficient first-response capability.",
                                 "High escalation load on leadership reduces strategic oversight capacity",
                                 "Strengthen first-response training and improve initial triage accuracy"))

        # ── Dynamic O014: High weather-driven incident rate ──────────────────
        root_causes = m.get("root_causes", {})
        if root_causes:
            weather_count = sum(
                v for k, v in root_causes.items()
                if "weather" in k.lower()
            )
            weather_rate = weather_count / total if total > 0 else 0
            if weather_rate > 0.30:
                oper.append(Loophole("O014", "operational", "medium",
                                     "High Weather-Driven Incident Rate",
                                     f"{weather_rate*100:.0f}% of incidents ({weather_count}/{total}) are weather-related. "
                                     "The absence of a dedicated weather escalation protocol (see O010) amplifies response delays.",
                                     "Extended MTTR during weather events risks cascading gate failures across multiple platforms",
                                     "Deploy DWD Wetterwarnungen API in the Notification Engine; auto-elevate to Severe protocol when DAS-Level 3 is reached"))

        # ── Dynamic O015: Team compliance fragility (high fatigue + high escalation) ──
        tf = m.get("team_fatigue", {})
        if tf and isinstance(tf, dict):
            fatigue_vals = [
                v["fatigue"] if isinstance(v, dict) else v
                for v in tf.values()
            ]
            avg_fatigue = sum(fatigue_vals) / \
                len(fatigue_vals) if fatigue_vals else 0
            if avg_fatigue > 70 and (escalated / max(total, 1)) > 0.20:
                oper.append(Loophole("O015", "operational", "high",
                                     "Compliance Fragility — High Fatigue With Elevated Escalation",
                                     f"Team average fatigue is {avg_fatigue:.0f}% while {escalated}/{total} incidents ({escalated/total*100:.0f}%) required escalation. "
                                     "Fatigue-driven decisions during incident triage risk protocol deviations and regulatory non-compliance.",
                                     "Fatigue-impaired operators may skip mandatory compliance checkpoints during escalated incidents",
                                     "Reset accumulated fatigue after 4h; auto-redirect escalation decisions to rested supervisor; log all fatigue-override events in the Compliance Audit node"))

    return tech, oper


# ── Recommendation Engine ──

@dataclass
class Recommendation:
    id: str
    priority: str  # critical, high, medium, info
    title: str
    description: str
    area: str  # team, process, system, training
    impact: str
    actionable: str


def generate_recommendations(metrics: dict | None = None,
                             root_causes: dict | None = None,
                             personas: list | None = None) -> list[Recommendation]:
    """Generate prioritized recommendations based on simulation metrics and personas."""
    recs = []

    # System-level recommendations
    recs.extend([
        Recommendation("R001", "critical", "Deploy Redundant Gate Controller at Leipzig",
                       "Leipzig Hbf is the single busiest station without controller redundancy. A single hardware fault disables 100% of PSD operations.",
                       "system", "Prevents ~45min service disruption, protects 12 platforms",
                       "Budget and deploy secondary controller within next maintenance cycle"),
        Recommendation("R002", "high", "Implement Edge Processing for Low-Latency Stations",
                       "Satellite stations experience latency spikes due to centralized processing. Edge nodes can reduce p99 latency from 200ms to <15ms.",
                       "system", "Eliminates monitoring blindspots, enables real-time response",
                       "Pilot edge gateway at Bremen station, assess impact before rollout"),
        Recommendation("R003", "high", "Enforce Mandatory Fatigue Breaks",
                       "Team members with fatigue >70% show 40% higher error rates. Auto-redirect incidents and enforce breaks.",
                       "process", "Reduces error rate, prevents cascading failures from fatigued decisions",
                       "Configure auto-escalation when fatigue exceeds 65% and enforce 15min break at 4h"),
        Recommendation("R004", "medium", "Cross-Training Rotation Program",
                       "22% incident reassignment rate indicates knowledge silos. Monthly cross-training between Gate Techs and Network Controllers.",
                       "training", "Reduces reassignment rate, improves first-response success",
                       "Schedule monthly half-day cross-training sessions with simulation drills"),
        Recommendation("R005", "medium", "Upgrade Legacy Protocol Gateways",
                       "3 stations still run unencrypted RS-485 to IP gateways. Security audit required.",
                       "system", "Eliminates unauthorized access risk to gate control systems",
                       "Replace gateways with TLS 1.3 capable units within 90 days"),
        Recommendation("R006", "info", "Establish Disaster Recovery Plan",
                       "All infrastructure is single-region. No tested DR procedure exists for regional outages.",
                       "process", "Ensures business continuity during regional cloud/provider failures",
                       "Design and test active-passive DR setup in secondary region"),
        Recommendation("R007", "info", "Implement Alert Intelligence",
                       "Current 200 alerts/day (15% actionable) causes alert fatigue. ML-based deduplication and smart escalation needed.",
                       "system", "Reduces MTTA by 4x, ensures critical alerts always visible",
                       "Evaluate anomaly correlation engine and deploy severity bucketing"),
    ])

    # Simulation-derived recommendations
    if metrics:
        sr = metrics.get("success_rate", 100)
        if sr < 80:
            recs.append(Recommendation("R008", "critical",
                         "Urgent Team Performance Review",
                         f"Success rate is {sr:.0f}% — well below the 90% target. Root cause analysis recommended.",
                         "team", "Improving success rate to 90%+ is critical for SLA compliance",
                         "Conduct performance review, identify weak areas, schedule intensive training"))

        avg_rt = metrics.get("avg_response_time", 0)
        if avg_rt > 4:
            recs.append(Recommendation("R009", "high",
                         "Optimize Incident Assignment Workflow",
                         f"Average response time is {avg_rt:.1f}m. Consider auto-assignment based on specialty + current load.",
                         "process", "Reducing response time by 40% improves incident resolution outcomes",
                         "Implement smart assignment: match incident type to persona specialty, balanced by current load"))

    if root_causes:
        top_cause = max(root_causes, key=root_causes.get)
        top_count = root_causes[top_cause]
        if top_count > 3:
            recs.append(Recommendation("R010", "medium",
                         f"Address Root Cause: '{top_cause}'",
                         f"'{top_cause}' was identified in {top_count} incidents — the most frequent root cause.",
                         "process", f"Reducing '{top_cause}' incidents by 50% would significantly improve overall metrics",
                         f"Investigate '{top_cause}' patterns and implement preventive measures"))

    if personas:
        worst = min(personas, key=lambda p: p.success_rate_computed)
        if worst.success_rate_computed < 80:
            recs.append(Recommendation("R011", "high",
                         f"Support: {worst.name} ({worst.role})",
                         f"{worst.name} has the lowest success rate ({worst.success_rate_computed:.0f}%). Additional training or workload adjustment needed.",
                         "team", "Improving weakest performer lifts overall team capability",
                         "Assign mentor, reduce active load by 30%, and retrain on weakness areas"))

    return sorted(recs, key=lambda r: ["critical", "high", "medium", "info"].index(r.priority))


def get_station_vulnerability_scores() -> list[dict]:
    """Return per-station vulnerability scores for heatmap visualization."""
    return [
        {"station": "Berlin Hbf", "score": 12, "critical": 1, "high": 2, "medium": 4, "low": 5},
        {"station": "München Hbf", "score": 8, "critical": 0, "high": 1, "medium": 3, "low": 4},
        {"station": "Hamburg Hbf", "score": 15, "critical": 2, "high": 3, "medium": 5, "low": 5},
        {"station": "Frankfurt Hbf", "score": 10, "critical": 1, "high": 1, "medium": 4, "low": 4},
        {"station": "Köln Hbf", "score": 18, "critical": 2, "high": 4, "medium": 6, "low": 6},
        {"station": "Stuttgart Hbf", "score": 6, "critical": 0, "high": 1, "medium": 2, "low": 3},
        {"station": "Leipzig Hbf", "score": 22, "critical": 3, "high": 5, "medium": 7, "low": 7},
        {"station": "Düsseldorf Hbf", "score": 9, "critical": 1, "high": 1, "medium": 3, "low": 4},
        {"station": "Dortmund Hbf", "score": 14, "critical": 1, "high": 3, "medium": 5, "low": 5},
        {"station": "Essen Hbf", "score": 11, "critical": 1, "high": 2, "medium": 4, "low": 4},
        {"station": "Hannover Hbf", "score": 7, "critical": 0, "high": 1, "medium": 2, "low": 4},
        {"station": "Bremen Hbf", "score": 13, "critical": 1, "high": 3, "medium": 4, "low": 5},
        {"station": "Nürnberg Hbf", "score": 5, "critical": 0, "high": 0, "medium": 2, "low": 3},
        {"station": "Dresden Hbf", "score": 4, "critical": 0, "high": 0, "medium": 1, "low": 3},
        {"station": "Mannheim Hbf", "score": 6, "critical": 0, "high": 1, "medium": 2, "low": 3},
    ]
