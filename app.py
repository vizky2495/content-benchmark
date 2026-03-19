import streamlit as st
import json
import re
import os
import psycopg2
import psycopg2.extras

DATABASE_URL = os.environ.get("DATABASE_URL")

PRODUCT_MAP = {
    "CL_INT": "Intacct",
    "CL_S50": "Sage 50",
    "CL_BMS": "Sage Business Management",
    "CL_CRE": "Sage CRE",
    "CL_ACS": "Sage Accountant Solutions",
    "CL_FAS": "Sage Fixed Assets",
    "CL_COPILOT": "Sage Copilot",
}

REGION_MAP = {
    "US": "United States",
}

SEGMENT_MAP = {
    "MED": "Medium",
    "SMB": "Small Business",
    "SMA": "Small",
    "ENT": "Enterprise",
}

ACTION_MAP = {
    "TOO": "Product Tour",
    "DLE": "Download E-book",
    "TTE": "Talk to Expert",
    "DEM": "Request Demo",
    "WBR": "Webinar",
    "PDF": "Content Download",
    "CON": "Contact",
    "TRL": "Trial",
    "VID": "Video",
    "QUO": "Quote",
    "WEB": "Webinar",
    "LGO": "Lead Gen Offer",
    "HPFS": "High Performance Series",
    "EBK": "E-book",
}

FUNNEL_MAP = {
    "TOFU": "TOF",
    "MOFU": "MOF",
    "BOFU": "BOF",
}

FUNNEL_STAGES = ["TOF", "MOF", "BOF"]
PERFORMANCE_TIERS = ["High", "Medium", "Low"]
WHY_IT_WORKED_OPTIONS = [
    "Clear pain-point alignment",
    "Strong proof or case study",
    "High-intent CTA",
]

AUDIENCE_OPTIONS = [
    "CFO / Finance Leader",
    "Controller / Accounting",
    "Executive / Leadership",
    "IT / Systems",
    "Nonprofit Operator",
    "Accountant / Partner",
    "General Finance",
]

COPY_ANGLE_OPTIONS = [
    "Efficiency / Time Savings",
    "Financial Visibility / Reporting",
    "Growth / Scaling",
    "Compliance / Risk",
    "Automation",
    "AI / Innovation",
    "Industry-Specific Challenges",
    "Cost Reduction",
    "General ERP Overview",
    "Hand Raiser",
]

ASSET_TYPE_OPTIONS = [
    "Guide",
    "E-book",
    "Whitepaper",
    "Case Study",
    "Product Tour",
    "Demo",
    "Pricing Page",
    "Webinar",
    "Video",
    "Checklist",
    "Landing Page",
]

CONTENT_INPUT_TYPES = ["Upload File", "Paste Link", "Paste Text"]


def get_conn():
    return psycopg2.connect(DATABASE_URL)


def slug_to_name(slug):
    parts = re.sub(r'([a-z])([A-Z])', r'\1 \2', slug)
    parts = re.sub(r'([A-Za-z])(\d)', r'\1 \2', parts)
    parts = re.sub(r'(\d)([A-Za-z])', r'\1 \2', parts)
    words = parts.replace("_", " ").replace("-", " ").split()
    titled = []
    for w in words:
        if w.isupper() and len(w) >= 2:
            titled.append(w)
        else:
            titled.append(w.capitalize())
    return " ".join(titled)


def parse_asset(filename):
    raw = filename.strip()
    parts = raw.split("_")
    notes_parts = []

    product_code = None
    product = None
    region_code = None
    region = None
    segment_code = None
    segment = None
    action_code = None
    action_type = None
    funnel_code = None
    funnel_stage = None
    asset_name_slug = None

    if len(parts) >= 2:
        candidate = f"{parts[0]}_{parts[1]}"
        if candidate.upper() in PRODUCT_MAP:
            product_code = candidate.upper()
            product = PRODUCT_MAP[product_code]
        else:
            product_code = candidate.upper()
            product = candidate.upper()
            notes_parts.append("Unknown code")

    if len(parts) >= 3:
        code = parts[2].upper()
        if code in REGION_MAP:
            region_code = code
            region = REGION_MAP[code]
        else:
            region_code = code
            region = code
            notes_parts.append("Unknown code")

    if len(parts) >= 4:
        code = parts[3].upper()
        if code in SEGMENT_MAP:
            segment_code = code
            segment = SEGMENT_MAP[code]
        else:
            segment_code = code
            segment = code
            notes_parts.append("Unknown code")

    if len(parts) >= 5:
        code = parts[4].upper()
        if code in ACTION_MAP:
            action_code = code
            action_type = ACTION_MAP[code]
        else:
            action_code = code
            action_type = code
            notes_parts.append("Unknown code")

    if len(parts) >= 6:
        code = parts[5].upper()
        if code in FUNNEL_MAP:
            funnel_code = code
            funnel_stage = FUNNEL_MAP[code]
        else:
            funnel_code = code
            funnel_stage = code
            notes_parts.append("Unknown code")

    if len(parts) >= 7:
        asset_name_slug = "_".join(parts[6:])
    else:
        asset_name_slug = ""
        notes_parts.append("Missing asset name in filename")

    asset_name = slug_to_name(asset_name_slug) if asset_name_slug else ""

    notes = "Unknown code" if notes_parts else ""

    return {
        "asset_id": raw,
        "product": product,
        "region": region,
        "segment": segment,
        "action_type": action_type,
        "funnel_stage": funnel_stage,
        "asset_name": asset_name,
        "performance_tier": None,
        "why_it_worked": [],
        "notes": notes,
    }


def save_asset(asset):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO assets (asset_id, asset_name, product, region, segment, action_type,
                                    funnel_stage, performance_tier, why_it_worked, notes,
                                    total_page_views, total_downloads, on_sage_com,
                                    audience, copy_angle, asset_type)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                asset.get("asset_id"), asset.get("asset_name"), asset.get("product"),
                asset.get("region"), asset.get("segment"), asset.get("action_type"),
                asset.get("funnel_stage"), asset.get("performance_tier"),
                asset.get("why_it_worked", []) or [], asset.get("notes") or "",
                asset.get("total_page_views", 0), asset.get("total_downloads", 0),
                asset.get("on_sage_com", False),
                asset.get("audience"), asset.get("copy_angle"), asset.get("asset_type"),
            ))
            new_id = cur.fetchone()[0]
            conn.commit()
            return new_id
    finally:
        conn.close()


def update_asset(asset_id_db, updates):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE assets
                SET asset_name = %s, product = %s, region = %s, segment = %s,
                    action_type = %s, funnel_stage = %s,
                    performance_tier = %s, why_it_worked = %s,
                    notes = %s, on_sage_com = %s,
                    audience = %s, copy_angle = %s, asset_type = %s,
                    updated_at = NOW()
                WHERE id = %s
            """, (
                updates.get("asset_name"), updates.get("product"),
                updates.get("region"), updates.get("segment"),
                updates.get("action_type"), updates.get("funnel_stage"),
                updates.get("performance_tier"), updates.get("why_it_worked", []) or [],
                updates.get("notes") or "", updates.get("on_sage_com", False),
                updates.get("audience"), updates.get("copy_angle"), updates.get("asset_type"),
                asset_id_db,
            ))
            conn.commit()
    finally:
        conn.close()


def delete_asset(asset_id_db):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM assets WHERE id = %s", (asset_id_db,))
            conn.commit()
    finally:
        conn.close()


def load_assets():
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM assets ORDER BY created_at DESC")
            rows = cur.fetchall()
            return [dict(r) for r in rows]
    finally:
        conn.close()


def check_duplicate(asset_id_str):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM assets WHERE asset_id = %s", (asset_id_str,))
            return cur.fetchone() is not None
    finally:
        conn.close()


def save_content_item(item):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO content_items (asset_db_id, file_name, file_type, file_path,
                    content_type, link_url, text_content,
                    primary_cta_type, cta_placement, cta_clarity,
                    stated_audience, primary_pain_point,
                    proof_types_present, proof_strength,
                    format_type, skimmability, length_proxy,
                    differentiated_angle, competitive_comparison)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                item.get("asset_db_id"), item.get("file_name"), item.get("file_type"),
                item.get("file_path"),
                item.get("content_type", "file"), item.get("link_url"), item.get("text_content"),
                item.get("primary_cta_type"), item.get("cta_placement"), item.get("cta_clarity"),
                item.get("stated_audience"), item.get("primary_pain_point"),
                item.get("proof_types_present"), item.get("proof_strength"),
                item.get("format_type"), item.get("skimmability"), item.get("length_proxy"),
                item.get("differentiated_angle"), item.get("competitive_comparison", False),
            ))
            new_id = cur.fetchone()[0]
            conn.commit()
            return new_id
    finally:
        conn.close()


def load_content_items(asset_db_id=None):
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            if asset_db_id:
                cur.execute("SELECT * FROM content_items WHERE asset_db_id = %s ORDER BY created_at DESC", (asset_db_id,))
            else:
                cur.execute("SELECT * FROM content_items ORDER BY created_at DESC")
            return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


def delete_content_item(content_id):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM content_items WHERE id = %s", (content_id,))
            conn.commit()
    finally:
        conn.close()


def load_content_with_assets():
    conn = get_conn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT c.*, a.asset_name, a.asset_id AS asset_id_str, a.product, a.region,
                       a.segment, a.action_type, a.funnel_stage, a.performance_tier,
                       a.total_page_views, a.total_downloads, a.on_sage_com
                FROM content_items c
                JOIN assets a ON c.asset_db_id = a.id
                ORDER BY a.performance_tier, a.funnel_stage, c.created_at DESC
            """)
            return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


CTA_TYPES = ["Request Demo", "Free Trial", "Contact Sales", "Download", "Watch Video",
             "Learn More", "Get Quote", "Sign Up", "Talk to Expert", "Register"]
CTA_PLACEMENTS = ["Top", "Mid", "End"]
CTA_CLARITY_OPTIONS = ["Clear", "Vague"]
PROOF_TYPES = ["Numbers", "Case Study", "Testimonial", "Screenshots", "None"]
PROOF_STRENGTHS = ["Strong", "Medium", "Weak"]
FORMAT_TYPES = ["PDF", "Video", "E-book", "Landing Page", "Webinar", "Infographic", "White Paper", "Blog Post"]
SKIMMABILITY_OPTIONS = ["High", "Medium", "Low"]


st.set_page_config(page_title="Content Benchmark", layout="wide")

DARK_CSS = """
<style>
/* ── Global ── */
[data-testid="stAppViewContainer"] { background-color: #1a1a2e; }
[data-testid="stHeader"] { background-color: #1a1a2e; }
[data-testid="stSidebar"] { background-color: #16213e; }
.main .block-container { padding-top: 2rem; max-width: 1400px; }

/* ── Typography ── */
h1, h2, h3 { color: #e0e0e0 !important; font-weight: 600 !important; letter-spacing: -0.02em; }
h1 { font-size: 2rem !important; }
h2 { font-size: 1.5rem !important; }
h3 { font-size: 1.2rem !important; }
p, span, label, .stMarkdown { color: #c0c0c0; }

/* ── Tabs ── */
[data-testid="stTabs"] button { color: #a0a0a0 !important; font-size: 1rem !important; font-weight: 500 !important; padding: 0.6rem 1.2rem !important; border-radius: 8px 8px 0 0 !important; }
[data-testid="stTabs"] button[aria-selected="true"] { color: #00C853 !important; border-bottom: 3px solid #00C853 !important; background-color: rgba(0,200,83,0.08) !important; }

/* ── Cards ── */
.sage-card { background: #1f2937; border-radius: 12px; padding: 1.5rem; margin-bottom: 1rem; border: 1px solid #374151; }
.sage-card-accent { background: #1f2937; border-radius: 12px; padding: 1.5rem; margin-bottom: 1rem; border-left: 4px solid #00C853; border-top: 1px solid #374151; border-right: 1px solid #374151; border-bottom: 1px solid #374151; }

/* ── KPI Cards ── */
.kpi-card { background: #1f2937; border-radius: 12px; padding: 1.2rem; text-align: center; border: 1px solid #374151; }
.kpi-value { font-size: 2rem; font-weight: 700; color: #00C853; margin: 0; }
.kpi-label { font-size: 0.85rem; color: #9ca3af; margin: 0; text-transform: uppercase; letter-spacing: 0.05em; }

/* ── Tier KPI Cards ── */
.tier-kpi-high { background: #1f2937; border-radius: 12px; padding: 1.2rem; text-align: center; border: 1px solid #374151; border-top: 3px solid #00C853; }
.tier-kpi-med { background: #1f2937; border-radius: 12px; padding: 1.2rem; text-align: center; border: 1px solid #374151; border-top: 3px solid #F59E0B; }
.tier-kpi-low { background: #1f2937; border-radius: 12px; padding: 1.2rem; text-align: center; border: 1px solid #374151; border-top: 3px solid #EF4444; }
.tier-kpi-unrated { background: #1f2937; border-radius: 12px; padding: 1.2rem; text-align: center; border: 1px solid #374151; border-top: 3px solid #6B7280; }

/* ── Badges ── */
.badge { display: inline-block; padding: 0.2rem 0.7rem; border-radius: 99px; font-size: 0.75rem; font-weight: 600; margin-right: 0.4rem; }
.badge-tof { background: #064e3b; color: #6ee7b7; }
.badge-mof { background: #1e3a5f; color: #93c5fd; }
.badge-bof { background: #4c1d95; color: #c4b5fd; }
.badge-high { background: #064e3b; color: #6ee7b7; }
.badge-medium { background: #78350f; color: #fcd34d; }
.badge-low { background: #7f1d1d; color: #fca5a5; }
.badge-unrated { background: #374151; color: #9ca3af; }

/* ── Insight Strip ── */
.insight-strip { background: linear-gradient(135deg, #064e3b 0%, #1a1a2e 100%); border-radius: 12px; padding: 1.2rem 1.5rem; margin-bottom: 1.5rem; border: 1px solid #065f46; }
.insight-strip p { color: #a7f3d0 !important; font-size: 0.95rem; margin: 0.3rem 0; }

/* ── Inputs ── */
[data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea { background-color: #111827 !important; color: #e0e0e0 !important; border: 1px solid #374151 !important; border-radius: 8px !important; }
[data-testid="stTextInput"] input:focus, [data-testid="stTextArea"] textarea:focus { border-color: #00C853 !important; box-shadow: 0 0 0 2px rgba(0,200,83,0.2) !important; }
[data-testid="stSelectbox"] > div > div { background-color: #111827 !important; border: 1px solid #374151 !important; border-radius: 8px !important; }

/* ── Buttons ── */
[data-testid="stBaseButton-primary"] { background-color: #00C853 !important; color: #000 !important; border-radius: 8px !important; font-weight: 600 !important; border: none !important; }
[data-testid="stBaseButton-primary"]:hover { background-color: #00E676 !important; }
[data-testid="stBaseButton-secondary"] { background-color: #374151 !important; color: #e0e0e0 !important; border-radius: 8px !important; border: 1px solid #4B5563 !important; }

/* ── Expanders ── */
div[data-testid="stExpander"] { background-color: #1f2937; border: 1px solid #374151; border-radius: 10px; border-left: 3px solid #00C853; margin-bottom: 0.5rem; }
div[data-testid="stExpander"] summary { color: #e0e0e0 !important; font-weight: 500; }

/* ── Metrics ── */
[data-testid="stMetric"] { background: #1f2937; border-radius: 10px; padding: 1rem; border: 1px solid #374151; }
[data-testid="stMetricValue"] { color: #00C853 !important; font-size: 1.8rem !important; }
[data-testid="stMetricLabel"] { color: #9ca3af !important; text-transform: uppercase; font-size: 0.8rem !important; letter-spacing: 0.05em; }

/* ── Dataframes ── */
[data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; }

/* ── Comparison columns ── */
.cmp-col-header { font-size: 1.1rem; font-weight: 600; padding: 0.8rem; border-radius: 8px 8px 0 0; text-align: center; margin-bottom: 0.5rem; }
.cmp-col-high { background: #064e3b; color: #6ee7b7; }
.cmp-col-med { background: #78350f; color: #fcd34d; }
.cmp-col-low { background: #7f1d1d; color: #fca5a5; }

/* ── Even KPI grid ── */
.kpi-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; margin-bottom: 1rem; }
.kpi-grid-item { background: #1f2937; border-radius: 10px; padding: 0.9rem 0.6rem; text-align: center; border: 1px solid #374151; min-height: 80px; display: flex; flex-direction: column; justify-content: center; }
.kpi-grid-item .kpi-value { font-size: 1.6rem; font-weight: 700; color: #00C853; margin: 0; line-height: 1.2; }
.kpi-grid-item .kpi-label { font-size: 0.7rem; color: #9ca3af; margin: 0; text-transform: uppercase; letter-spacing: 0.05em; line-height: 1.3; }

/* ── Progress bars for breakdowns ── */
.breakdown-row { display: flex; align-items: center; margin: 0.4rem 0; }
.breakdown-label { width: 120px; font-size: 0.82rem; color: #d1d5db; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.breakdown-bar-bg { flex: 1; height: 20px; background: #374151; border-radius: 4px; overflow: hidden; margin: 0 0.5rem; }
.breakdown-bar { height: 100%; border-radius: 4px; }
.breakdown-bar-green { background: #00C853; }
.breakdown-bar-yellow { background: #F59E0B; }
.breakdown-bar-red { background: #EF4444; }
.breakdown-pct { width: 40px; font-size: 0.82rem; color: #9ca3af; text-align: right; }

/* ── Large audience bars ── */
.breakdown-row-lg { display: flex; align-items: center; margin: 0.5rem 0; }
.breakdown-row-lg .breakdown-label { width: 130px; font-size: 0.9rem; font-weight: 500; }
.breakdown-row-lg .breakdown-bar-bg { height: 26px; }
.breakdown-row-lg .breakdown-pct { font-size: 0.9rem; font-weight: 600; }

/* ── Small secondary bars ── */
.breakdown-row-sm { display: flex; align-items: center; margin: 0.3rem 0; }
.breakdown-row-sm .breakdown-label { width: 110px; font-size: 0.75rem; }
.breakdown-row-sm .breakdown-bar-bg { height: 14px; }
.breakdown-row-sm .breakdown-pct { font-size: 0.75rem; width: 35px; }

/* ── Compact asset list ── */
.compact-asset { background: #111827; border-radius: 6px; padding: 0.4rem 0.7rem; margin: 0.25rem 0; border: 1px solid #1f2937; display: flex; align-items: center; justify-content: space-between; }
.compact-asset-name { font-size: 0.78rem; color: #9ca3af; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 70%; }
.compact-asset-badge { font-size: 0.65rem; }

/* ── Sticky insight panel ── */
.sticky-panel { position: sticky; top: 3.5rem; max-height: calc(100vh - 5rem); overflow-y: auto; }
.sticky-panel::-webkit-scrollbar { width: 4px; }
.sticky-panel::-webkit-scrollbar-thumb { background: #374151; border-radius: 4px; }
.insight-panel { background: #111827; border-radius: 12px; padding: 1.2rem; border: 1px solid #374151; }
.insight-bullet { color: #d1d5db; font-size: 0.88rem; margin: 0.7rem 0; padding-left: 0.3rem; border-left: 2px solid #00C853; padding-left: 0.8rem; line-height: 1.5; }
.section-divider { border: none; border-top: 1px solid #2a2a3e; margin: 1rem 0; }

/* ── Decision panel ── */
.decision-fix { background: #1e3a5f; border-radius: 10px; padding: 1rem; border: 1px solid #2563eb; margin: 0.5rem 0; }
.decision-retire { background: #3b1325; border-radius: 10px; padding: 1rem; border: 1px solid #9f1239; margin: 0.5rem 0; }
.decision-keep { background: #1f2937; border-radius: 10px; padding: 1rem; border: 1px solid #4B5563; margin: 0.5rem 0; }

/* ── Radio horizontal ── */
[data-testid="stRadio"] > div { gap: 0.5rem; }

/* ── Dividers ── */
hr { border-color: #374151 !important; }
</style>
"""
st.markdown(DARK_CSS, unsafe_allow_html=True)

def render_badge(text, badge_type=""):
    type_map = {
        "TOF": "badge-tof", "MOF": "badge-mof", "BOF": "badge-bof",
        "High": "badge-high", "Medium": "badge-medium", "Low": "badge-low", "Unrated": "badge-unrated",
    }
    css_class = type_map.get(text, badge_type or "badge-unrated")
    return f'<span class="badge {css_class}">{text}</span>'

def render_kpi(value, label, card_class="kpi-card"):
    return f'<div class="{card_class}"><p class="kpi-value">{value}</p><p class="kpi-label">{label}</p></div>'

def render_breakdown_bars(freq_data, total, bar_color="breakdown-bar-green", size="md"):
    row_class = {"lg": "breakdown-row-lg", "sm": "breakdown-row-sm"}.get(size, "breakdown-row")
    limit = 6 if size == "lg" else 5
    html = ""
    for val, count in freq_data[:limit]:
        pct = round(count / total * 100) if total > 0 else 0
        html += f'''<div class="{row_class}">
            <span class="breakdown-label" title="{val}">{val}</span>
            <div class="breakdown-bar-bg"><div class="breakdown-bar {bar_color}" style="width:{pct}%"></div></div>
            <span class="breakdown-pct">{pct}%</span>
        </div>'''
    return html

st.markdown('<h1 style="margin-bottom:0;">Content Benchmark</h1>', unsafe_allow_html=True)
st.markdown('<p style="color:#6B7280;margin-top:0.2rem;margin-bottom:1.5rem;">Sage content performance library</p>', unsafe_allow_html=True)

tab_library, tab_add_content, tab_compare, tab_unrated, tab_import, tab_export = st.tabs(["Library", "Add Asset & Content", "Comparison", "Unrated", "Import & Parse", "Export"])

with tab_library:
    all_assets = load_assets()

    search_query = st.text_input("Search by asset name", placeholder="Type an asset name to search...", key="search_bar")

    col_f1, col_f2, col_f3, col_f4, col_f5 = st.columns(5)
    with col_f1:
        filter_funnel = st.selectbox("Funnel Stage", ["All"] + FUNNEL_STAGES, key="filter_funnel")
    with col_f2:
        all_types = sorted(set(a.get("action_type") or "" for a in all_assets if a.get("action_type")))
        filter_type = st.selectbox("Action Type", ["All"] + all_types, key="filter_type")
    with col_f3:
        all_segments = sorted(set(a.get("segment") or "" for a in all_assets if a.get("segment")))
        filter_segment = st.selectbox("Segment", ["All"] + all_segments, key="filter_segment")
    with col_f4:
        all_products = sorted(set(a.get("product") or "" for a in all_assets if a.get("product")))
        filter_product = st.selectbox("Product", ["All"] + all_products, key="filter_product")
    with col_f5:
        filter_sage = st.selectbox("On Sage.com", ["All", "Yes", "No"], key="filter_sage")

    filtered = all_assets
    if search_query:
        q = search_query.lower()
        filtered = [a for a in filtered if q in (a.get("asset_name") or "").lower()]
    if filter_funnel != "All":
        filtered = [a for a in filtered if a.get("funnel_stage") == filter_funnel]
    if filter_type != "All":
        filtered = [a for a in filtered if a.get("action_type") == filter_type]
    if filter_segment != "All":
        filtered = [a for a in filtered if a.get("segment") == filter_segment]
    if filter_product != "All":
        filtered = [a for a in filtered if a.get("product") == filter_product]
    if filter_sage == "Yes":
        filtered = [a for a in filtered if a.get("on_sage_com")]
    elif filter_sage == "No":
        filtered = [a for a in filtered if not a.get("on_sage_com")]

    if not all_assets:
        st.info("No assets yet. Use the **Import & Parse** or **Add Asset** tabs to get started.")
    elif not filtered:
        st.warning("No assets match your filters.")
    else:
        tier_groups = {"High": [], "Medium": [], "Low": [], "Unrated": []}
        for a in filtered:
            t = a.get("performance_tier") or "Unrated"
            if t not in tier_groups:
                t = "Unrated"
            tier_groups[t].append(a)

        high_count = len(tier_groups["High"])
        med_count = len(tier_groups["Medium"])
        low_count = len(tier_groups["Low"])
        unrated_count = len(tier_groups["Unrated"])

        active_tier = st.session_state.get("drill_tier", "All")

        tier_colors = {"High": "#00C853", "Medium": "#F59E0B", "Low": "#EF4444", "Unrated": "#6B7280"}
        tier_borders = {"High": "border-top:3px solid #00C853;", "Medium": "border-top:3px solid #F59E0B;", "Low": "border-top:3px solid #EF4444;", "Unrated": "border-top:3px solid #6B7280;"}
        tier_labels = {"High": "High Performers", "Medium": "Medium Performers", "Low": "Low Performers", "Unrated": "Unrated"}
        tier_counts = {"High": high_count, "Medium": med_count, "Low": low_count, "Unrated": unrated_count}

        tile_html = '<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:0.75rem;margin-bottom:1rem;">'
        for tn in ["High", "Medium", "Low", "Unrated"]:
            is_active = active_tier == tn
            active_ring = f"box-shadow:0 0 0 2px {tier_colors[tn]};" if is_active else ""
            tile_html += f'''<div style="background:#1f2937;border-radius:12px;padding:1.2rem;text-align:center;
                border:1px solid #374151;{tier_borders[tn]}{active_ring}min-height:100px;display:flex;flex-direction:column;justify-content:center;">
                <p style="font-size:2rem;font-weight:700;color:{tier_colors[tn]};margin:0;line-height:1.2;">{tier_counts[tn]}</p>
                <p style="font-size:0.8rem;color:#9ca3af;margin:0;text-transform:uppercase;letter-spacing:0.05em;">{tier_labels[tn]}</p>
            </div>'''
        tile_html += '</div>'
        st.markdown(tile_html, unsafe_allow_html=True)

        bc1, bc2, bc3, bc4, bc5 = st.columns(5)
        with bc1:
            if st.button("View High", key="drill_high", use_container_width=True, type="primary" if active_tier == "High" else "secondary"):
                st.session_state["drill_tier"] = "High"
                st.rerun()
        with bc2:
            if st.button("View Medium", key="drill_med", use_container_width=True, type="primary" if active_tier == "Medium" else "secondary"):
                st.session_state["drill_tier"] = "Medium"
                st.rerun()
        with bc3:
            if st.button("View Low", key="drill_low", use_container_width=True, type="primary" if active_tier == "Low" else "secondary"):
                st.session_state["drill_tier"] = "Low"
                st.rerun()
        with bc4:
            if st.button("View Unrated", key="drill_unrated", use_container_width=True, type="primary" if active_tier == "Unrated" else "secondary"):
                st.session_state["drill_tier"] = "Unrated"
                st.rerun()
        with bc5:
            if st.button("Show All", key="drill_all", use_container_width=True, type="primary" if active_tier == "All" else "secondary"):
                st.session_state["drill_tier"] = "All"
                st.rerun()

        if active_tier != "All":
            chip_color = tier_colors.get(active_tier, "#6B7280")
            chip_bg = {"High": "#064e3b", "Medium": "#78350f", "Low": "#7f1d1d", "Unrated": "#374151"}.get(active_tier, "#374151")
            st.markdown(f'''<div style="display:inline-flex;align-items:center;gap:0.4rem;margin:0.5rem 0 0.3rem;">
                <span style="background:{chip_bg};color:{chip_color};padding:0.25rem 0.8rem;border-radius:99px;font-size:0.82rem;font-weight:600;">
                    Filter: {active_tier}</span>
            </div>''', unsafe_allow_html=True)
            if st.button("Clear filter", key="clear_chip", type="secondary"):
                st.session_state["drill_tier"] = "All"
                st.rerun()

        if active_tier == "All":
            display_tiers = ["High", "Medium", "Low", "Unrated"]
            showing_count = len(filtered)
        else:
            display_tiers = [active_tier]
            showing_count = tier_counts.get(active_tier, 0)

        st.markdown(f'<p style="color:#6B7280;margin:0.5rem 0;">Showing {showing_count} of {len(all_assets)} assets</p>', unsafe_allow_html=True)

        st.markdown("---")

        for tier_name in display_tiers:
            group = tier_groups.get(tier_name, [])

            tier_icon = {"High": "🟢", "Medium": "🟡", "Low": "🔴", "Unrated": "⚪"}.get(tier_name, "⚪")
            tier_color = tier_colors.get(tier_name, "#6B7280")

            if not group:
                st.markdown(f'<div style="background:#1f2937;border-radius:10px;padding:1.2rem;border:1px solid #374151;border-left:3px solid {tier_color};margin-bottom:1rem;">'
                            f'<p style="color:#6B7280;margin:0;">{tier_icon} {tier_name} — No assets in this tier</p></div>', unsafe_allow_html=True)
                continue

            total_pv = sum(a.get("total_page_views") or 0 for a in group)
            total_dl = sum(a.get("total_downloads") or 0 for a in group)
            sage_count = sum(1 for a in group if a.get("on_sage_com"))
            funnel_breakdown = {}
            for a in group:
                fs = a.get("funnel_stage") or "Unknown"
                funnel_breakdown[fs] = funnel_breakdown.get(fs, 0) + 1
            funnel_str = " · ".join(f"{k}: {v}" for k, v in sorted(funnel_breakdown.items()))

            stats_html = f'''<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:0.5rem;margin-bottom:0.8rem;">
                <div class="kpi-grid-item"><p class="kpi-value" style="font-size:1.4rem;">{len(group)}</p><p class="kpi-label">Assets</p></div>
                <div class="kpi-grid-item"><p class="kpi-value" style="font-size:1.4rem;">{total_pv:,}</p><p class="kpi-label">Page Views</p></div>
                <div class="kpi-grid-item"><p class="kpi-value" style="font-size:1.4rem;">{total_dl:,}</p><p class="kpi-label">Downloads</p></div>
                <div class="kpi-grid-item"><p class="kpi-value" style="font-size:1.4rem;">{sage_count}</p><p class="kpi-label">On Sage.com</p></div>
            </div>'''

            st.markdown(f"### {tier_icon} {tier_name} Performers", unsafe_allow_html=True)
            st.markdown(stats_html, unsafe_allow_html=True)
            if funnel_str:
                st.markdown(f'<p style="color:#4B5563;font-size:0.78rem;margin-top:-0.5rem;margin-bottom:0.8rem;">Funnel: {funnel_str}</p>', unsafe_allow_html=True)

            with st.expander(f"Assets ({len(group)})", expanded=False):
                for asset in group:
                    sage_badge = " 🌐" if asset.get("on_sage_com") else ""
                    header = f"{tier_icon} {asset.get('asset_name') or asset.get('asset_id') or 'Untitled'}{sage_badge}"
                    with st.expander(header):
                        detail_col, edit_col = st.columns([1, 1])

                        with detail_col:
                            st.markdown("##### Asset Details")
                            st.markdown(f"**Asset ID:** `{asset.get('asset_id') or '—'}`")
                            st.markdown(f"**Product:** {asset.get('product') or '—'}")
                            st.markdown(f"**Region:** {asset.get('region') or '—'}")
                            st.markdown(f"**Segment:** {asset.get('segment') or '—'}")
                            st.markdown(f"**Action Type:** {asset.get('action_type') or '—'}")
                            st.markdown(f"**Funnel Stage:** {asset.get('funnel_stage') or '—'}")
                            st.markdown(f"**On Sage.com:** {'Yes' if asset.get('on_sage_com') else 'No'}")
                            st.markdown(f"**Audience:** {asset.get('audience') or '—'}")
                            st.markdown(f"**Copy Angle:** {asset.get('copy_angle') or '—'}")
                            st.markdown(f"**Asset Type:** {asset.get('asset_type') or '—'}")

                            pv = asset.get("total_page_views") or 0
                            dl = asset.get("total_downloads") or 0
                            if pv or dl:
                                st.markdown(f"**Page Views:** {pv:,} · **Downloads:** {dl:,}")

                            wiw = asset.get("why_it_worked") or []
                            if wiw and wiw[0]:
                                st.markdown(f"**Why It Worked:** {wiw[0]}")

                            if asset.get("notes"):
                                st.info(f"Notes: {asset['notes']}")

                        with edit_col:
                            st.markdown("##### Edit")
                            key_prefix = f"edit_{asset['id']}"

                            new_name = st.text_input("Asset Name", value=asset.get("asset_name") or "", key=f"{key_prefix}_name")

                            current_funnel = asset.get("funnel_stage") or ""
                            funnel_options = [""] + FUNNEL_STAGES
                            funnel_idx = funnel_options.index(current_funnel) if current_funnel in funnel_options else 0
                            new_funnel = st.selectbox("Funnel Stage", funnel_options, index=funnel_idx, key=f"{key_prefix}_funnel")

                            current_tier = asset.get("performance_tier") or ""
                            tier_options = [""] + PERFORMANCE_TIERS
                            tier_idx = tier_options.index(current_tier) if current_tier in tier_options else 0
                            new_tier = st.selectbox("Performance Tier", tier_options, index=tier_idx, key=f"{key_prefix}_tier")

                            current_wiw = (asset.get("why_it_worked") or [""])[0] if asset.get("why_it_worked") else ""
                            wiw_options = [""] + WHY_IT_WORKED_OPTIONS
                            wiw_idx = wiw_options.index(current_wiw) if current_wiw in wiw_options else 0
                            new_wiw = st.selectbox("Why It Worked", wiw_options, index=wiw_idx, key=f"{key_prefix}_wiw")

                            current_audience = asset.get("audience") or ""
                            aud_options = [""] + AUDIENCE_OPTIONS
                            aud_idx = aud_options.index(current_audience) if current_audience in aud_options else 0
                            new_audience = st.selectbox("Audience", aud_options, index=aud_idx, key=f"{key_prefix}_aud")

                            current_copy_angle = asset.get("copy_angle") or ""
                            ca_options = [""] + COPY_ANGLE_OPTIONS
                            ca_idx = ca_options.index(current_copy_angle) if current_copy_angle in ca_options else 0
                            new_copy_angle = st.selectbox("Copy Angle", ca_options, index=ca_idx, key=f"{key_prefix}_ca")

                            current_asset_type = asset.get("asset_type") or ""
                            at_options = [""] + ASSET_TYPE_OPTIONS
                            at_idx = at_options.index(current_asset_type) if current_asset_type in at_options else 0
                            new_asset_type = st.selectbox("Asset Type", at_options, index=at_idx, key=f"{key_prefix}_at")

                            new_sage = st.checkbox("On Sage.com", value=bool(asset.get("on_sage_com")), key=f"{key_prefix}_sage")

                            btn_col1, btn_col2 = st.columns(2)
                            with btn_col1:
                                if st.button("Save", key=f"{key_prefix}_save", type="primary", use_container_width=True):
                                    update_asset(asset["id"], {
                                        "asset_name": new_name or None,
                                        "product": asset.get("product"),
                                        "region": asset.get("region"),
                                        "segment": asset.get("segment"),
                                        "action_type": asset.get("action_type"),
                                        "funnel_stage": new_funnel or None,
                                        "performance_tier": new_tier or None,
                                        "why_it_worked": [new_wiw] if new_wiw else [],
                                        "notes": asset.get("notes"),
                                        "on_sage_com": new_sage,
                                        "audience": new_audience or None,
                                        "copy_angle": new_copy_angle or None,
                                        "asset_type": new_asset_type or None,
                                    })
                                    st.success("Saved!")
                                    st.rerun()

                            with btn_col2:
                                if st.button("Delete", key=f"{key_prefix}_del", use_container_width=True):
                                    delete_asset(asset["id"])
                                    st.rerun()


with tab_add_content:
    st.subheader("Add Asset & Upload Content")
    st.markdown("Add a new asset to the library and optionally upload content — all in one step.")

    st.markdown("#### Asset Information")
    add_name = st.text_input("Asset Name *", placeholder="Ceros Prod Tour", key="add_name")
    add_id = st.text_input("Asset ID (optional)", placeholder="CL_INT_US_MED_TOO_BOFU_CerosProdTour", key="add_id")

    col1, col2 = st.columns(2)
    with col1:
        product_options = list(PRODUCT_MAP.values())
        add_product = st.selectbox("Product", [""] + product_options, key="add_product")
        region_options = list(REGION_MAP.values())
        add_region = st.selectbox("Region", [""] + region_options, key="add_region")
        segment_options = list(SEGMENT_MAP.values())
        add_segment = st.selectbox("Segment", [""] + segment_options, key="add_segment")
    with col2:
        action_options = list(ACTION_MAP.values())
        add_action = st.selectbox("Action Type", [""] + action_options, key="add_action")
        add_funnel = st.selectbox("Funnel Stage", [""] + FUNNEL_STAGES, key="add_funnel")
        add_tier = st.selectbox("Performance Tier", [""] + PERFORMANCE_TIERS, key="add_tier")

    add_wiw = st.selectbox("Why It Worked", [""] + WHY_IT_WORKED_OPTIONS, key="add_wiw")
    add_sage = st.checkbox("On Sage.com", key="add_sage")
    add_notes = st.text_area("Notes (optional)", height=80, key="add_notes")

    st.markdown("---")
    st.markdown("#### Content Upload (optional)")
    st.caption("Add content by uploading a file, pasting a link, or pasting text. You can skip this section if you just want to add the asset.")

    add_content_type = st.radio("Content Input Type", ["None", "Upload File", "Paste Link", "Paste Text"], horizontal=True, key="add_content_radio")

    uploaded_file = None
    add_link_url = ""
    add_text_content = ""

    if add_content_type == "Upload File":
        uploaded_file = st.file_uploader("Upload Content File", type=["pdf", "ppt", "pptx", "doc", "docx", "png", "jpg", "jpeg", "gif", "svg"], key="add_file_upload")
    elif add_content_type == "Paste Link":
        add_link_url = st.text_input("Link URL", placeholder="e.g. https://youtube.com/watch?v=... or https://sage.com/landing-page", key="add_link_url")
    elif add_content_type == "Paste Text":
        add_text_content = st.text_area("Paste Content Text", placeholder="Paste body copy, transcript, email copy, etc.", height=200, key="add_text_content")

    cl_c1, cl_c2, cl_c3 = st.columns(3)
    with cl_c1:
        add_audience = st.selectbox("Audience", [""] + AUDIENCE_OPTIONS, key="add_audience")
    with cl_c2:
        add_copy_angle = st.selectbox("Copy Angle", [""] + COPY_ANGLE_OPTIONS, key="add_copy_angle")
    with cl_c3:
        add_asset_type = st.selectbox("Asset Type", [""] + ASSET_TYPE_OPTIONS, key="add_asset_type")

    cu_opt1, cu_opt2 = st.columns(2)
    with cu_opt1:
        cu_cta_type = st.selectbox("Primary CTA Type (optional)", [""] + CTA_TYPES, key="add_cta_type")
    with cu_opt2:
        cu_length = st.text_input("Length Proxy (optional)", placeholder="e.g. 12 pages, 5 min, 2000 words", key="add_length")

    if st.button("Save Asset & Content", type="primary", key="save_asset_btn"):
        if not add_name.strip():
            st.error("Asset Name is required.")
        else:
            content_valid = True
            if add_content_type == "Upload File" and not uploaded_file:
                st.warning("You selected 'Upload File' but didn't attach a file. Asset saved without content.")
                content_valid = False
            elif add_content_type == "Paste Link" and not add_link_url.strip():
                st.warning("You selected 'Paste Link' but didn't enter a URL. Asset saved without content.")
                content_valid = False
            elif add_content_type == "Paste Text" and not add_text_content.strip():
                st.warning("You selected 'Paste Text' but didn't enter any text. Asset saved without content.")
                content_valid = False

            new_asset_id = save_asset({
                "asset_id": add_id.strip() or None,
                "asset_name": add_name.strip(),
                "product": add_product or None,
                "region": add_region or None,
                "segment": add_segment or None,
                "action_type": add_action or None,
                "funnel_stage": add_funnel or None,
                "performance_tier": add_tier or None,
                "why_it_worked": [add_wiw] if add_wiw else [],
                "notes": add_notes.strip() or "",
                "on_sage_com": add_sage,
                "audience": add_audience or None,
                "copy_angle": add_copy_angle or None,
                "asset_type": add_asset_type or None,
            })

            has_content = (add_content_type != "None") and content_valid

            if has_content:
                file_path = None
                file_name = None
                file_type = None
                content_type_val = "file"
                link_url_val = None
                text_content_val = None

                if add_content_type == "Upload File" and uploaded_file:
                    file_name = os.path.basename(uploaded_file.name)
                    file_name = re.sub(r'[^a-zA-Z0-9._\-]', '_', file_name)
                    ext = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""
                    file_type = ext
                    import time as _time
                    safe_name = f"{new_asset_id}_{int(_time.time())}_{file_name}"
                    file_path = os.path.join("uploads", safe_name)
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    content_type_val = "file"
                elif add_content_type == "Paste Link":
                    content_type_val = "link"
                    link_url_val = add_link_url.strip()
                    file_name = link_url_val
                elif add_content_type == "Paste Text":
                    content_type_val = "text"
                    text_content_val = add_text_content.strip()
                    file_name = f"Text ({len(text_content_val)} chars)"

            if has_content:
                save_content_item({
                    "asset_db_id": new_asset_id,
                    "file_name": file_name,
                    "file_type": file_type,
                    "file_path": file_path,
                    "content_type": content_type_val,
                    "link_url": link_url_val,
                    "text_content": text_content_val,
                    "primary_cta_type": cu_cta_type or None,
                    "length_proxy": cu_length.strip() or None,
                })
                st.success(f"Asset '{add_name.strip()}' added with content!")
            else:
                st.success(f"Asset '{add_name.strip()}' added to the library!")
            st.rerun()

    st.markdown("---")
    st.markdown("### Upload Content to Existing Asset")
    st.caption("Already have an asset in the library? Add content (file, link, or text) here.")

    content_assets = load_assets()
    asset_choices = {f"{a['asset_name'] or a['asset_id']} (ID: {a['id']})": a['id'] for a in content_assets}

    if not asset_choices:
        st.info("No assets in the library yet. Use the form above to add one.")
    else:
        selected_asset_label = st.selectbox("Link to Existing Asset *", [""] + list(asset_choices.keys()), key="ex_asset_select")

        ex_content_type = st.radio("Content Input Type", ["Upload File", "Paste Link", "Paste Text"], horizontal=True, key="ex_input_type")

        ex_uploaded_file = None
        ex_link_url = ""
        ex_text_content = ""

        if ex_content_type == "Upload File":
            ex_uploaded_file = st.file_uploader("Upload Content File", type=["pdf", "ppt", "pptx", "doc", "docx", "png", "jpg", "jpeg", "gif", "svg"], key="ex_file")
        elif ex_content_type == "Paste Link":
            ex_link_url = st.text_input("Link URL", placeholder="e.g. https://youtube.com/watch?v=... or https://sage.com/landing-page", key="ex_link")
        elif ex_content_type == "Paste Text":
            ex_text_content = st.text_area("Paste Content Text", placeholder="Paste body copy, transcript, email copy, etc.", height=200, key="ex_text")

        ex_cl1, ex_cl2, ex_cl3 = st.columns(3)
        with ex_cl1:
            ex_audience = st.selectbox("Audience", [""] + AUDIENCE_OPTIONS, key="ex_aud")
        with ex_cl2:
            ex_copy_angle = st.selectbox("Copy Angle", [""] + COPY_ANGLE_OPTIONS, key="ex_ca")
        with ex_cl3:
            ex_asset_type = st.selectbox("Asset Type", [""] + ASSET_TYPE_OPTIONS, key="ex_at")

        ex_submitted = st.button("Upload Content to Existing Asset", type="primary", key="ex_submit_btn")

        if ex_submitted:
            if not selected_asset_label:
                st.error("Please select an asset to link this content to.")
            else:
                asset_db_id = asset_choices[selected_asset_label]
                file_path = None
                file_name = None
                file_type = None
                ct_val = "file"
                lu_val = None
                tc_val = None

                if ex_content_type == "Upload File" and ex_uploaded_file:
                    file_name = os.path.basename(ex_uploaded_file.name)
                    file_name = re.sub(r'[^a-zA-Z0-9._\-]', '_', file_name)
                    ext = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""
                    file_type = ext
                    import time as _time
                    safe_name = f"{asset_db_id}_{int(_time.time())}_{file_name}"
                    file_path = os.path.join("uploads", safe_name)
                    with open(file_path, "wb") as f:
                        f.write(ex_uploaded_file.getbuffer())
                    ct_val = "file"
                elif ex_content_type == "Paste Link" and ex_link_url.strip():
                    ct_val = "link"
                    lu_val = ex_link_url.strip()
                    file_name = lu_val
                elif ex_content_type == "Paste Text" and ex_text_content.strip():
                    ct_val = "text"
                    tc_val = ex_text_content.strip()
                    file_name = f"Text ({len(tc_val)} chars)"

                save_content_item({
                    "asset_db_id": asset_db_id,
                    "file_name": file_name,
                    "file_type": file_type,
                    "file_path": file_path,
                    "content_type": ct_val,
                    "link_url": lu_val,
                    "text_content": tc_val,
                })

                update_fields = {}
                if ex_audience:
                    update_fields["audience"] = ex_audience
                if ex_copy_angle:
                    update_fields["copy_angle"] = ex_copy_angle
                if ex_asset_type:
                    update_fields["asset_type"] = ex_asset_type
                if update_fields:
                    conn = get_conn()
                    cur = conn.cursor()
                    set_clause = ", ".join(f"{k} = %s" for k in update_fields)
                    cur.execute(f"UPDATE assets SET {set_clause}, updated_at = NOW() WHERE id = %s", list(update_fields.values()) + [asset_db_id])
                    conn.commit()
                    cur.close()
                    conn.close()

                st.success("Content saved and linked to asset!")
                st.rerun()

    st.markdown("---")
    st.markdown("### Uploaded Content Items")
    all_content = load_content_with_assets()
    if not all_content:
        st.info("No content uploaded yet.")
    else:
        for ci in all_content:
            ct = ci.get("content_type") or "file"
            if ct == "link":
                ci_icon = "🔗"
                ci_desc = ci.get("link_url") or ci.get("file_name") or "Link"
            elif ct == "text":
                ci_icon = "📝"
                ci_desc = ci.get("file_name") or "Pasted Text"
            else:
                ci_icon = "📄"
                ci_desc = ci.get("file_name") or "No file"
            ci_label = f"{ci_icon} {ci_desc} → {ci.get('asset_name') or 'Unknown'} ({ci.get('performance_tier') or 'Unrated'})"
            with st.expander(ci_label):
                cc1, cc2 = st.columns(2)
                with cc1:
                    st.markdown(f"**Asset:** {ci.get('asset_name')}")
                    st.markdown(f"**Funnel Stage:** {ci.get('funnel_stage') or '—'}")
                    st.markdown(f"**Performance Tier:** {ci.get('performance_tier') or 'Unrated'}")
                    st.markdown(f"**Content Type:** {ct.capitalize()}")
                    if ct == "file" and ci.get("file_name"):
                        st.markdown(f"**File:** {ci['file_name']} ({ci.get('file_type', '—')})")
                    elif ct == "link" and ci.get("link_url"):
                        st.markdown(f"**Link:** [{ci['link_url']}]({ci['link_url']})")
                    elif ct == "text" and ci.get("text_content"):
                        preview = ci["text_content"][:300] + ("..." if len(ci["text_content"]) > 300 else "")
                        st.markdown(f"**Text Preview:**")
                        st.text(preview)
                with cc2:
                    st.markdown(f"**CTA:** {ci.get('primary_cta_type') or '—'} | Placement: {ci.get('cta_placement') or '—'} | Clarity: {ci.get('cta_clarity') or '—'}")
                    st.markdown(f"**Audience:** {ci.get('stated_audience') or '—'}")
                    st.markdown(f"**Pain Point:** {ci.get('primary_pain_point') or '—'}")
                    st.markdown(f"**Proof:** {ci.get('proof_types_present') or '—'} (Strength: {ci.get('proof_strength') or '—'})")
                    st.markdown(f"**Format:** {ci.get('format_type') or '—'} | Skimmability: {ci.get('skimmability') or '—'} | Length: {ci.get('length_proxy') or '—'}")
                    diff = ci.get('differentiated_angle') or '—'
                    comp = "Yes" if ci.get('competitive_comparison') else "No"
                    st.markdown(f"**Differentiation:** {diff} | Competitive Comparison: {comp}")

                if st.button("Delete Content", key=f"del_ci_{ci['id']}", use_container_width=True):
                    if ci.get("file_path"):
                        try:
                            os.remove(ci["file_path"])
                        except OSError:
                            pass
                    delete_content_item(ci["id"])
                    st.rerun()


with tab_compare:
    st.markdown("### Comparison Dashboard")
    st.markdown('<p style="color:#6B7280;">Evidence-based performance comparison — patterns first, assets second.</p>', unsafe_allow_html=True)

    compare_assets = load_assets()

    assets_with_framework = [
        a for a in compare_assets
        if (a.get("audience") or a.get("copy_angle") or a.get("asset_type"))
        and (a.get("performance_tier") or a.get("funnel_stage") == "BOF")
    ]

    if not assets_with_framework:
        st.info("No assets with comparison attributes yet. Tag assets with **Audience**, **Copy Angle**, and **Asset Type** in the Library or Add Asset tab to enable comparisons.")
    else:
        def get_freq(items, field):
            vals = [a.get(field) for a in items if a.get(field)]
            counts = {}
            for v in vals:
                counts[v] = counts.get(v, 0) + 1
            total = len(vals)
            sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)
            return sorted_counts, total

        ctrl1, ctrl2, ctrl3 = st.columns(3)
        with ctrl1:
            avail_funnels = sorted(set(a.get("funnel_stage") for a in assets_with_framework if a.get("funnel_stage")))
            cmp_funnel = st.selectbox("Funnel Stage", avail_funnels if avail_funnels else ["—"], key="cmp_funnel")
        with ctrl2:
            avail_actions = sorted(set(a.get("action_type") for a in assets_with_framework if a.get("action_type")))
            cmp_action = st.selectbox("Action Type (optional)", ["All"] + avail_actions, key="cmp_action")
        with ctrl3:
            cmp_mode = st.selectbox("Comparison Mode", ["3-Way View", "High vs Medium", "High vs Low", "Medium vs Low"], key="cmp_mode")

        cmp_filtered = assets_with_framework
        if cmp_funnel and cmp_funnel != "—":
            cmp_filtered = [a for a in cmp_filtered if a.get("funnel_stage") == cmp_funnel]
        if cmp_action != "All":
            cmp_filtered = [a for a in cmp_filtered if a.get("action_type") == cmp_action]

        high_assets = []
        med_assets = []
        low_assets = []
        for a in cmp_filtered:
            tier = a.get("performance_tier") or ""
            if a.get("funnel_stage") == "BOF" and tier == "":
                high_assets.append(a)
            elif tier == "High":
                high_assets.append(a)
            elif tier == "Medium":
                med_assets.append(a)
            elif tier == "Low":
                low_assets.append(a)

        framework_fields = [
            ("audience", "Audience"),
            ("copy_angle", "Copy Angle"),
            ("asset_type", "Asset Type"),
        ]

        all_high = high_assets
        all_medlow = med_assets + low_assets

        content_items_all = load_content_items()
        assets_with_content = set(ci.get("asset_db_id") for ci in content_items_all)

        h_top_patterns = {}
        for field, label in framework_fields:
            h_freq_p, _ = get_freq(all_high, field)
            if h_freq_p:
                h_top_patterns[field] = set(v for v, _ in h_freq_p[:3])

        fix_list = []
        retire_list = []
        keep_list = []
        for a in low_assets:
            has_content = a["id"] in assets_with_content
            mismatches = 0
            for field, label in framework_fields:
                val = a.get(field)
                if val and field in h_top_patterns and val not in h_top_patterns[field]:
                    mismatches += 1
            if has_content and mismatches > 0:
                fix_list.append(a)
            elif not has_content:
                retire_list.append(a)
            else:
                keep_list.append(a)

        def render_tier_column(tier_assets, tier_name, bar_color, header_class):
            st.markdown(f'<div class="cmp-col-header {header_class}">{tier_name} ({len(tier_assets)})</div>', unsafe_allow_html=True)
            if not tier_assets:
                st.markdown('<p style="color:#6B7280;text-align:center;padding:1rem;">No assets</p>', unsafe_allow_html=True)
                return

            total_pv = sum(a.get("total_page_views") or 0 for a in tier_assets)
            total_dl = sum(a.get("total_downloads") or 0 for a in tier_assets)
            avg_pv = round(total_pv / len(tier_assets)) if tier_assets else 0
            avg_dl = round(total_dl / len(tier_assets)) if tier_assets else 0

            st.markdown(f'''<div class="kpi-grid">
                <div class="kpi-grid-item"><p class="kpi-value">{len(tier_assets)}</p><p class="kpi-label">Assets</p></div>
                <div class="kpi-grid-item"><p class="kpi-value">{avg_dl:,}</p><p class="kpi-label">Avg Downloads</p></div>
                <div class="kpi-grid-item"><p class="kpi-value">{avg_pv:,}</p><p class="kpi-label">Avg Page Views</p></div>
                <div class="kpi-grid-item"><p class="kpi-value">{total_pv:,}</p><p class="kpi-label">Total Views</p></div>
            </div>''', unsafe_allow_html=True)

            aud_freq, aud_total = get_freq(tier_assets, "audience")
            if aud_freq:
                st.markdown('<p style="color:#e0e0e0;font-size:0.95rem;font-weight:600;margin:1.2rem 0 0.4rem;text-transform:uppercase;letter-spacing:0.05em;">Audience Breakdown</p>', unsafe_allow_html=True)
                st.markdown(render_breakdown_bars(aud_freq, aud_total, bar_color, size="lg"), unsafe_allow_html=True)

            ca_freq, ca_total = get_freq(tier_assets, "copy_angle")
            if ca_freq:
                st.markdown('<p style="color:#9ca3af;font-size:0.8rem;margin:1rem 0 0.3rem;text-transform:uppercase;letter-spacing:0.05em;">Copy Angle</p>', unsafe_allow_html=True)
                st.markdown(render_breakdown_bars(ca_freq, ca_total, bar_color, size="sm"), unsafe_allow_html=True)

            at_freq, at_total = get_freq(tier_assets, "asset_type")
            if at_freq:
                st.markdown('<p style="color:#9ca3af;font-size:0.8rem;margin:1rem 0 0.3rem;text-transform:uppercase;letter-spacing:0.05em;">Asset Type</p>', unsafe_allow_html=True)
                st.markdown(render_breakdown_bars(at_freq, at_total, bar_color, size="sm"), unsafe_allow_html=True)

            if tier_assets:
                st.markdown('<p style="color:#6B7280;font-size:0.7rem;margin:1.2rem 0 0.3rem;text-transform:uppercase;letter-spacing:0.08em;">Assets</p>', unsafe_allow_html=True)
                for a in tier_assets[:8]:
                    name = a.get("asset_name") or a.get("asset_id") or "Untitled"
                    atype = a.get("asset_type") or ""
                    type_html = f'<span class="badge badge-mof compact-asset-badge">{atype}</span>' if atype else ""
                    st.markdown(f'<div class="compact-asset"><span class="compact-asset-name" title="{name}">{name}</span>{type_html}</div>', unsafe_allow_html=True)
                if len(tier_assets) > 8:
                    st.markdown(f'<p style="color:#4B5563;font-size:0.72rem;text-align:center;margin-top:0.3rem;">+{len(tier_assets) - 8} more</p>', unsafe_allow_html=True)

        def build_sticky_panel_insights():
            diff_bullets = []
            low_bullets = []

            for field, label in framework_fields:
                h_freq, h_total = get_freq(all_high, field)
                m_freq, m_total = get_freq(med_assets, field)
                l_freq, l_total = get_freq(low_assets, field)

                if h_freq and (m_freq or l_freq):
                    h_top = h_freq[0][0]
                    h_pct = round(h_freq[0][1] / h_total * 100) if h_total else 0

                    compare_freq = l_freq if l_freq else m_freq
                    compare_total = l_total if l_freq else m_total
                    compare_label = "Low" if l_freq else "Medium"

                    if compare_freq:
                        c_top = compare_freq[0][0]
                        c_pct = round(compare_freq[0][1] / compare_total * 100) if compare_total else 0

                        if h_top != c_top:
                            diff_bullets.append(f"<strong>{label}:</strong> High favors <em>{h_top}</em> ({h_pct}%) vs {compare_label} <em>{c_top}</em> ({c_pct}%)")

                        all_vals = set()
                        for f_list in [h_freq, m_freq, l_freq]:
                            for v, _ in f_list:
                                all_vals.add(v)
                        for val in all_vals:
                            hp = next((round(c/h_total*100) for v, c in h_freq if v == val), 0) if h_total else 0
                            lp = next((round(c/l_total*100) for v, c in l_freq if v == val), 0) if l_total else 0
                            mp = next((round(c/m_total*100) for v, c in m_freq if v == val), 0) if m_total else 0
                            delta = max(abs(hp - lp), abs(hp - mp))
                            if delta >= 25 and f"<strong>{label}:" not in " ".join(diff_bullets[-1:]):
                                diff_bullets.append(f"<strong>{label}:</strong> <em>{val}</em> — High {hp}% vs Low {lp}% ({'+' if hp > lp else ''}{hp-lp}%)")

                if h_freq and l_freq:
                    h_top = h_freq[0][0]
                    l_top = l_freq[0][0]
                    if h_top != l_top:
                        h_pct = round(h_freq[0][1] / h_total * 100) if h_total else 0
                        l_pct = round(l_freq[0][1] / l_total * 100) if l_total else 0
                        low_bullets.append(f"<strong>{label} mismatch:</strong> Low favors <em>{l_top}</em> ({l_pct}%) while High favors <em>{h_top}</em> ({h_pct}%)")

            return diff_bullets[:5], low_bullets[:3]

        diff_bullets, low_bullets = build_sticky_panel_insights()

        if cmp_mode == "3-Way View":
            main_col, panel_col = st.columns([3, 1])
            with main_col:
                tc1, tc2, tc3 = st.columns(3)
                with tc1:
                    render_tier_column(high_assets, "High", "breakdown-bar-green", "cmp-col-high")
                with tc2:
                    render_tier_column(med_assets, "Medium", "breakdown-bar-yellow", "cmp-col-med")
                with tc3:
                    render_tier_column(low_assets, "Low", "breakdown-bar-red", "cmp-col-low")
        elif cmp_mode == "High vs Medium":
            main_col, panel_col = st.columns([3, 1])
            with main_col:
                tc1, tc2 = st.columns(2)
                with tc1:
                    render_tier_column(high_assets, "High", "breakdown-bar-green", "cmp-col-high")
                with tc2:
                    render_tier_column(med_assets, "Medium", "breakdown-bar-yellow", "cmp-col-med")
        elif cmp_mode == "High vs Low":
            main_col, panel_col = st.columns([3, 1])
            with main_col:
                tc1, tc2 = st.columns(2)
                with tc1:
                    render_tier_column(high_assets, "High", "breakdown-bar-green", "cmp-col-high")
                with tc2:
                    render_tier_column(low_assets, "Low", "breakdown-bar-red", "cmp-col-low")
        elif cmp_mode == "Medium vs Low":
            main_col, panel_col = st.columns([3, 1])
            with main_col:
                tc1, tc2 = st.columns(2)
                with tc1:
                    render_tier_column(med_assets, "Medium", "breakdown-bar-yellow", "cmp-col-med")
                with tc2:
                    render_tier_column(low_assets, "Low", "breakdown-bar-red", "cmp-col-low")
        else:
            main_col, panel_col = st.columns([3, 1])

        with panel_col:
            st.markdown('<div class="sticky-panel">', unsafe_allow_html=True)

            st.markdown('<div class="insight-panel">', unsafe_allow_html=True)
            st.markdown('<p style="color:#e0e0e0;font-size:1rem;font-weight:600;margin:0 0 0.2rem;">What\'s Different</p>', unsafe_allow_html=True)
            st.markdown('<p style="color:#6B7280;font-size:0.75rem;margin:0 0 0.8rem;">Key pattern differences across tiers</p>', unsafe_allow_html=True)

            if diff_bullets:
                for b in diff_bullets:
                    st.markdown(f'<div class="insight-bullet">{b}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<p style="color:#4B5563;font-size:0.85rem;">Not enough data to identify differences. Tag more assets with audience, copy angle, and asset type.</p>', unsafe_allow_html=True)

            if low_bullets:
                st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
                st.markdown('<p style="color:#fca5a5;font-size:0.85rem;font-weight:600;margin:0 0 0.5rem;">Why Low May Underperform</p>', unsafe_allow_html=True)
                for b in low_bullets:
                    st.markdown(f'<div class="insight-bullet" style="border-left-color:#EF4444;">{b}</div>', unsafe_allow_html=True)

            if low_assets:
                st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
                st.markdown('<p style="color:#9ca3af;font-size:0.85rem;font-weight:600;margin:0 0 0.5rem;">Decision Summary</p>', unsafe_allow_html=True)
                dec_html = f'''<div style="display:flex;gap:0.4rem;margin-bottom:0.5rem;">
                    <div style="flex:1;background:#1e3a5f;border-radius:6px;padding:0.4rem;text-align:center;border:1px solid #2563eb;">
                        <span style="color:#60a5fa;font-weight:700;font-size:1.1rem;">{len(fix_list)}</span>
                        <span style="color:#93c5fd;font-size:0.65rem;display:block;">Fix</span></div>
                    <div style="flex:1;background:#3b1325;border-radius:6px;padding:0.4rem;text-align:center;border:1px solid #9f1239;">
                        <span style="color:#fb7185;font-weight:700;font-size:1.1rem;">{len(retire_list)}</span>
                        <span style="color:#fca5a5;font-size:0.65rem;display:block;">Retire</span></div>
                    <div style="flex:1;background:#1f2937;border-radius:6px;padding:0.4rem;text-align:center;border:1px solid #4B5563;">
                        <span style="color:#9ca3af;font-weight:700;font-size:1.1rem;">{len(keep_list)}</span>
                        <span style="color:#d1d5db;font-size:0.65rem;display:block;">Keep</span></div>
                </div>'''
                st.markdown(dec_html, unsafe_allow_html=True)

            st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div style="margin-top:0.5rem;">', unsafe_allow_html=True)
            insight_q = st.text_input("Ask about performance patterns", placeholder="e.g. What copy angles work best?", key="insight_q", label_visibility="collapsed")
            st.markdown('</div>', unsafe_allow_html=True)

            if insight_q:
                q_lower = insight_q.lower()
                st.markdown('<div class="insight-panel" style="margin-top:0.5rem;">', unsafe_allow_html=True)
                st.markdown('<p style="color:#00C853;font-size:0.8rem;font-weight:600;margin:0 0 0.5rem;">Insights</p>', unsafe_allow_html=True)

                response_lines = []

                for field, label in framework_fields:
                    h_freq, h_total = get_freq(all_high, field)
                    l_freq, l_total = get_freq(low_assets, field)
                    if h_freq:
                        top_vals = ", ".join(f"<em>{v}</em> ({round(c/h_total*100)}%)" for v, c in h_freq[:2])
                        response_lines.append(f"High {label.lower()}: {top_vals}")

                if "high" in q_lower or "success" in q_lower or "pattern" in q_lower or "work" in q_lower:
                    for field, label in framework_fields:
                        h_freq, h_total = get_freq(all_high, field)
                        if h_freq and h_total >= 2:
                            top_pct = round(h_freq[0][1] / h_total * 100)
                            if top_pct >= 30:
                                response_lines.append(f"High performers concentrate on <em>{h_freq[0][0]}</em> for {label.lower()} ({top_pct}%). This may indicate a proven pattern.")

                elif "low" in q_lower or "underperform" in q_lower or "retire" in q_lower or "fix" in q_lower:
                    for field, label in framework_fields:
                        h_freq, h_total = get_freq(all_high, field)
                        l_freq, l_total = get_freq(low_assets, field)
                        if h_freq and l_freq and h_freq[0][0] != l_freq[0][0]:
                            response_lines.append(f"Low favors <em>{l_freq[0][0]}</em> for {label.lower()} while High favors <em>{h_freq[0][0]}</em>.")
                    if fix_list:
                        response_lines.append(f"{len(fix_list)} assets are candidates for Fix & Retest.")
                    if retire_list:
                        response_lines.append(f"{len(retire_list)} assets may be candidates for Retirement.")

                elif "asset type" in q_lower or "convert" in q_lower or "best" in q_lower:
                    h_freq, _ = get_freq(all_high, "asset_type")
                    if h_freq:
                        response_lines.append(f"Top asset types in High: {', '.join(f'<em>{v}</em>' for v, _ in h_freq[:3])}")

                elif "copy angle" in q_lower or "download" in q_lower or "angle" in q_lower:
                    h_freq, _ = get_freq(all_high, "copy_angle")
                    if h_freq:
                        response_lines.append(f"Top copy angles in High: {', '.join(f'<em>{v}</em>' for v, _ in h_freq[:3])}")

                for rl in response_lines:
                    st.markdown(f'<div class="insight-bullet" style="font-size:0.8rem;margin:0.4rem 0;">{rl}</div>', unsafe_allow_html=True)

                st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)


with tab_import:
    st.subheader("Import & Parse Sage Asset Filenames")
    st.markdown("""
Paste asset filenames (one per line). Expected pattern:

`[Product]_[Region]_[Segment]_[Action]_[FunnelStage]_[AssetName]`

Example: `CL_INT_US_MED_TOO_BOFU_CerosProdTour`
""")

    asset_text = st.text_area(
        "Asset filenames:",
        height=200,
        placeholder="CL_INT_US_MED_TOO_BOFU_CerosProdTour\nCL_INT_US_SMB_DLE_TOFU_FinanceLeadersEbook",
        key="import_text",
    )

    if st.button("Parse & Preview", type="primary", key="parse_btn"):
        if asset_text.strip():
            lines = [l.strip().strip(",; ") for l in asset_text.strip().splitlines() if l.strip()]
            seen = set()
            parsed = []
            dupes = []
            for line in lines:
                if not line:
                    continue
                if line in seen:
                    dupes.append(line)
                else:
                    seen.add(line)
                    parsed.append(parse_asset(line))

            st.session_state["parsed_preview"] = parsed
            st.session_state["parsed_dupes"] = dupes
        else:
            st.warning("Please enter at least one filename.")

    if "parsed_preview" in st.session_state and st.session_state["parsed_preview"]:
        parsed = st.session_state["parsed_preview"]
        dupes = st.session_state.get("parsed_dupes", [])

        st.markdown(f"**Parsed {len(parsed)} assets** ({len(dupes)} duplicate{'s' if len(dupes) != 1 else ''} removed)")

        if dupes:
            with st.expander(f"Duplicates removed ({len(dupes)})"):
                for d in dupes:
                    st.code(d, language=None)

        preview_data = []
        for a in parsed:
            preview_data.append({
                "Asset ID": a["asset_id"],
                "Product": a["product"] or "—",
                "Region": a["region"] or "—",
                "Segment": a["segment"] or "—",
                "Action": a["action_type"] or "—",
                "Funnel": a["funnel_stage"] or "—",
                "Asset Name": a["asset_name"] or "—",
                "Notes": a["notes"] or "",
            })
        st.dataframe(preview_data, use_container_width=True, hide_index=True)

        if st.button("Import All to Library", type="primary", key="import_btn"):
            imported = 0
            skipped = 0
            for a in parsed:
                if check_duplicate(a["asset_id"]):
                    skipped += 1
                else:
                    save_asset(a)
                    imported += 1
            st.success(f"Imported {imported} assets. {skipped} skipped (already in library).")
            del st.session_state["parsed_preview"]
            if "parsed_dupes" in st.session_state:
                del st.session_state["parsed_dupes"]
            st.rerun()


with tab_unrated:
    st.subheader("Unrated Assets")
    st.markdown("Assets that haven't been assigned a performance tier yet. Rate them here to keep your library clean.")

    unrated_assets = [a for a in load_assets() if not a.get("performance_tier")]

    if not unrated_assets:
        st.success("All assets have been rated! Your library is in good shape.")
    else:
        st.warning(f"**{len(unrated_assets)} unrated asset{'s' if len(unrated_assets) != 1 else ''}** need attention.")

        for ua in unrated_assets:
            ua_label = f"⚪ {ua.get('asset_name') or ua.get('asset_id') or 'Untitled'}"
            funnel_badge = f" — {ua.get('funnel_stage')}" if ua.get('funnel_stage') else ""
            product_badge = f" | {ua.get('product')}" if ua.get('product') else ""
            with st.expander(f"{ua_label}{funnel_badge}{product_badge}"):
                ur_d, ur_e = st.columns([1, 1])

                with ur_d:
                    st.markdown(f"**Asset ID:** `{ua.get('asset_id') or '—'}`")
                    st.markdown(f"**Product:** {ua.get('product') or '—'}")
                    st.markdown(f"**Segment:** {ua.get('segment') or '—'}")
                    st.markdown(f"**Action Type:** {ua.get('action_type') or '—'}")
                    st.markdown(f"**Funnel Stage:** {ua.get('funnel_stage') or '—'}")
                    st.markdown(f"**Audience:** {ua.get('audience') or '—'}")
                    st.markdown(f"**Copy Angle:** {ua.get('copy_angle') or '—'}")
                    st.markdown(f"**Asset Type:** {ua.get('asset_type') or '—'}")
                    pv = ua.get("total_page_views") or 0
                    dl = ua.get("total_downloads") or 0
                    if pv or dl:
                        st.markdown(f"**Page Views:** {pv:,} · **Downloads:** {dl:,}")
                    st.markdown(f"**On Sage.com:** {'Yes' if ua.get('on_sage_com') else 'No'}")

                with ur_e:
                    ur_key = f"ur_{ua['id']}"
                    ur_tier = st.selectbox("Set Performance Tier", [""] + PERFORMANCE_TIERS, key=f"{ur_key}_tier")
                    ur_wiw = st.selectbox("Why It Worked", [""] + WHY_IT_WORKED_OPTIONS, key=f"{ur_key}_wiw")

                    cur_aud = ua.get("audience") or ""
                    ur_aud_opts = [""] + AUDIENCE_OPTIONS
                    ur_aud_idx = ur_aud_opts.index(cur_aud) if cur_aud in ur_aud_opts else 0
                    ur_audience = st.selectbox("Audience", ur_aud_opts, index=ur_aud_idx, key=f"{ur_key}_aud")

                    cur_ca = ua.get("copy_angle") or ""
                    ur_ca_opts = [""] + COPY_ANGLE_OPTIONS
                    ur_ca_idx = ur_ca_opts.index(cur_ca) if cur_ca in ur_ca_opts else 0
                    ur_copy_angle = st.selectbox("Copy Angle", ur_ca_opts, index=ur_ca_idx, key=f"{ur_key}_ca")

                    cur_at = ua.get("asset_type") or ""
                    ur_at_opts = [""] + ASSET_TYPE_OPTIONS
                    ur_at_idx = ur_at_opts.index(cur_at) if cur_at in ur_at_opts else 0
                    ur_asset_type = st.selectbox("Asset Type", ur_at_opts, index=ur_at_idx, key=f"{ur_key}_at")

                    if st.button("Save Rating", key=f"{ur_key}_save", type="primary", use_container_width=True):
                        if not ur_tier:
                            st.error("Please select a performance tier.")
                        else:
                            update_asset(ua["id"], {
                                "asset_name": ua.get("asset_name"),
                                "product": ua.get("product"),
                                "region": ua.get("region"),
                                "segment": ua.get("segment"),
                                "action_type": ua.get("action_type"),
                                "funnel_stage": ua.get("funnel_stage"),
                                "performance_tier": ur_tier,
                                "why_it_worked": [ur_wiw] if ur_wiw else ua.get("why_it_worked", []),
                                "notes": ua.get("notes"),
                                "on_sage_com": ua.get("on_sage_com", False),
                                "audience": ur_audience or ua.get("audience"),
                                "copy_angle": ur_copy_angle or ua.get("copy_angle"),
                                "asset_type": ur_asset_type or ua.get("asset_type"),
                            })
                            st.success(f"Rated '{ua.get('asset_name')}' as {ur_tier}!")
                            st.rerun()


with tab_export:
    st.subheader("Export Library")

    assets_for_export = load_assets()
    if not assets_for_export:
        st.info("No assets to export.")
    else:
        all_content_export = load_content_with_assets()
        content_by_asset = {}
        for ci in all_content_export:
            adb = ci.get("asset_db_id")
            if adb not in content_by_asset:
                content_by_asset[adb] = []
            content_by_asset[adb].append({
                "file_name": ci.get("file_name"),
                "file_type": ci.get("file_type"),
                "content_type": ci.get("content_type") or "file",
                "link_url": ci.get("link_url"),
                "text_content": ci.get("text_content"),
                "primary_cta_type": ci.get("primary_cta_type"),
                "cta_placement": ci.get("cta_placement"),
                "cta_clarity": ci.get("cta_clarity"),
                "stated_audience": ci.get("stated_audience"),
                "primary_pain_point": ci.get("primary_pain_point"),
                "proof_types_present": ci.get("proof_types_present"),
                "proof_strength": ci.get("proof_strength"),
                "format_type": ci.get("format_type"),
                "skimmability": ci.get("skimmability"),
                "length_proxy": ci.get("length_proxy"),
                "differentiated_angle": ci.get("differentiated_angle"),
                "competitive_comparison": bool(ci.get("competitive_comparison")),
            })

        export_data = {"assets": [], "duplicates_removed": []}
        for a in assets_for_export:
            asset_entry = {
                "asset_id": a.get("asset_id"),
                "product": a.get("product"),
                "region": a.get("region"),
                "segment": a.get("segment"),
                "action_type": a.get("action_type"),
                "funnel_stage": a.get("funnel_stage"),
                "asset_name": a.get("asset_name"),
                "audience": a.get("audience"),
                "copy_angle": a.get("copy_angle"),
                "asset_type": a.get("asset_type"),
                "total_page_views": a.get("total_page_views") or 0,
                "total_downloads": a.get("total_downloads") or 0,
                "on_sage_com": bool(a.get("on_sage_com")),
                "performance_tier": a.get("performance_tier"),
                "why_it_worked": a.get("why_it_worked") or [],
                "notes": a.get("notes") or "",
            }
            if a["id"] in content_by_asset:
                asset_entry["content_items"] = content_by_asset[a["id"]]
            export_data["assets"].append(asset_entry)

        st.json(export_data)

        st.download_button(
            label="Download JSON",
            data=json.dumps(export_data, indent=2, default=str),
            file_name="sage_content_library.json",
            mime="application/json",
            use_container_width=True,
        )
