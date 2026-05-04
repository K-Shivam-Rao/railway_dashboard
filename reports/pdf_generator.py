"""
PDF Report Generator for SicherGleis Pro
Merged from report_generator.py and Backend/dashboard.py
"""
import io
import tempfile
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    Image,
    HRFlowable,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib.colors import HexColor
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO


# ─────────────────────────────────────────────
# COMPANY PROFILE REPORT FUNCTIONS
# ─────────────────────────────────────────────

COLORS = {
    "primary": HexColor("#1E3C72"),
    "secondary": HexColor("#2A5298"),
    "accent": HexColor("#00c0ff"),
    "gold": HexColor("#ffd700"),
    "dark": HexColor("#0b0f1a"),
    "light": HexColor("#f0f4f8"),
    "text": HexColor("#1a1a2e"),
    "subtext": HexColor("#4a4a5a"),
}


def get_company_data():
    """Return company information for the report."""
    return {
        "name": "SicherGleis GmbH",
        "tagline": "Precision Railway Safety Systems",
        "vision": "Suraksha (Safety-First) + German Engineering Excellence",
        "markets": "DACH Region (Germany, Austria, Switzerland) + India",
        "website": "www.sicher-gleis.com",
        "email": "contact@sicher-gleis.com",
        "established": "2023",
    }


def get_leadership_team():
    """Return leadership team information."""
    return [
        {
            "name": "Khushboo Patil",
            "role": "Chief Executive Officer (CEO)",
            "bio": "Visionary leader with 15+ years in railway technology and business development. Led expansion to 15+ German railway stations and secured €2.5M in Series A funding.",
            "experience": "15+ years in Railway Technology and Business Development",
            "education": "MBA, Technical University of Munich",
            "specialization": "Strategic Partnerships, Market Entry Strategy",
        },
        {
            "name": "Namrata Joshi",
            "role": "Chief Operating Officer (COO)",
            "bio": "Operations expert with 12+ years in operations and project management. Managed rollout of 200+ PSD units across Germany with 99.5% on-time delivery rate.",
            "experience": "12+ years in Operations and Project Management",
            "education": "MSc Operations Management, ETH Zurich",
            "specialization": "Large-scale infrastructure rollouts",
        },
        {
            "name": "Kona Shivam Rao",
            "role": "Chief Technology Officer (CTO)",
            "bio": "Technology pioneer with 18+ years in systems engineering and IoT. Patented 3 safety-critical sensor technologies and achieved SIL-2 safety certification.",
            "experience": "18+ years in Systems Engineering and IoT",
            "education": "PhD Computer Science, TU Berlin",
            "specialization": "IoT sensors, Edge computing, Safety systems",
        },
        {
            "name": "Sanika Kale",
            "role": "Chief Product Officer (CPO)",
            "bio": "Product strategist with 10+ years in product management and UX. Designed award-winning operator dashboard and reduced user onboarding time by 60%.",
            "experience": "10+ years in Product Management and UX",
            "education": "MDes Product Design, IIT Bombay",
            "specialization": "User-centric safety interfaces",
        },
        {
            "name": "Nikhil Chavan",
            "role": "Chief Financial Officer (CFO)",
            "bio": "Financial leader with 14+ years in finance and investment banking. Raised €5M in total funding and achieved 40% YoY revenue growth.",
            "experience": "14+ years in Finance and Investment Banking",
            "education": "CFA Charterholder, Wharton MBA",
            "specialization": "Infrastructure financing, SaaS metrics",
        },
    ]


def get_services():
    """Return services offered by the company."""
    return [
        {
            "title": "Platform Screen Door (PSD) Systems",
            "description": "Advanced PSD systems with smart sensors, automated gate synchronization, and real-time monitoring for subway, light rail, and commuter train platforms.",
            "features": [
                "Intelligent door state detection (open/closing/closed/jammed/offline)",
                "Temperature and vibration monitoring",
                "Passenger flow optimization",
                "Train synchronization scoring",
            ],
        },
        {
            "title": "Predictive Maintenance Analytics",
            "description": "AI-powered predictive maintenance system that forecasts potential failures before they occur, minimizing downtime and maintenance costs.",
            "features": [
                "7-day risk trajectory forecasting",
                "Multi-factor risk scoring (0-100)",
                "Maintenance status classification (OPTIMAL → CRITICAL)",
                "Automated alert generation",
            ],
        },
        {
            "title": "Real-Time Operations Dashboard",
            "description": "Comprehensive dashboard for monitoring station operations, managing incidents, and tracking performance metrics in real-time.",
            "features": [
                "Live PSD gate monitoring",
                "Incident logging and management",
                "Network-wide overview",
                "Mobile-responsive design",
            ],
        },
        {
            "title": "Customer Segmentation & Business Intelligence",
            "description": "RFM-based customer segmentation, contract health scoring, and renewal forecasting for strategic business planning.",
            "features": [
                "Recency, Frequency, Monetary analysis",
                "At-risk account identification",
                "Renewal value forecasting",
                "Customer portfolio management",
            ],
        },
        {
            "title": "Consulting & Implementation Services",
            "description": "End-to-end consulting services for PSD system design, installation, and integration with existing rail infrastructure.",
            "features": [
                "Site assessment and planning",
                "System design and engineering",
                "Installation and commissioning",
                "Training and support",
            ],
        },
    ]


def get_case_studies():
    """Return case studies/projects completed."""
    return [
        {
            "title": "Berlin Hauptbahnhof PSD Integration",
            "description": "Deployed a comprehensive Platform Screen Door system at Berlin's central railway station, integrating with existing S-Bahn and U-Bahn networks.",
            "results": [
                "40% reduction in platform edge incidents",
                "99.8% system uptime achieved",
                "Real-time passenger flow monitoring for 12 platforms",
            ],
        },
        {
            "title": "Munich S-Bahn Predictive Maintenance",
            "description": "Implemented predictive maintenance analytics across the Munich S-Bahn network, enabling proactive maintenance scheduling.",
            "results": [
                "35% reduction in unplanned maintenance events",
                "€2.1M annual maintenance cost savings",
                "Zero critical failures in 18 months",
            ],
        },
        {
            "title": "Vienna U-Bahn Network Upgrade",
            "description": "Upgraded legacy gate systems across Vienna's U-Bahn network with IoT-enabled smart sensors and centralized monitoring.",
            "results": [
                "50,000+ daily passenger flow optimization",
                "Integrated with Vienna transport API",
                "24/7 real-time monitoring dashboard",
            ],
        },
        {
            "title": "Indian Metro Rail Authority (MRA) Pilot",
            "description": "Pilot deployment of advanced PSD systems across select Indian metro stations, adapting technology for high-volume passenger environments.",
            "results": [
                "Successfully handled 25,000+ peak hour passengers",
                "85% sync efficiency achieved",
                "Awarded 'Innovation in Urban Transit' 2024",
            ],
        },
    ]


def create_cover_page(elements, styles):
    """Create the cover page for the PDF report."""
    company = get_company_data()
    
    title_style = ParagraphStyle(
        "CoverTitle",
        parent=styles["Title"],
        fontSize=36,
        textColor=COLORS["primary"],
        spaceAfter=20,
        alignment=TA_CENTER,
    )
    
    subtitle_style = ParagraphStyle(
        "CoverSubtitle",
        parent=styles["Normal"],
        fontSize=18,
        textColor=COLORS["secondary"],
        spaceAfter=40,
        alignment=TA_CENTER,
    )
    
    tagline_style = ParagraphStyle(
        "Tagline",
        parent=styles["Normal"],
        fontSize=14,
        textColor=COLORS["subtext"],
        spaceAfter=60,
        alignment=TA_CENTER,
    )
    
    elements.append(Spacer(1, 2.5 * inch))
    elements.append(Paragraph("SicherGleis GmbH", title_style))
    elements.append(Paragraph(company["tagline"], subtitle_style))
    elements.append(Paragraph(f"\"{company['vision']}\"", tagline_style))
    
    elements.append(Spacer(1, 1.5 * inch))
    
    report_title = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontSize=24,
        textColor=COLORS["dark"],
        spaceAfter=10,
        alignment=TA_CENTER,
    )
    elements.append(Paragraph("Company Profile & Services", report_title))
    
    report_subtitle = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontSize=14,
        textColor=COLORS["subtext"],
        alignment=TA_CENTER,
    )
    elements.append(Paragraph("For Prospective Clients", report_subtitle))
    
    elements.append(Spacer(1, 2 * inch))
    elements.append(Paragraph(f"<b>Prepared:</b> {datetime.now().strftime('%B %Y')}", styles["Normal"]))
    elements.append(PageBreak())


def create_company_overview(elements, styles):
    """Create the company overview section."""
    company = get_company_data()
    
    section_title = ParagraphStyle(
        "SectionTitle",
        parent=styles["Heading1"],
        fontSize=20,
        textColor=COLORS["primary"],
        spaceAfter=15,
        pageBreakBefore=False,
    )
    
    elements.append(Paragraph("About SicherGleis", section_title))
    elements.append(Spacer(1, 0.2 * inch))
    
    intro_text = f"""
    SicherGleis delivers precision-engineered Platform Screen Door (PSD) systems that unite 
    <b>Suraksha</b> (safety-first philosophy) with German engineering excellence to create 
    safe, intelligent, and future-ready urban rail infrastructure.
    """
    elements.append(Paragraph(intro_text, styles["Normal"]))
    elements.append(Spacer(1, 0.3 * inch))
    
    elements.append(Paragraph("<b>Our Vision</b>", styles["Normal"]))
    elements.append(Paragraph(company["vision"], styles["Normal"]))
    elements.append(Spacer(1, 0.2 * inch))
    
    elements.append(Paragraph("<b>Target Markets</b>", styles["Normal"]))
    elements.append(Paragraph(company["markets"], styles["Normal"]))
    elements.append(Spacer(1, 0.2 * inch))
    
    elements.append(Paragraph("<b>Established</b>", styles["Normal"]))
    elements.append(Paragraph(company["established"], styles["Normal"]))


def create_services_section(elements, styles):
    """Create the services section."""
    services = get_services()
    
    section_title = ParagraphStyle(
        "SectionTitle",
        parent=styles["Heading1"],
        fontSize=20,
        textColor=COLORS["primary"],
        spaceAfter=15,
        pageBreakBefore=False,
    )
    
    elements.append(Paragraph("Our Services", section_title))
    elements.append(Spacer(1, 0.2 * inch))
    
    for i, service in enumerate(services, 1):
        service_title = ParagraphStyle(
            f"ServiceTitle{i}",
            parent=styles["Heading2"],
            fontSize=14,
            textColor=COLORS["secondary"],
            spaceAfter=8,
        )
        elements.append(Paragraph(f"{i}. {service['title']}", service_title))
        elements.append(Spacer(1, 0.1 * inch))
        
        elements.append(Paragraph(service["description"], styles["Normal"]))
        elements.append(Spacer(1, 0.1 * inch))
        
        features_text = "<b>Key Features:</b> " + ", ".join(service["features"])
        elements.append(Paragraph(features_text, styles["Normal"]))
        elements.append(Spacer(1, 0.3 * inch))


def create_case_studies_section(elements, styles):
    """Create the case studies/projects section."""
    projects = get_case_studies()
    
    section_title = ParagraphStyle(
        "SectionTitle",
        parent=styles["Heading1"],
        fontSize=20,
        textColor=COLORS["primary"],
        spaceAfter=15,
        pageBreakBefore=False,
    )
    
    elements.append(Paragraph("Projects & Case Studies", section_title))
    elements.append(Spacer(1, 0.2 * inch))
    
    for i, project in enumerate(projects, 1):
        project_title = ParagraphStyle(
            f"ProjectTitle{i}",
            parent=styles["Heading2"],
            fontSize=14,
            textColor=COLORS["secondary"],
            spaceAfter=8,
        )
        elements.append(Paragraph(f"{i}. {project['title']}", project_title))
        elements.append(Spacer(1, 0.1 * inch))
        
        elements.append(Paragraph(project["description"], styles["Normal"]))
        elements.append(Spacer(1, 0.1 * inch))
        
        results = "<b>Results:</b><br/>" + "<br/>".join([f"• {r}" for r in project["results"]])
        elements.append(Paragraph(results, styles["Normal"]))
        elements.append(Spacer(1, 0.3 * inch))


def create_team_section(elements, styles):
    """Create the leadership team section."""
    team = get_leadership_team()
    
    team_title = ParagraphStyle(
        "TeamTitle",
        parent=styles["Heading1"],
        fontSize=20,
        textColor=COLORS["primary"],
        spaceAfter=15,
        pageBreakBefore=False,
    )
    
    elements.append(Paragraph("Leadership Team", team_title))
    elements.append(Spacer(1, 0.2 * inch))
    
    team_data = [["Name", "Role"]]
    for member in team:
        team_data.append([member["name"], member["role"]])
    
    team_table = Table(team_data, colWidths=[2.5 * inch, 3 * inch])
    team_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), COLORS["primary"]),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 12),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 1), (-1, -1), 10),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 12),
                ("GRID", (0, 0), (-1, -1), 1, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, HexColor("#f8f9fa")]),
            ]
        )
    )
    elements.append(team_table)
    elements.append(Spacer(1, 0.3 * inch))
    
    for member in team:
        member_name = ParagraphStyle(
            "MemberName",
            parent=styles["Heading3"],
            fontSize=11,
            textColor=COLORS["dark"],
            spaceAfter=4,
        )
        elements.append(Paragraph(f"<b>{member['name']}</b> - {member['role']}", member_name))
        elements.append(Paragraph(member["bio"], styles["Normal"]))
        elements.append(Spacer(1, 0.2 * inch))


def create_contact_section(elements, styles):
    """Create the contact section."""
    company = get_company_data()
    
    section_title = ParagraphStyle(
        "SectionTitle",
        parent=styles["Heading1"],
        fontSize=20,
        textColor=COLORS["primary"],
        spaceAfter=15,
        pageBreakBefore=False,
    )
    
    elements.append(Paragraph("Contact & Next Steps", section_title))
    elements.append(Spacer(1, 0.2 * inch))
    
    elements.append(Paragraph("<b>Website:</b> " + company["website"], styles["Normal"]))
    elements.append(Paragraph("<b>Email:</b> " + company["email"], styles["Normal"]))
    elements.append(Spacer(1, 0.3 * inch))
    
    cta_text = """
    We invite you to connect with us to discuss how SicherGleis can enhance safety and efficiency 
    in your railway infrastructure. Our team is ready to provide consultation, demonstrations, 
    and customized proposals for your requirements.
    """
    elements.append(Paragraph(cta_text, styles["Normal"]))
    elements.append(Spacer(1, 0.5 * inch))
    
    elements.append(Paragraph(
        "<i>Thank you for your interest in SicherGleis GmbH</i>",
        styles["Normal"]
    ))


def generate_client_report():
    """Generate the complete client report PDF."""
    buffer = io.BytesIO()
    
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    styles.add(
        ParagraphStyle(
            name="Justified",
            parent=styles["Normal"],
            alignment=TA_JUSTIFY,
        )
    )
    
    create_cover_page(elements, styles)
    create_company_overview(elements, styles)
    elements.append(PageBreak())
    
    create_services_section(elements, styles)
    elements.append(PageBreak())
    
    create_case_studies_section(elements, styles)
    elements.append(PageBreak())
    
    create_team_section(elements, styles)
    elements.append(PageBreak())
    
    create_contact_section(elements, styles)
    
    doc.build(elements)
    
    buffer.seek(0)
    return buffer


def get_report_bytes():
    """Get the PDF report as bytes."""
    pdf_buffer = generate_client_report()
    return pdf_buffer.getvalue()


# ─────────────────────────────────────────────
# SAAS FINANCIAL REPORT FUNCTIONS
# ─────────────────────────────────────────────

def generate_complete_pdf_report(df_base, scenario_name, simulation_months, starting_customers, breakeven_base, bytes_list):
    """Generate complete PDF report with charts and tables."""
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=0.5*inch, leftMargin=0.5*inch, topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()
    
    DARK_BLUE = HexColor('#1a237e')
    MEDIUM_BLUE = HexColor('#0277bd')
    TEXT_DARK = HexColor('#263238')
    
    title_s = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=24, spaceAfter=8, alignment=TA_CENTER, textColor=DARK_BLUE, fontName='Helvetica-Bold')
    subtitle_s = ParagraphStyle('Subtitle', parent=styles['Normal'], fontSize=12, spaceAfter=6, alignment=TA_CENTER, textColor=HexColor('#546e7a'))
    head_s = ParagraphStyle('Heading', parent=styles['Heading2'], fontSize=14, spaceAfter=12, spaceBefore=15, textColor=MEDIUM_BLUE, fontName='Helvetica-Bold')
    bullet_s = ParagraphStyle('Bullet', parent=styles['Normal'], fontSize=10, spaceAfter=4, textColor=TEXT_DARK)
    footer_s = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, alignment=TA_CENTER, textColor=colors.grey)
    
    final_base = df_base.iloc[-1]
    breakeven_text = "Month {int(breakeven_base)}" if pd.notna(breakeven_base) else "Not achieved"
    
    elems = []
    elems.append(HRFlowable(width="100%", thickness=3, color=HexColor('#0d1b3e'), spaceAfter=15))
    elems.append(Paragraph("SaaS Financial Report", title_s))
    elems.append(Paragraph(f"<b>{scenario_name}</b>", subtitle_s))
    elems.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y')} | {simulation_months}-Month Forecast", subtitle_s))
    elems.append(HRFlowable(width="100%", thickness=1, color=HexColor('#bdc3c7'), spaceBefore=10, spaceAfter=20))
    
    # Key Highlights
    elems.append(Paragraph("Key Highlights at a Glance", head_s))
    highlights_data = [
        ["📊 Metric", "💰 Value"],
        ["Final MRR", f"${final_base['MRR']:,.0f}"],
        ["Final Customers", f"{int(final_base['Total_Customers']):,}"],
        ["LTV:CAC Ratio", f"{final_base['LTV_CAC_Ratio']:.2f}x"],
        ["Break-even Point", breakeven_text],
    ]
    highlights_t = Table(highlights_data, colWidths=[1.8*inch, 1.5*inch])
    highlights_t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), DARK_BLUE),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('LINEBELOW', (0, 0), (-1, 0), 2, MEDIUM_BLUE),
        ('LINEBELOW', (0, -1), (-1, -1), 1.5, MEDIUM_BLUE),
        ('LINEBEFORE', (1, 0), (1, -1), 1, HexColor('#90a4ae')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, HexColor('#f5f5f5')]),
        ('FONTNAME', (1, 1), (1, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (1, 1), (1, -1), HexColor('#1a237e')),
    ]))
    elems.append(highlights_t)
    elems.append(Spacer(1, 20))
    
    # Charts
    elems.append(Paragraph("Charts & Visual Analysis", head_s))
    chart_info = [
        ("Customer Growth", bytes_list[0], f"Shows the trajectory of customer acquisition over {simulation_months} months. Net customer growth is {int(final_base['Total_Customers'] - starting_customers):,} customers."),
        ("Monthly Recurring Revenue (MRR)", bytes_list[1], f"Revenue progression from ${df_base.iloc[0]['MRR']:,.0f} to ${final_base['MRR']:,.0f} - a {((final_base['MRR']/df_base.iloc[0]['MRR'])-1)*100:.0f}% increase."),
        ("Cumulative Cash Position", bytes_list[2], f"Tracks cash flow. Break-even achieved at {breakeven_text}. Final cash position: ${final_base['Cumulative_Cash']:,.0f}."),
        ("LTV:CAC Ratio Trend", bytes_list[3], f"Unit economics metric. Target is 3x. Final ratio: {final_base['LTV_CAC_Ratio']:.2f}x."),
    ]
    
    for title, img_bytes, caption in chart_info:
        elems.append(Paragraph(title, head_s))
        elems.append(Image(BytesIO(img_bytes), width=6.5*inch, height=3.5*inch))
        elems.append(Paragraph(caption, ParagraphStyle('Caption', parent=styles['Normal'], fontSize=9, spaceAfter=15, textColor=TEXT_DARK, alignment=TA_CENTER)))
        elems.append(Spacer(1, 10))
    
    elems.append(Spacer(1, 15))
    elems.append(HRFlowable(width="100%", thickness=3, color=DARK_BLUE, spaceAfter=10))
    elems.append(Paragraph("Generated by BahnSetu SaaS Financial Dashboard | Based on SaaS Financial Plan 2.0", footer_s))
    
    doc.build(elems)
    buf.seek(0)
    return buf.getvalue()


def generate_charts_only_pdf_report(df_base, scenario_name, simulation_months, starting_customers, breakeven_base, bytes_list):
    """Generate PDF report with charts only."""
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=0.5*inch, leftMargin=0.5*inch, topMargin=0.5*inch, bottomMargin=0.5*inch)
    styles = getSampleStyleSheet()
    
    DARK_BLUE = HexColor('#1a237e')
    MEDIUM_BLUE = HexColor('#0277bd')
    TEXT_DARK = HexColor('#263238')
    
    title_s = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=24, spaceAfter=8, alignment=TA_CENTER, textColor=DARK_BLUE, fontName='Helvetica-Bold')
    subtitle_s = ParagraphStyle('Subtitle', parent=styles['Normal'], fontSize=12, spaceAfter=6, alignment=TA_CENTER, textColor=HexColor('#546e7a'))
    head_s = ParagraphStyle('Heading', parent=styles['Heading2'], fontSize=14, spaceAfter=12, spaceBefore=15, textColor=MEDIUM_BLUE, fontName='Helvetica-Bold')
    caption_s = ParagraphStyle('Caption', parent=styles['Normal'], fontSize=9, spaceAfter=15, textColor=TEXT_DARK, alignment=TA_CENTER)
    footer_s = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, alignment=TA_CENTER, textColor=colors.grey)
    
    final_base = df_base.iloc[-1]
    breakeven_text = "Month {int(breakeven_base)}" if pd.notna(breakeven_base) else "Not achieved"
    
    elems = []
    elems.append(HRFlowable(width="100%", thickness=3, color=HexColor('#0d1b3e'), spaceAfter=15))
    elems.append(Paragraph("Charts & Visual Analysis", title_s))
    elems.append(Paragraph(f"<b>{scenario_name}</b>", subtitle_s))
    elems.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y')} | {simulation_months}-Month Forecast", subtitle_s))
    elems.append(HRFlowable(width="100%", thickness=1, color=HexColor('#bdc3c7'), spaceBefore=10, spaceAfter=20))
    
    # Key Highlights
    elems.append(Paragraph("Key Highlights at a Glance", head_s))
    highlights_data = [
        ["📊 Metric", "💰 Value"],
        ["Final MRR", f"${final_base['MRR']:,.0f}"],
        ["Final Customers", f"{int(final_base['Total_Customers']):,}"],
        ["LTV:CAC Ratio", f"{final_base['LTV_CAC_Ratio']:.2f}x"],
        ["Break-even Point", breakeven_text],
    ]
    highlights_t = Table(highlights_data, colWidths=[1.8*inch, 1.5*inch])
    highlights_t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), DARK_BLUE),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('LINEBELOW', (0, 0), (-1, 0), 2, MEDIUM_BLUE),
        ('LINEBELOW', (0, -1), (-1, -1), 1.5, MEDIUM_BLUE),
        ('LINEBEFORE', (1, 0), (1, -1), 1, HexColor('#90a4ae')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, HexColor('#f5f5f5')]),
        ('FONTNAME', (1, 1), (1, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (1, 1), (1, -1), HexColor('#1a237e')),
    ]))
    elems.append(highlights_t)
    elems.append(Spacer(1, 20))
    
    # Charts only
    chart_info = [
        ("Customer Growth", bytes_list[0], f"Shows the trajectory of customer acquisition over {simulation_months} months. Net customer growth is {int(final_base['Total_Customers'] - starting_customers):,} customers."),
        ("Monthly Recurring Revenue (MRR)", bytes_list[1], f"Revenue progression from ${df_base.iloc[0]['MRR']:,.0f} to ${final_base['MRR']:,.0f} - a {((final_base['MRR']/df_base.iloc[0]['MRR'])-1)*100:.0f}% increase."),
        ("Cumulative Cash Position", bytes_list[2], f"Tracks cash flow. Break-even achieved at {breakeven_text}. Final cash position: ${final_base['Cumulative_Cash']:,.0f}."),
        ("LTV:CAC Ratio Trend", bytes_list[3], f"Unit economics metric. Target is 3x. Final ratio: {final_base['LTV_CAC_Ratio']:.2f}x."),
    ]
    
    for title, img_bytes, caption in chart_info:
        elems.append(Paragraph(title, head_s))
        elems.append(Image(BytesIO(img_bytes), width=6.5*inch, height=3.5*inch))
        elems.append(Paragraph(caption, caption_s))
        elems.append(Spacer(1, 10))
    
    elems.append(Spacer(1, 15))
    elems.append(HRFlowable(width="100%", thickness=3, color=DARK_BLUE, spaceAfter=10))
    elems.append(Paragraph("Generated by BahnSetu SaaS Financial Dashboard | Based on SaaS Financial Plan 2.0", footer_s))
    
    doc.build(elems)
    buf.seek(0)
    return buf.getvalue()


def generate_tables_only_pdf_report(df_base, scenario_name, simulation_months, starting_customers):
    """Generate PDF report with data tables only."""
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, rightMargin=0.4*inch, leftMargin=0.4*inch, topMargin=0.4*inch, bottomMargin=0.4*inch)
    styles = getSampleStyleSheet()
    
    DARK_BLUE = HexColor('#1a237e')
    MEDIUM_BLUE = HexColor('#0277bd')
    LIGHT_BLUE = HexColor('#e3f2fd')
    ROW_ALT = HexColor('#f5f5f5')
    ROW_WHITE = colors.white
    BORDER = HexColor('#90a4ae')
    TEXT_DARK = HexColor('#263238')
    TEXT_BOLD = HexColor('#1a237e')
    
    title_s = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=24, spaceAfter=8, alignment=TA_CENTER, textColor=DARK_BLUE, fontName='Helvetica-Bold')
    subtitle_s = ParagraphStyle('Subtitle', parent=styles['Normal'], fontSize=12, spaceAfter=6, alignment=TA_CENTER, textColor=HexColor('#546e7a'))
    head_s = ParagraphStyle('Heading', parent=styles['Heading2'], fontSize=14, spaceAfter=12, spaceBefore=15, textColor=MEDIUM_BLUE, fontName='Helvetica-Bold')
    footer_s = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, alignment=TA_CENTER, textColor=colors.grey)
    
    final_base = df_base.iloc[-1]
    
    elems = []
    elems.append(HRFlowable(width="100%", thickness=3, color=DARK_BLUE, spaceAfter=15))
    elems.append(Paragraph("Data Tables Report", title_s))
    elems.append(Paragraph(f"<b>{scenario_name}</b>", subtitle_s))
    elems.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y')} | {simulation_months}-Month Simulation", subtitle_s))
    elems.append(HRFlowable(width="100%", thickness=1, color=BORDER, spaceBefore=10, spaceAfter=15))
    
    # Monthly Financial Summary
    elems.append(Paragraph("Monthly Financial Summary", head_s))
    monthly_data = [["📅 Month", "👥 Customers", "➕ New", "➖ Churned", "💵 MRR", "💰 Revenue", "📊 Costs", "📈 P&L", "💳 Cash"]]
    for _, row in df_base.iterrows():
        monthly_data.append([
            f"M{int(row['Month']):02d}",
            f"{int(row['Total_Customers']):,}",
            f"+{int(row['New_Customers'])}",
            f"-{int(row['Churned_Customers'])}",
            f"${row['MRR']:,.0f}",
            f"${row['Total_Revenue']:,.0f}",
            f"${row['Total_Costs']:,.0f}",
            f"${row['Profit_Loss']:,.0f}",
            f"${row['Cumulative_Cash']:,.0f}",
        ])
    monthly_t = Table(monthly_data, colWidths=[0.55*inch, 0.7*inch, 0.5*inch, 0.55*inch, 0.7*inch, 0.7*inch, 0.7*inch, 0.65*inch, 0.75*inch])
    monthly_t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), DARK_BLUE),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('LINEBELOW', (0, 0), (-1, 0), 2, MEDIUM_BLUE),
        ('LINEBELOW', (0, -1), (-1, -1), 1.5, MEDIUM_BLUE),
        ('LINEBEFORE', (1, 0), (1, -1), 0.5, BORDER),
        ('LINEBEFORE', (2, 0), (2, -1), 0.5, BORDER),
        ('LINEBEFORE', (3, 0), (3, -1), 0.5, BORDER),
        ('LINEBEFORE', (4, 0), (4, -1), 0.5, BORDER),
        ('LINEBEFORE', (5, 0), (5, -1), 0.5, BORDER),
        ('LINEBEFORE', (6, 0), (6, -1), 0.5, BORDER),
        ('LINEBEFORE', (7, 0), (7, -1), 0.5, BORDER),
        ('LINEBEFORE', (8, 0), (8, -1), 0.5, BORDER),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [ROW_WHITE, ROW_ALT]),
    ]))
    elems.append(monthly_t)
    elems.append(Spacer(1, 15))
    
    # Key Metrics by Month
    elems.append(Paragraph("Key Metrics by Month", head_s))
    metrics_data = [["📅 Month", "📊 Gross Margin", "💎 LTV:CAC", "⏱️ CAC Payback", "📈 MoM Growth"]]
    for _, row in df_base.iterrows():
        metrics_data.append([
            f"M{int(row['Month']):02d}",
            f"{row['Gross_Margin_%']:.1f}%",
            f"{row['LTV_CAC_Ratio']:.2f}x",
            f"{row.get('CAC_Payback_Pro', 0):.1f} mo",
            f"{row['MoM_Growth_%']:.1f}%",
        ])
    metrics_t = Table(metrics_data, colWidths=[0.65*inch, 1.05*inch, 0.95*inch, 1.05*inch, 0.95*inch])
    metrics_t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), MEDIUM_BLUE),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('LINEBELOW', (0, 0), (-1, 0), 2, DARK_BLUE),
        ('LINEBELOW', (0, -1), (-1, -1), 1.5, DARK_BLUE),
        ('LINEBEFORE', (1, 0), (1, -1), 0.5, BORDER),
        ('LINEBEFORE', (2, 0), (2, -1), 0.5, BORDER),
        ('LINEBEFORE', (3, 0), (3, -1), 0.5, BORDER),
        ('LINEBEFORE', (4, 0), (4, -1), 0.5, BORDER),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [ROW_WHITE, ROW_ALT]),
    ]))
    elems.append(metrics_t)
    
    elems.append(Spacer(1, 15))
    
    # Departmental Costs
    elems.append(Paragraph("Departmental Costs", head_s))
    dept_data = [["📅 Month", "🏭 COGS", "🔬 R&D", "📣 Sales & Mktg", "📋 G&A", "🤝 Customer Success"]]
    for _, row in df_base.iterrows():
        dept_data.append([
            f"M{int(row['Month']):02d}",
            f"${row['COGS']:,.0f}",
            f"${row['RD_Cost']:,.0f}",
            f"${row['SM_Cost']:,.0f}",
            f"${row['GA_Cost']:,.0f}",
            f"${row['CS_Cost']:,.0f}",
        ])
    dept_t = Table(dept_data, colWidths=[0.55*inch, 0.85*inch, 0.85*inch, 0.95*inch, 0.85*inch, 1.0*inch])
    dept_t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), TEXT_BOLD),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('LINEBELOW', (0, 0), (-1, 0), 2, MEDIUM_BLUE),
        ('LINEBELOW', (0, -1), (-1, -1), 1.5, MEDIUM_BLUE),
        ('LINEBEFORE', (1, 0), (1, -1), 0.5, BORDER),
        ('LINEBEFORE', (2, 0), (2, -1), 0.5, BORDER),
        ('LINEBEFORE', (3, 0), (3, -1), 0.5, BORDER),
        ('LINEBEFORE', (4, 0), (4, -1), 0.5, BORDER),
        ('LINEBEFORE', (5, 0), (5, -1), 0.5, BORDER),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [ROW_WHITE, ROW_ALT]),
    ]))
    elems.append(dept_t)
    
    elems.append(Spacer(1, 15))
    elems.append(HRFlowable(width="100%", thickness=3, color=DARK_BLUE, spaceAfter=10))
    elems.append(Paragraph("Generated by BahnSetu SaaS Financial Dashboard | Based on SaaS Financial Plan 2.0", footer_s))
    
    doc.build(elems)
    buf.seek(0)
    return buf.getvalue()
