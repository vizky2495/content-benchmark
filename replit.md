# Content Benchmark

## Overview
A Streamlit web application serving as a searchable benchmark library of Sage content assets. Assets are tagged by product, region, segment, action type, funnel stage, audience, copy angle, and asset type — with performance signals and "why it worked" insights. Dark HubSpot-style UI with Sage green accents, single-selection dropdowns throughout. Includes multi-format content upload (file, link, text) with attribute tagging and an enhanced comparison dashboard with 3-way tier views, breakdown bars, delta analysis, decision panels, and an Insights Assistant.

## User Preferences
- Preferred communication style: Simple, everyday language.
- UX theme: Dark charcoal (#1a1a2e) with Sage green (#00C853) accents — HubSpot-style executive dashboard feel
- All selections: Single dropdowns only (no multiselect)
- Library view: Group by performance tier ranking with drill-down metrics

## System Architecture

### Application Structure
- **`app.py`**: Single-page Streamlit app with parsing logic, CRUD operations, search, content upload, comparison framework, and UI
- **`main.py`**: Unused placeholder
- **`uploads/`**: Directory for uploaded content files

### Database (PostgreSQL)
Table: `assets`
- `id` (SERIAL PK), `asset_id` (TEXT), `asset_name` (TEXT)
- `product` (TEXT), `region` (TEXT), `segment` (TEXT), `action_type` (TEXT)
- `funnel_stage` (TEXT: TOF/MOF/BOF)
- `performance_tier` (TEXT: High/Medium/Low)
- `audience` (TEXT — fixed picklist: CFO/Finance Leader, Controller/Accounting, Executive/Leadership, IT/Systems, Nonprofit Operator, Accountant/Partner, General Finance)
- `copy_angle` (TEXT — fixed picklist: Efficiency/Time Savings, Financial Visibility/Reporting, Growth/Scaling, Compliance/Risk, Automation, AI/Innovation, Industry-Specific Challenges, Cost Reduction, General ERP Overview)
- `asset_type` (TEXT — fixed picklist: Guide, E-book, Whitepaper, Case Study, Product Tour, Demo, Pricing Page, Webinar, Video, Checklist, Landing Page)
- `why_it_worked` (TEXT[]), `notes` (TEXT)
- `total_page_views` (INTEGER), `total_downloads` (INTEGER)
- `on_sage_com` (BOOLEAN, default FALSE)
- `created_at`, `updated_at` (TIMESTAMP)

Table: `content_items`
- `id` (SERIAL PK), `asset_db_id` (INTEGER FK → assets.id ON DELETE CASCADE)
- `file_name` (TEXT), `file_type` (TEXT), `file_path` (TEXT)
- `content_type` (TEXT: file/link/text), `link_url` (TEXT), `text_content` (TEXT)
- CTA: `primary_cta_type` (TEXT), `cta_placement` (TEXT: Top/Mid/End), `cta_clarity` (TEXT: Clear/Vague)
- Audience: `stated_audience` (TEXT), `primary_pain_point` (TEXT)
- Proof: `proof_types_present` (TEXT: Numbers/Case Study/Testimonial/Screenshots/None), `proof_strength` (TEXT: Strong/Medium/Weak)
- Structure: `format_type` (TEXT), `skimmability` (TEXT: High/Medium/Low), `length_proxy` (TEXT)
- Differentiation: `differentiated_angle` (TEXT), `competitive_comparison` (BOOLEAN)
- `created_at`, `updated_at` (TIMESTAMP)

### Filename Pattern
`[Product]_[Region]_[Segment]_[Action]_[FunnelStage]_[AssetName]`

Field mappings:
- **Product**: CL_INT → Intacct, CL_S50 → Sage 50, CL_BMS → Sage Business Management, CL_CRE → Sage CRE, CL_ACS → Sage Accountant Solutions, CL_FAS → Sage Fixed Assets, CL_COPILOT → Sage Copilot
- **Region**: US → United States
- **Segment**: MED → Medium, SMB → Small Business, SMA → Small, ENT → Enterprise
- **Action**: TOO → Product Tour, DLE → Download E-book, TTE → Talk to Expert, DEM → Request Demo, WBR → Webinar, PDF → Content Download, CON → Contact, TRL → Trial, VID → Video, QUO → Quote, WEB → Webinar, LGO → Lead Gen Offer, HPFS → High Performance Series, EBK → E-book
- **Funnel**: TOFU → TOF, MOFU → MOF, BOFU → BOF

Unknown codes keep raw value and set notes to "Unknown code".

### Content Upload
Three input modes:
- **Upload File**: PDF, PPT, PPTX, DOC, DOCX, PNG, JPG, JPEG, GIF, SVG
- **Paste Link**: YouTube/Vimeo URLs, landing page URLs
- **Paste Text**: Body copy, transcripts, email copy

### Content Comparison Framework
- Each asset has: `audience` (picklist), `copy_angle` (picklist), `asset_type` (picklist), `performance_tier`
- Compare within same funnel stage only
- Count frequency of audience, copy_angle, asset_type
- Identify most common combinations in High performers vs Medium/Low
- Output: Top patterns in High, Top patterns in Med/Low, 3-5 actionable insights
- No subjective judgments — all insights based on frequency patterns and performance tiers
- BOF assets: treat unrated as High (SQO generation)

### Comparison Dashboard Features
- Comparison Mode selector: 3-Way View (default), High vs Medium, High vs Low, Medium vs Low
- Each tier column shows: KPI snapshot (count, avg downloads, avg page views, total views), asset type breakdown bars, copy angle breakdown bars, asset list
- "What's Different" section: delta analysis table comparing attribute percentages across tiers
- "Why Low is Low" section: evidence-based bullet points about pattern mismatches
- Low Performer Decision Panel: rules-based classification (Fix & Retest / Retire / Keep)
- Insights Assistant: text input with suggested prompts, pattern-matching responses using frequency data

### Library Tab Features
- Search bar (asset name only)
- Filter dropdowns: funnel stage, action type, segment, product, on sage.com
- Grouped by performance tier (High/Medium/Low/Unrated) with colored metric cards
- Each metric card shows count; click to drill down into that tier
- Tier sections show aggregate stats (page views, downloads, funnel breakdown, sage.com count)
- Expandable asset cards with edit (incl. audience, copy angle, asset type, on sage.com) and delete

### Tabs
- **Library**: Grouped tier view with drill-down metrics and asset cards
- **Add Asset & Content**: Combined form — add asset with audience/copy_angle/asset_type + optionally upload content (file/link/text) with attributes; also upload to existing assets
- **Comparison**: Executive dashboard with 3-way tier comparison, breakdown bars, delta analysis, decision panels, and Insights Assistant
- **Unrated**: Shows only unrated assets with quick-rate controls (tier + why it worked + audience/copy_angle/asset_type)
- **Import & Parse**: Bulk parse filenames and import to library
- **Export**: JSON export with download (includes all fields + content items)

### Running
```
streamlit run app.py --server.port 5000
```

## Dependencies
- Python 3.11, Streamlit, psycopg2-binary, PostgreSQL
