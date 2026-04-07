import io
import os
from datetime import datetime
from typing import Dict, List, Tuple, Optional

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from PIL import Image


# ============================================================
# CONFIG
# ============================================================
PICTURES_FOLDER = "Pictures"
PX_SAMPLES = 10
APP_TITLE = "Keyence IV4 Smart Camera Engineering Tool"

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="📷",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# LIGHT ENGINEERING UI
# ============================================================
st.markdown(
    """
    <style>
    :root {
        --bg: #f6f8fb;
        --card: #ffffff;
        --text: #17202a;
        --muted: #607080;
        --line: #dfe6ee;
        --brand: #0b65d8;
        --brand-soft: #eaf3ff;
        --ok: #0b8f4d;
        --ok-soft: #e8f7ef;
        --warn: #b97500;
        --warn-soft: #fff6df;
        --bad: #c7382a;
        --bad-soft: #fdecea;
        --slate: #34495e;
    }

    .stApp {
        background: linear-gradient(180deg, #f7f9fc 0%, #eef3f8 100%);
        color: var(--text);
    }

    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 4rem;
        max-width: 1550px;
    }

    [data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid var(--line);
    }

    .hero {
        background: linear-gradient(135deg, #ffffff 0%, #f2f7ff 100%);
        border: 1px solid var(--line);
        border-radius: 18px;
        padding: 22px 26px;
        box-shadow: 0 8px 24px rgba(25, 52, 84, 0.06);
        margin-bottom: 14px;
    }

    .hero h1 {
        margin: 0;
        font-size: 1.6rem;
        color: #11263a;
    }

    .hero p {
        margin: 6px 0 0 0;
        color: var(--muted);
        font-size: 0.94rem;
    }

    .summary-card {
        background: var(--card);
        border: 1px solid var(--line);
        border-radius: 16px;
        padding: 14px 16px;
        box-shadow: 0 5px 16px rgba(16, 35, 58, 0.04);
        height: 100%;
    }

    .summary-label {
        color: var(--muted);
        font-size: 0.72rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 4px;
        font-weight: 700;
    }

    .summary-value {
        color: var(--text);
        font-size: 1.12rem;
        font-weight: 700;
        line-height: 1.25;
    }

    .summary-subvalue {
        color: var(--muted);
        font-size: 0.8rem;
        margin-top: 3px;
    }

    .panel {
        background: var(--card);
        border: 1px solid var(--line);
        border-radius: 18px;
        padding: 18px 18px 16px 18px;
        box-shadow: 0 6px 20px rgba(16, 35, 58, 0.04);
        margin-bottom: 14px;
    }

    .panel-title {
        font-size: 0.75rem;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        color: var(--muted);
        font-weight: 700;
        margin-bottom: 12px;
    }

    .verdict-box {
        border-radius: 16px;
        padding: 16px 18px;
        border: 1px solid;
        margin-bottom: 10px;
    }

    .verdict-ok {
        background: var(--ok-soft);
        border-color: #b7e3c9;
        color: #0b5c34;
    }

    .verdict-warn {
        background: var(--warn-soft);
        border-color: #efd59a;
        color: #7c5400;
    }

    .verdict-bad {
        background: var(--bad-soft);
        border-color: #f1bcb4;
        color: #8e261d;
    }

    .verdict-title {
        font-size: 1rem;
        font-weight: 800;
        margin-bottom: 4px;
    }

    .small-note {
        font-size: 0.82rem;
        color: var(--muted);
    }

    .badge-row {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 8px;
    }

    .badge {
        display: inline-block;
        padding: 6px 10px;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 700;
        border: 1px solid;
        background: #fff;
    }

    .badge-ok { color: #0b6c3a; border-color: #b7e3c9; background: #eefaf3; }
    .badge-warn { color: #8a5b00; border-color: #f0d28c; background: #fff8e7; }
    .badge-bad { color: #9a261b; border-color: #efb3aa; background: #fff0ee; }
    .badge-neutral { color: #32506b; border-color: #cfe0f1; background: #f5faff; }

    .spec-table-wrap {
        background: #fff;
        border: 1px solid var(--line);
        border-radius: 18px;
        overflow: auto;
        box-shadow: 0 6px 20px rgba(16, 35, 58, 0.04);
    }

    table.spec-table {
        border-collapse: separate;
        border-spacing: 0;
        width: 100%;
        min-width: 1180px;
        font-size: 0.84rem;
    }

    .spec-table thead th {
        position: sticky;
        top: 0;
        z-index: 5;
        background: #143b63;
        color: #fff;
        padding: 12px 10px;
        border-right: 1px solid #31567b;
        text-align: center;
        font-weight: 700;
    }

    .spec-table thead th:first-child,
    .spec-table thead th:nth-child(2) {
        left: 0;
        z-index: 6;
    }

    .spec-table thead th:nth-child(2) {
        left: 220px;
        z-index: 6;
    }

    .spec-table tbody td {
        border-right: 1px solid #ebf0f5;
        border-bottom: 1px solid #ebf0f5;
        padding: 10px 12px;
        vertical-align: top;
        background: #fff;
    }

    .spec-table tbody tr:nth-child(even) td {
        background: #fbfdff;
    }

    .spec-table tbody td:first-child {
        position: sticky;
        left: 0;
        z-index: 4;
        min-width: 220px;
        max-width: 220px;
        background: #f8fbff;
        font-weight: 700;
        color: #294a67;
    }

    .spec-table tbody td:nth-child(2) {
        position: sticky;
        left: 220px;
        z-index: 4;
        min-width: 220px;
        max-width: 220px;
        background: #fcfdff;
        color: #4f6273;
        font-weight: 600;
    }

    .spec-category {
        background: #edf4fb !important;
        color: #1e4669 !important;
        font-weight: 800 !important;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }

    .tiny {
        font-size: 0.76rem;
    }

    .footer {
        color: #738496;
        font-size: 0.78rem;
        text-align: center;
        margin-top: 10px;
    }

    .formula {
        background: #f8fbff;
        border: 1px dashed #cfe0f1;
        border-radius: 12px;
        padding: 12px 14px;
        font-size: 0.84rem;
        color: #3b5368;
        margin-top: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# FORMATTERS
# ============================================================
def fmt_mm(v: float, d: int = 1) -> str:
    return f"{v:.{d}f} mm"


def fmt_pair_mm(a: float, b: float, d: int = 1) -> str:
    return f"{a:.{d}f} × {b:.{d}f} mm"


def fmt_mm_px(v: float, d: int = 4) -> str:
    return f"{v:.{d}f} mm/px"


def fmt_px_mm(v: float, d: int = 2) -> str:
    return f"{v:.{d}f} px/mm"


def fmt_pct(v: float, d: int = 1) -> str:
    return f"{v:.{d}f}%"


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def lerp(v: float, in0: float, in1: float, out0: float, out1: float) -> float:
    if in1 == in0:
        return float(out0)
    return float(out0 + (v - in0) * (out1 - out0) / (in1 - in0))


def fov_from_dist(dist: float, cam: Dict) -> Tuple[float, float]:
    fx = lerp(dist, cam["min_dist"], cam["max_dist"], cam["min_fov_x"], cam["max_fov_x"])
    fy = lerp(dist, cam["min_dist"], cam["max_dist"], cam["min_fov_y"], cam["max_fov_y"])
    return fx, fy


def dist_from_fov(fov_x: float, cam: Dict) -> float:
    return lerp(fov_x, cam["min_fov_x"], cam["max_fov_x"], cam["min_dist"], cam["max_dist"])


def resolution_metrics(fov_mm: float, pixels: int) -> Tuple[float, float]:
    if pixels <= 0 or fov_mm <= 0:
        return 0.0, 0.0
    mm_per_px = fov_mm / pixels
    px_per_mm = 1.0 / mm_per_px
    return mm_per_px, px_per_mm


def min_feature_for_threshold(mm_per_px: float, px_threshold: float) -> float:
    return mm_per_px * px_threshold


# ============================================================
# UI HELPERS
# ============================================================
def summary_card(label: str, value: str, subvalue: str = ""):
    st.markdown(
        f"""
        <div class="summary-card">
            <div class="summary-label">{label}</div>
            <div class="summary-value">{value}</div>
            {f'<div class="summary-subvalue">{subvalue}</div>' if subvalue else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_panel_start(title: str):
    st.markdown(f'<div class="panel"><div class="panel-title">{title}</div>', unsafe_allow_html=True)


def section_panel_end():
    st.markdown('</div>', unsafe_allow_html=True)


def verdict_html(title: str, text: str, cls: str, badges: Optional[List[Tuple[str, str]]] = None):
    badge_html = ""
    if badges:
        badge_html = '<div class="badge-row">' + "".join(
            f'<span class="badge badge-{kind}">{label}</span>' for label, kind in badges
        ) + '</div>'
    st.markdown(
        f"""
        <div class="verdict-box verdict-{cls}">
            <div class="verdict-title">{title}</div>
            <div>{text}</div>
            {badge_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def log_calculation(label: str, data: Dict):
    if "history" not in st.session_state:
        st.session_state.history = []
    row = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "type": label,
    }
    row.update(data)
    st.session_state.history.append(row)


# ============================================================
# DATA
# ============================================================
@st.cache_data

def get_camera_data() -> Dict[str, Dict]:
    common = {
        "resolution_h": 1280,
        "resolution_v": 960,
        "programs": "128 programs (with SD card) / 32 programs (without SD card)",
        "network": "EtherNet/IP, PROFINET, TCP/IP",
        "ip_rating": "IP67",
        "temp_range": "0 to +50 °C",
        "humidity": "35 to 85 % RH",
        "transfer": "microSD / FTP / SFTP",
        "focus": "Auto during installation",
        "tools": "65 tools total",
    }

    return {
        "IV4-400CA": {
            **common,
            "image": "iv4-400ca.png",
            "min_fov_x": 58,
            "max_fov_x": 464,
            "min_fov_y": 44,
            "max_fov_y": 348,
            "min_dist": 400,
            "max_dist": 3000,
            "color": True,
            "type": "Narrow field of view",
            "sensor": '1/2.9 inch colour CMOS',
            "illumination": "White LED",
            "lighting": "Pulse / continuous switchable",
            "weight": "Approx. 300 g",
        },
        "IV4-400MA": {
            **common,
            "image": "iv4-400ma.png",
            "min_fov_x": 58,
            "max_fov_x": 464,
            "min_fov_y": 44,
            "max_fov_y": 348,
            "min_dist": 400,
            "max_dist": 3000,
            "color": False,
            "type": "Narrow field of view",
            "sensor": '1/2.9 inch monochrome CMOS',
            "illumination": "Infrared LED",
            "lighting": "Pulse lighting",
            "weight": "Approx. 300 g",
        },
        "IV4-500CA": {
            **common,
            "image": "iv4-500ca.png",
            "min_fov_x": 22,
            "max_fov_x": 1184,
            "min_fov_y": 16,
            "max_fov_y": 888,
            "min_dist": 50,
            "max_dist": 3000,
            "color": True,
            "type": "Standard",
            "sensor": '1/2.9 inch colour CMOS',
            "illumination": "White LED",
            "lighting": "Pulse / continuous switchable",
            "weight": "Approx. 75 g",
        },
        "IV4-500MA": {
            **common,
            "image": "iv4-500ma.png",
            "min_fov_x": 22,
            "max_fov_x": 1184,
            "min_fov_y": 16,
            "max_fov_y": 888,
            "min_dist": 50,
            "max_dist": 3000,
            "color": False,
            "type": "Standard",
            "sensor": '1/2.9 inch monochrome CMOS',
            "illumination": "Infrared LED",
            "lighting": "Pulse lighting",
            "weight": "Approx. 75 g",
        },
        "IV4-600CA": {
            **common,
            "image": "iv4-600ca.png",
            "min_fov_x": 51,
            "max_fov_x": 2730,
            "min_fov_y": 38,
            "max_fov_y": 2044,
            "min_dist": 50,
            "max_dist": 3000,
            "color": True,
            "type": "Wide field of view",
            "sensor": '1/2.9 inch colour CMOS',
            "illumination": "White LED",
            "lighting": "Pulse / continuous switchable",
            "weight": "Approx. 75 g",
        },
        "IV4-600MA": {
            **common,
            "image": "iv4-600ma.png",
            "min_fov_x": 51,
            "max_fov_x": 2730,
            "min_fov_y": 38,
            "max_fov_y": 2044,
            "min_dist": 50,
            "max_dist": 3000,
            "color": False,
            "type": "Wide field of view",
            "sensor": '1/2.9 inch monochrome CMOS',
            "illumination": "Infrared LED",
            "lighting": "Pulse lighting",
            "weight": "Approx. 75 g",
        },
    }


@st.cache_data

def get_iv4_specs_data() -> Dict:
    return {
        "models": ["IV4-400CA", "IV4-400MA", "IV4-500CA", "IV4-500MA", "IV4-600CA", "IV4-600MA"],
        "categories": {
            "Basic Information": {
                "Type": [
                    "Narrow field of view",
                    "Narrow field of view",
                    "Standard",
                    "Standard",
                    "Wide field of view",
                    "Wide field of view",
                ],
                "Installed distance": [
                    "From 400 mm *1", "From 400 mm *1",
                    "From 50 mm *1", "From 50 mm *1",
                    "From 50 mm *1", "From 50 mm *1",
                ],
            },
            "Tools": {
                "Available modes": "Standard Mode, Sorting Mode, AI Through Count Mode",
                "Available tool": "Standard/Sorting Modes: AI Differentiate, Outline, Colour Area *2, Area *3, Edge Pixels, Colour Average *2, Brightness Avg *3, Width, Diameter, Edge Presence, Pitch, Colour Prohibit, Position Adjustment, Hi-Sp. Adj (1-axis/2-axis), Blob Count, AI Identify, AI Count, Total, AI OCR, AI Trigger | AI Through Count Mode: Count, Total",
                "Number of tools": "65 tools *4",
            },
            "Field of View": {
                "Field of view": [
                    "400 mm: 58 (H) × 44 (V) mm to 3000 mm: 464 (H) × 348 (V) mm",
                    "400 mm: 58 (H) × 44 (V) mm to 3000 mm: 464 (H) × 348 (V) mm",
                    "50 mm: 22 (H) × 16 (V) mm to 3000 mm: 1184 (H) × 888 (V) mm",
                    "50 mm: 22 (H) × 16 (V) mm to 3000 mm: 1184 (H) × 888 (V) mm",
                    "50 mm: 51 (H) × 38 (V) mm to 3000 mm: 2730 (H) × 2044 (V) mm",
                    "50 mm: 51 (H) × 38 (V) mm to 3000 mm: 2730 (H) × 2044 (V) mm",
                ],
            },
            "Settings": {
                "Switch settings (programs)": "128 programs (with SD card) / 32 programs (without SD card)",
            },
            "Image Receiving Element": {
                "Type": [
                    '1/2.9 inch colour CMOS',
                    '1/2.9 inch monochrome CMOS',
                    '1/2.9 inch colour CMOS',
                    '1/2.9 inch monochrome CMOS',
                    '1/2.9 inch colour CMOS',
                    '1/2.9 inch monochrome CMOS',
                ],
                "Number of pixels": "1280 (H) × 960 (V)",
            },
            "Image History": {
                "Number of storable images": "100 images *5",
                "Save conditions": "Logging 1: NG only / OK near NG threshold *6 / All. Logging 2: number before/after NG / fixed interval *5",
            },
            "Focus Adjustment": {
                "Focus": "Auto *7",
            },
            "Image Data Transfer": {
                "Transfer destination": "microSD card / FTP server / SFTP server",
                "Transfer format": "BMP / JPEG / iv4p / txt",
                "Transfer conditions": "OK / NG / NG and OK near threshold *6 / OK near threshold *6 / All / Judgement Complete",
            },
            "Exposure Time": {
                "Exposure": "12 μs to 10 ms *8",
            },
            "Analysis Information": {
                "RUN display": "Tool-specific list (judgement, match, match bar display) *9",
                "RUN information": "OFF / histogram / processing time / count / output monitor *9",
            },
            "Lights": {
                "Illumination": ["White LED", "Infrared LED", "White LED", "Infrared LED", "White LED", "Infrared LED"],
                "Lighting method": [
                    "Pulse / continuous switchable",
                    "Pulse lighting",
                    "Pulse / continuous switchable",
                    "Pulse lighting",
                    "Pulse / continuous switchable",
                    "Pulse lighting",
                ],
            },
        },
        "footnotes": [
            "*1 If using at 3 m or more, Keyence recommends removing the polarising filter before use.",
            "*2 Colour type only.",
            "*3 Monochrome type only.",
            "*4 Total combined number of differentiation and position adjustment tools. Up to 64 differentiation tools. Up to 16 AI Count / AI OCR tools.",
            "*5 Saved to internal memory.",
            "*6 AI Differentiate, AI Identify, AI OCR (show matching rate) only.",
            "*7 Focus can be adjusted automatically during installation, not while running.",
            "*8 Maximum exposure time is 500 ms only when lighting is OFF.",
            "*9 Can be displayed on IV4-CP70, IV4-DU10, or PC software IV-H1SN.",
        ],
    }


# ============================================================
# CALCULATION ENGINE
# ============================================================
def evaluate_application(cam: Dict, distance_mm: float, part_w: float, part_h: float, feature_mm: float, req_px: float, margin_pct: float) -> Dict:
    fov_x, fov_y = fov_from_dist(distance_mm, cam)
    mmpp_h, pxpm_h = resolution_metrics(fov_x, cam["resolution_h"])
    mmpp_v, pxpm_v = resolution_metrics(fov_y, cam["resolution_v"])

    req_w = part_w * (1 + margin_pct / 100.0)
    req_h = part_h * (1 + margin_pct / 100.0)

    fit_ok = fov_x >= req_w and fov_y >= req_h
    fit_margin_w_pct = ((fov_x / req_w) - 1) * 100 if req_w > 0 else 0
    fit_margin_h_pct = ((fov_y / req_h) - 1) * 100 if req_h > 0 else 0
    fit_margin_pct = min(fit_margin_w_pct, fit_margin_h_pct)

    px_on_feature_h = feature_mm * pxpm_h
    px_on_feature_v = feature_mm * pxpm_v
    px_on_feature = min(px_on_feature_h, px_on_feature_v)
    detect_ok = px_on_feature >= req_px
    detect_margin_px = px_on_feature - req_px

    if fit_ok and detect_ok:
        verdict = "ok"
    elif px_on_feature >= 1.0 and fit_ok:
        verdict = "marginal"
    else:
        verdict = "fail"

    roi_coverage = (part_w * part_h) / (fov_x * fov_y) * 100 if fov_x > 0 and fov_y > 0 else 0.0

    return {
        "distance": distance_mm,
        "fov_x": fov_x,
        "fov_y": fov_y,
        "mmpp_h": mmpp_h,
        "mmpp_v": mmpp_v,
        "pxpm_h": pxpm_h,
        "pxpm_v": pxpm_v,
        "fit_ok": fit_ok,
        "detect_ok": detect_ok,
        "fit_margin_pct": fit_margin_pct,
        "detect_margin_px": detect_margin_px,
        "px_on_feature": px_on_feature,
        "px_on_feature_h": px_on_feature_h,
        "px_on_feature_v": px_on_feature_v,
        "roi_coverage_pct": roi_coverage,
        "verdict": verdict,
        "min_feature_1px": min_feature_for_threshold(mmpp_h, 1),
        "min_feature_3px": min_feature_for_threshold(mmpp_h, 3),
        "min_feature_5px": min_feature_for_threshold(mmpp_h, 5),
        "required_fov_x": req_w,
        "required_fov_y": req_h,
    }


def find_valid_distance_range(cam: Dict, part_w: float, part_h: float, feature_mm: float, req_px: float, margin_pct: float, step: int = 10) -> Dict:
    valid = []
    samples = []
    for d in range(int(cam["min_dist"]), int(cam["max_dist"]) + 1, step):
        res = evaluate_application(cam, d, part_w, part_h, feature_mm, req_px, margin_pct)
        samples.append(res)
        if res["fit_ok"] and res["detect_ok"]:
            valid.append(d)

    if not valid:
        return {"valid": False, "min": None, "max": None, "best": None, "samples": samples}

    best = valid[len(valid) // 2]
    return {"valid": True, "min": min(valid), "max": max(valid), "best": best, "samples": samples}


def recommend_cameras(cameras: Dict[str, Dict], preferred_distance: float, part_w: float, part_h: float, feature_mm: float, req_px: float, margin_pct: float, require_color: str) -> pd.DataFrame:
    rows = []
    for name, cam in cameras.items():
        if require_color == "Colour only" and not cam["color"]:
            continue
        if require_color == "Monochrome only" and cam["color"]:
            continue

        range_info = find_valid_distance_range(cam, part_w, part_h, feature_mm, req_px, margin_pct)
        current = evaluate_application(cam, clamp(preferred_distance, cam["min_dist"], cam["max_dist"]), part_w, part_h, feature_mm, req_px, margin_pct)

        if range_info["valid"]:
            best_d = range_info["best"]
            best_eval = evaluate_application(cam, best_d, part_w, part_h, feature_mm, req_px, margin_pct)
            span = range_info["max"] - range_info["min"]
            dist_penalty = abs(best_d - preferred_distance)
            score = 1000 + span + best_eval["detect_margin_px"] * 20 + best_eval["fit_margin_pct"] - dist_penalty * 0.2
            recommendation = "Recommended"
            rank_key = 0
            valid_range = f"{range_info['min']} to {range_info['max']} mm"
        else:
            best_d = None
            best_eval = current
            span = 0
            score = current["detect_margin_px"] * 15 + current["fit_margin_pct"]
            recommendation = "Not ideal"
            rank_key = 1
            valid_range = "No full pass range"

        rows.append(
            {
                "Model": name,
                "Type": cam["type"],
                "Sensor": "Colour" if cam["color"] else "Monochrome",
                "Current Verdict": current["verdict"].upper(),
                "Recommended Range": valid_range,
                "Best Distance (mm)": best_d if best_d is not None else "—",
                "Min Feature @ 3px": round(best_eval["min_feature_3px"], 3),
                "Detection Margin (px)": round(best_eval["detect_margin_px"], 2),
                "Fit Margin (%)": round(best_eval["fit_margin_pct"], 1),
                "Score": round(score, 2),
                "Recommendation": recommendation,
                "_rank_key": rank_key,
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        return df
    return df.sort_values(["_rank_key", "Score"], ascending=[True, False]).drop(columns=["_rank_key"]).reset_index(drop=True)


# ============================================================
# EXPORT HELPERS
# ============================================================
def generate_excel_log(history: List[Dict]) -> bytes:
    output = io.BytesIO()
    df = pd.DataFrame(history)
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Session Log", index=False)
    output.seek(0)
    return output.read()


def generate_pdf_report(report: Dict) -> bytes:
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.pdfgen import canvas
    except Exception as exc:
        raise RuntimeError(
            "PDF export requires reportlab. Install it with: pip install reportlab"
        ) from exc

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    def line(y, text, size=10, color=colors.black, bold=False):
        c.setFillColor(color)
        c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        c.drawString(18 * mm, y, text)

    y = height - 18 * mm
    c.setFillColor(colors.HexColor("#143b63"))
    c.rect(0, height - 30 * mm, width, 30 * mm, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(18 * mm, height - 18 * mm, "Keyence IV4 Engineering Report")
    c.setFont("Helvetica", 9)
    c.drawString(18 * mm, height - 24 * mm, report["created"])

    y = height - 42 * mm
    blocks = [
        ("Project", report["project"] or "—"),
        ("Engineer", report["engineer"] or "—"),
        ("Camera", report["camera"]),
        ("Distance", f"{report['distance']} mm"),
        ("FOV", report["fov"]),
        ("Resolution", report["resolution"]),
        ("Min feature @ 3 px", report["min_feature_3px"]),
        ("Verdict", report["verdict_text"]),
    ]

    c.setStrokeColor(colors.HexColor("#d7e2ee"))
    c.setFillColor(colors.HexColor("#f8fbff"))
    c.roundRect(14 * mm, y - 48 * mm, width - 28 * mm, 52 * mm, 4 * mm, fill=1, stroke=1)

    x1 = 20 * mm
    x2 = 105 * mm
    cur_y1 = y - 4 * mm
    cur_y2 = y - 4 * mm
    for i, (k, v) in enumerate(blocks):
        if i < 4:
            line(cur_y1, f"{k}:", size=9, color=colors.HexColor("#5d748a"), bold=True)
            line(cur_y1 - 5 * mm, str(v), size=11, color=colors.HexColor("#17202a"))
            cur_y1 -= 12 * mm
        else:
            line(cur_y2, f"{k}:", size=9, color=colors.HexColor("#5d748a"), bold=True)
            line(cur_y2 - 5 * mm, str(v), size=11, color=colors.HexColor("#17202a"))
            cur_y2 -= 12 * mm

    y -= 62 * mm
    line(y, "Application Inputs", size=12, color=colors.HexColor("#143b63"), bold=True)
    y -= 8 * mm
    for text in report["application_lines"]:
        line(y, f"• {text}", size=10, color=colors.HexColor("#1f2f3d"))
        y -= 6 * mm

    y -= 4 * mm
    line(y, "Engineering Notes", size=12, color=colors.HexColor("#143b63"), bold=True)
    y -= 8 * mm
    for text in report["notes_lines"]:
        line(y, f"• {text}", size=10, color=colors.HexColor("#1f2f3d"))
        y -= 6 * mm
        if y < 35 * mm:
            c.showPage()
            y = height - 20 * mm

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.read()


# ============================================================
# SPEC TABLE RENDERER
# ============================================================
def spec_value_to_list(value, n: int) -> List[str]:
    if isinstance(value, list):
        return [str(v) for v in value]
    return [str(value) for _ in range(n)]


def build_specs_dataframe(iv4_data: Dict) -> pd.DataFrame:
    rows = []
    models = iv4_data["models"]
    for category, items in iv4_data["categories"].items():
        first = True
        for item_name, item_value in items.items():
            vals = spec_value_to_list(item_value, len(models))
            row = {"Category": category if first else "", "Parameter": item_name}
            for model, val in zip(models, vals):
                row[model] = val
            rows.append(row)
            first = False
    return pd.DataFrame(rows)


def render_specs_html(df: pd.DataFrame, differences_only: bool = False):
    display_df = df.copy()
    if differences_only:
        keep_rows = []
        model_cols = [c for c in display_df.columns if c not in ["Category", "Parameter"]]
        for _, row in display_df.iterrows():
            vals = [str(row[c]).strip() for c in model_cols]
            if row["Category"] or len(set(vals)) > 1:
                keep_rows.append(True)
            else:
                keep_rows.append(False)
        display_df = display_df[keep_rows].reset_index(drop=True)

    model_cols = [c for c in display_df.columns if c not in ["Category", "Parameter"]]
    html = ["<div class='spec-table-wrap'><table class='spec-table'>"]
    html.append("<thead><tr><th>Category</th><th>Parameter</th>")
    for col in model_cols:
        html.append(f"<th>{col}</th>")
    html.append("</tr></thead><tbody>")

    for _, row in display_df.iterrows():
        category_cls = "spec-category" if str(row["Category"]).strip() else ""
        html.append("<tr>")
        html.append(f"<td class='{category_cls}'>{row['Category']}</td>")
        html.append(f"<td>{row['Parameter']}</td>")
        for col in model_cols:
            html.append(f"<td>{str(row[col])}</td>")
        html.append("</tr>")

    html.append("</tbody></table></div>")
    st.markdown("".join(html), unsafe_allow_html=True)


# ============================================================
# CHARTS
# ============================================================
def build_distance_sweep_figure(cam: Dict, part_w: float, part_h: float, feature_mm: float, req_px: float, margin_pct: float, current_distance: float) -> go.Figure:
    distances = list(range(int(cam["min_dist"]), int(cam["max_dist"]) + 1, 25))
    fov_w, min_feature_3px, px_on_feature, fit_pass, det_pass = [], [], [], [], []

    for d in distances:
        res = evaluate_application(cam, d, part_w, part_h, feature_mm, req_px, margin_pct)
        fov_w.append(res["fov_x"])
        min_feature_3px.append(res["min_feature_3px"])
        px_on_feature.append(res["px_on_feature"])
        fit_pass.append(1 if res["fit_ok"] else 0)
        det_pass.append(1 if res["detect_ok"] else 0)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=distances, y=fov_w, mode="lines", name="FOV width (mm)", yaxis="y1"))
    fig.add_trace(go.Scatter(x=distances, y=min_feature_3px, mode="lines", name="Min feature @ 3 px (mm)", yaxis="y2"))
    fig.add_vline(x=current_distance, line_width=2, line_dash="dash", annotation_text="Current")
    fig.update_layout(
        height=360,
        margin=dict(l=20, r=20, t=20, b=20),
        paper_bgcolor="white",
        plot_bgcolor="white",
        legend=dict(orientation="h", y=1.04, x=0),
        yaxis=dict(title="FOV width (mm)", showgrid=True, gridcolor="#edf2f7"),
        yaxis2=dict(title="Min feature @ 3 px (mm)", overlaying="y", side="right"),
        xaxis=dict(title="Distance (mm)", showgrid=False),
    )
    return fig


def build_fov_overlay_figure(eval_res: Dict, part_w: float, part_h: float, roi_w: float, roi_h: float) -> go.Figure:
    fov_x = eval_res["fov_x"]
    fov_y = eval_res["fov_y"]

    half_x = fov_x / 2
    half_y = fov_y / 2
    part_half_x = part_w / 2
    part_half_y = part_h / 2
    roi_half_x = roi_w / 2
    roi_half_y = roi_h / 2

    fig = go.Figure()
    fig.add_shape(type="rect", x0=-half_x, x1=half_x, y0=-half_y, y1=half_y, line=dict(width=2), fillcolor="rgba(11,101,216,0.08)")
    fig.add_shape(type="rect", x0=-part_half_x, x1=part_half_x, y0=-part_half_y, y1=part_half_y, line=dict(width=2), fillcolor="rgba(11,143,77,0.12)")
    fig.add_shape(type="rect", x0=-roi_half_x, x1=roi_half_x, y0=-roi_half_y, y1=roi_half_y, line=dict(width=2, dash="dot"), fillcolor="rgba(199,56,42,0.12)")

    fig.add_annotation(x=0, y=half_y * 1.06, text=f"Full FOV {fov_x:.0f} × {fov_y:.0f} mm", showarrow=False)
    fig.add_annotation(x=0, y=0, text=f"Part {part_w:.0f} × {part_h:.0f} mm", showarrow=False)
    fig.add_annotation(x=0, y=-roi_half_y - 8, text=f"ROI {roi_w:.0f} × {roi_h:.0f} mm", showarrow=False)

    pad = max(fov_x, fov_y) * 0.15
    fig.update_layout(
        height=420,
        margin=dict(l=15, r=15, t=25, b=15),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-half_x - pad, half_x + pad]),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, scaleanchor="x", scaleratio=1, range=[-half_y - pad, half_y + pad]),
        paper_bgcolor="white",
        plot_bgcolor="white",
    )
    return fig


def build_side_view_figure(cam: Dict, eval_res: Dict, part_w: float) -> go.Figure:
    dist = eval_res["distance"]
    fov_x = eval_res["fov_x"]
    half = fov_x / 2
    fig = go.Figure()

    fig.add_shape(type="line", x0=0, x1=0, y0=0, y1=40, line=dict(width=6))
    fig.add_shape(type="line", x0=dist, x1=dist, y0=-half, y1=half, line=dict(width=2, dash="dot"))
    fig.add_shape(type="line", x0=0, x1=dist, y0=0, y1=half, line=dict(width=2))
    fig.add_shape(type="line", x0=0, x1=dist, y0=0, y1=-half, line=dict(width=2))
    fig.add_shape(type="rect", x0=dist - 8, x1=dist + 8, y0=-(part_w / 2), y1=(part_w / 2), line=dict(width=2), fillcolor="rgba(11,143,77,0.15)")
    fig.add_annotation(x=0, y=50, text=cam.get("type", "Camera"), showarrow=False)
    fig.add_annotation(x=dist / 2, y=half + 25, text=f"Distance {dist:.0f} mm", showarrow=False)
    fig.add_annotation(x=dist + 30, y=0, text=f"FOV width {fov_x:.0f} mm", showarrow=False)

    fig.update_layout(
        height=300,
        margin=dict(l=15, r=15, t=20, b=20),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-40, dist + 140]),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-half - 60, half + 60]),
        paper_bgcolor="white",
        plot_bgcolor="white",
    )
    return fig


# ============================================================
# INIT
# ============================================================
if "history" not in st.session_state:
    st.session_state.history = []

cameras = get_camera_data()
iv4_specs = get_iv4_specs_data()
specs_df = build_specs_dataframe(iv4_specs)


# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown("## 📷 IV4 Engineering Tool")
    st.caption("Light layout focused on engineering decisions")

    camera_name = st.selectbox("Selected camera", list(cameras.keys()), index=2)
    cam = cameras[camera_name]

    st.markdown("---")
    st.markdown("### Project")
    project_name = st.text_input("Project / machine", value="")
    engineer_name = st.text_input("Engineer", value="Dejan Rožič")

    st.markdown("---")
    st.markdown("### Application Inputs")
    part_w = st.number_input("Part width (mm)", min_value=1.0, value=120.0, step=1.0)
    part_h = st.number_input("Part height (mm)", min_value=1.0, value=80.0, step=1.0)
    feature_mm = st.number_input("Smallest feature (mm)", min_value=0.01, value=0.40, step=0.01, format="%.2f")
    req_px = st.select_slider("Required pixels on feature", options=[1, 2, 3, 5, 8, 10], value=3)
    margin_pct = st.slider("Part fit margin (%)", min_value=0, max_value=50, value=10, step=1)
    preferred_distance = st.slider(
        "Preferred mounting distance (mm)",
        min_value=int(cam["min_dist"]),
        max_value=int(cam["max_dist"]),
        value=int(clamp(500, cam["min_dist"], cam["max_dist"])),
        step=10,
    )

    st.markdown("---")
    st.markdown("### Optional Filters")
    require_color = st.selectbox("Sensor preference", ["Any", "Colour only", "Monochrome only"], index=0)
    roi_scale = st.slider("ROI as % of part size", min_value=20, max_value=100, value=80, step=5)
    roi_w = part_w * roi_scale / 100.0
    roi_h = part_h * roi_scale / 100.0

    st.markdown("---")
    st.markdown("### Selected Camera")
    st.markdown(f"**Type:** {cam['type']}")
    st.markdown(f"**Sensor:** {'Colour' if cam['color'] else 'Monochrome'}")
    st.markdown(f"**Distance range:** {cam['min_dist']} to {cam['max_dist']} mm")
    st.markdown(f"**Resolution:** {cam['resolution_h']} × {cam['resolution_v']} px")
    st.markdown(f"**Illumination:** {cam['illumination']}")

    image_path = os.path.join(os.getcwd(), PICTURES_FOLDER, cam["image"])
    if os.path.exists(image_path):
        try:
            st.image(Image.open(image_path), caption=camera_name, width="stretch")
        except Exception:
            st.info("Camera image could not be loaded.")
    else:
        st.caption(f"Optional image: /{PICTURES_FOLDER}/{cam['image']}")


# ============================================================
# CORE RESULTS
# ============================================================
current_eval = evaluate_application(cam, preferred_distance, part_w, part_h, feature_mm, req_px, margin_pct)
range_info = find_valid_distance_range(cam, part_w, part_h, feature_mm, req_px, margin_pct)
recommendation_df = recommend_cameras(cameras, preferred_distance, part_w, part_h, feature_mm, req_px, margin_pct, require_color)

if current_eval["verdict"] == "ok":
    verdict_title = "✅ Suitable"
    verdict_class = "ok"
    verdict_text = (
        f"The selected setup fits the part with margin and places approximately {current_eval['px_on_feature']:.2f} px on the smallest feature."
    )
elif current_eval["verdict"] == "marginal":
    verdict_title = "⚠️ Marginal"
    verdict_class = "warn"
    verdict_text = (
        f"The part fits, but the smallest feature is only about {current_eval['px_on_feature']:.2f} px. Use a narrower view, shorter distance, or lower FOV."
    )
else:
    verdict_title = "❌ Not suitable"
    verdict_class = "bad"
    verdict_text = (
        "The current setup does not fully satisfy fit and detection requirements. Check the recommended distance range or choose another model."
    )


# ============================================================
# HEADER
# ============================================================
st.markdown(
    f"""
    <div class="hero">
        <h1>{APP_TITLE}</h1>
        <p>
            Engineering-first sizing workflow for part fit, feature detectability, mounting distance, and model selection.
            Active model: <b>{camera_name}</b>
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

sum_cols = st.columns(5)
with sum_cols[0]:
    summary_card("Selected model", camera_name, cam["type"])
with sum_cols[1]:
    summary_card("Mounting distance", fmt_mm(preferred_distance, 0), f"Range {cam['min_dist']} to {cam['max_dist']} mm")
with sum_cols[2]:
    summary_card("FOV at distance", fmt_pair_mm(current_eval['fov_x'], current_eval['fov_y']), f"Required {fmt_pair_mm(current_eval['required_fov_x'], current_eval['required_fov_y'])}")
with sum_cols[3]:
    summary_card("Resolution", fmt_mm_px(current_eval['mmpp_h']), f"{fmt_px_mm(current_eval['pxpm_h'])} horizontal")
with sum_cols[4]:
    summary_card("Min feature @ 3 px", fmt_mm(current_eval['min_feature_3px'], 3), f"Actual feature ≈ {current_eval['px_on_feature']:.2f} px")

verdict_html(
    verdict_title,
    verdict_text,
    verdict_class,
    badges=[
        (f"Part fit margin {fmt_pct(current_eval['fit_margin_pct'])}", "ok" if current_eval['fit_ok'] else "bad"),
        (f"Detection margin {current_eval['detect_margin_px']:.2f} px", "ok" if current_eval['detect_ok'] else "warn"),
        (f"ROI coverage {fmt_pct(current_eval['roi_coverage_pct'])}", "neutral"),
        (
            f"Recommended range {range_info['min']} to {range_info['max']} mm" if range_info['valid'] else "No full-pass distance range",
            "ok" if range_info['valid'] else "bad",
        ),
    ],
)

with st.expander("Formulas and assumptions"):
    st.markdown(
        """
        <div class="formula">
        <b>FOV interpolation</b>: linear interpolation between the published minimum and maximum installation distance reference values.<br>
        <b>Resolution</b>: mm/px = FOV width ÷ horizontal pixels.<br>
        <b>Feature pixels</b>: feature size × px/mm.<br>
        <b>Practical threshold</b>: 3 px is a common minimum for reliable detection; 5 px is safer for robust inspection; 8–10 px is better for OCR or fine detail.<br>
        <b>Important</b>: real performance still depends on contrast, lighting, focus, depth variation, surface finish, and tool choice.
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# TABS
# ============================================================
overview_tab, sizing_tab, visuals_tab, compare_tab, specs_tab, reports_tab = st.tabs(
    [
        "Overview",
        "Application Sizing",
        "FOV & Visuals",
        "Compare Models",
        "Full Technical Specs",
        "Reports & Export",
    ]
)


# ============================================================
# TAB 1 - OVERVIEW
# ============================================================
with overview_tab:
    left, right = st.columns([1.05, 1.2], gap="large")

    with left:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">Application summary</div>', unsafe_allow_html=True)

        app_df = pd.DataFrame(
            [
                ["Part size", fmt_pair_mm(part_w, part_h)],
                ["Required fit margin", fmt_pct(margin_pct)],
                ["Smallest feature", fmt_mm(feature_mm, 2)],
                ["Required pixels on feature", f"{req_px} px"],
                ["Preferred distance", fmt_mm(preferred_distance, 0)],
                ["Sensor preference", require_color],
            ],
            columns=["Parameter", "Value"],
        )
        st.dataframe(app_df, width="stretch", hide_index=True, height=245)

        st.markdown("##### Engineering verdict")
        st.write(f"- FOV available: **{fmt_pair_mm(current_eval['fov_x'], current_eval['fov_y'])}**")
        st.write(f"- Part fit margin: **{fmt_pct(current_eval['fit_margin_pct'])}**")
        st.write(f"- Feature size on sensor: **{current_eval['px_on_feature']:.2f} px**")
        st.write(f"- Minimum feature for 3 px: **{fmt_mm(current_eval['min_feature_3px'], 3)}**")
        st.write(f"- Minimum feature for 5 px: **{fmt_mm(current_eval['min_feature_5px'], 3)}**")

        if st.button("➕ Log overview decision"):
            log_calculation(
                "Overview",
                {
                    "camera": camera_name,
                    "distance_mm": preferred_distance,
                    "part_w_mm": part_w,
                    "part_h_mm": part_h,
                    "feature_mm": feature_mm,
                    "req_px": req_px,
                    "fit_margin_pct": round(current_eval["fit_margin_pct"], 2),
                    "detect_margin_px": round(current_eval["detect_margin_px"], 2),
                    "verdict": current_eval["verdict"],
                },
            )
            st.success("Overview logged.")
        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">Recommended cameras for this application</div>', unsafe_allow_html=True)
        if recommendation_df.empty:
            st.warning("No models match the current sensor filter.")
        else:
            st.dataframe(
                recommendation_df.drop(columns=["Score"]),
                width="stretch",
                hide_index=True,
                height=300,
            )
            top_model = recommendation_df.iloc[0]["Model"]
            st.caption(f"Top ranked model for the current inputs: {top_model}")
        st.markdown('</div>', unsafe_allow_html=True)

    extra_left, extra_right = st.columns([1, 1], gap="large")
    with extra_left:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">Distance sweep</div>', unsafe_allow_html=True)
        sweep_fig = build_distance_sweep_figure(cam, part_w, part_h, feature_mm, req_px, margin_pct, preferred_distance)
        st.plotly_chart(sweep_fig, width="stretch")
        st.markdown('</div>', unsafe_allow_html=True)

    with extra_right:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">Selected camera quick specs</div>', unsafe_allow_html=True)
        quick_specs = pd.DataFrame(
            [
                ["Model", camera_name],
                ["Type", cam["type"]],
                ["Sensor", cam["sensor"]],
                ["Illumination", cam["illumination"]],
                ["Lighting", cam["lighting"]],
                ["Focus", cam["focus"]],
                ["Programs", cam["programs"]],
                ["Network", cam["network"]],
                ["Transfer", cam["transfer"]],
                ["IP rating", cam["ip_rating"]],
                ["Weight", cam["weight"]],
            ],
            columns=["Parameter", "Value"],
        )
        st.dataframe(quick_specs, width="stretch", hide_index=True, height=360)
        st.markdown('</div>', unsafe_allow_html=True)


# ============================================================
# TAB 2 - APPLICATION SIZING
# ============================================================
with sizing_tab:
    left, right = st.columns([1, 1.2], gap="large")

    with left:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">Current setup checks</div>', unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            summary_card("Required FOV", fmt_pair_mm(current_eval['required_fov_x'], current_eval['required_fov_y']))
            summary_card("Actual FOV", fmt_pair_mm(current_eval['fov_x'], current_eval['fov_y']))
        with c2:
            summary_card("Feature px", f"{current_eval['px_on_feature']:.2f} px", f"Threshold {req_px} px")
            summary_card("Fit margin", fmt_pct(current_eval['fit_margin_pct']))

        fit_status = "Pass" if current_eval["fit_ok"] else "Fail"
        det_status = "Pass" if current_eval["detect_ok"] else "Fail"
        status_df = pd.DataFrame(
            [
                ["Part fits FOV", fit_status],
                ["Feature detectable", det_status],
                ["Recommended distance range", f"{range_info['min']} to {range_info['max']} mm" if range_info['valid'] else "No full pass range"],
                ["Best working distance", f"{range_info['best']} mm" if range_info['valid'] else "—"],
            ],
            columns=["Check", "Result"],
        )
        st.dataframe(status_df, width="stretch", hide_index=True, height=180)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">Suggested engineering actions</div>', unsafe_allow_html=True)
        actions = []
        if not current_eval["fit_ok"]:
            actions.append("Increase FOV by selecting a wider model or increasing mounting distance.")
        if current_eval["fit_ok"] and not current_eval["detect_ok"]:
            actions.append("Reduce distance or move to a narrower field-of-view model to increase pixels on the feature.")
        if current_eval["detect_ok"] and current_eval["fit_margin_pct"] < 10:
            actions.append("Fit margin is low. Add more distance or use a slightly wider model for installation tolerance.")
        if current_eval["detect_ok"] and current_eval["px_on_feature"] < 5:
            actions.append("Detection is acceptable, but 5 px or more is better for robust production conditions.")
        if not actions:
            actions.append("The current setup is solid. Validate lighting, contrast, and mechanical tolerance on the real machine.")
        for item in actions:
            st.write(f"- {item}")
        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">All-model ranking for current part</div>', unsafe_allow_html=True)
        if recommendation_df.empty:
            st.info("No recommendations available.")
        else:
            st.dataframe(recommendation_df, width="stretch", hide_index=True, height=420)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">Detection threshold guide</div>', unsafe_allow_html=True)
        threshold_df = pd.DataFrame(
            {
                "Inspection type": ["Presence / absence", "Basic position", "Reliable detection", "Robust edge / contour", "OCR / small detail"],
                "Typical threshold": ["1–2 px", "2–3 px", "3 px", "5 px", "8–10 px"],
            }
        )
        st.dataframe(threshold_df, width="stretch", hide_index=True, height=215)
        st.markdown('</div>', unsafe_allow_html=True)


# ============================================================
# TAB 3 - FOV & VISUALS
# ============================================================
with visuals_tab:
    top_left, top_right = st.columns([1, 1], gap="large")
    with top_left:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">Scaled top view: full FOV, part, and ROI</div>', unsafe_allow_html=True)
        overlay_fig = build_fov_overlay_figure(current_eval, part_w, part_h, roi_w, roi_h)
        st.plotly_chart(overlay_fig, width="stretch")
        st.caption("Blue = full FOV, green = part envelope, red dashed = ROI.")
        st.markdown('</div>', unsafe_allow_html=True)

    with top_right:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">Side view installation sketch</div>', unsafe_allow_html=True)
        side_fig = build_side_view_figure(cam, current_eval, part_w)
        st.plotly_chart(side_fig, width="stretch")
        st.caption("Simple installation drawing showing mounting distance and viewing cone.")
        st.markdown('</div>', unsafe_allow_html=True)

    bottom_left, bottom_right = st.columns([1, 1], gap="large")
    with bottom_left:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">ROI metrics</div>', unsafe_allow_html=True)
        roi_df = pd.DataFrame(
            [
                ["ROI size", fmt_pair_mm(roi_w, roi_h)],
                ["ROI width in pixels", f"{roi_w * current_eval['pxpm_h']:.0f} px"],
                ["ROI height in pixels", f"{roi_h * current_eval['pxpm_v']:.0f} px"],
                ["ROI coverage of full FOV", fmt_pct((roi_w * roi_h) / (current_eval['fov_x'] * current_eval['fov_y']) * 100)],
            ],
            columns=["Metric", "Value"],
        )
        st.dataframe(roi_df, width="stretch", hide_index=True, height=175)
        st.markdown('</div>', unsafe_allow_html=True)

    with bottom_right:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">Resolution limits at this distance</div>', unsafe_allow_html=True)
        lim_df = pd.DataFrame(
            {
                "Threshold": ["1 px", "3 px", "5 px", "8 px", "10 px"],
                "Minimum feature (H)": [
                    fmt_mm(current_eval['min_feature_1px'], 3),
                    fmt_mm(current_eval['min_feature_3px'], 3),
                    fmt_mm(current_eval['min_feature_5px'], 3),
                    fmt_mm(current_eval['mmpp_h'] * 8, 3),
                    fmt_mm(current_eval['mmpp_h'] * 10, 3),
                ],
            }
        )
        st.dataframe(lim_df, width="stretch", hide_index=True, height=215)
        st.markdown('</div>', unsafe_allow_html=True)


# ============================================================
# TAB 4 - COMPARE MODELS
# ============================================================
with compare_tab:
    c1, c2, c3 = st.columns([1, 1, 1], gap="large")
    with c1:
        cam_a_name = st.selectbox("Camera A", list(cameras.keys()), index=list(cameras.keys()).index(camera_name))
    with c2:
        default_b = 0 if camera_name != list(cameras.keys())[0] else 1
        cam_b_name = st.selectbox("Camera B", list(cameras.keys()), index=default_b)
    with c3:
        mode = st.radio("Comparison mode", ["At same distance", "At target FOV width"], horizontal=False)

    cam_a = cameras[cam_a_name]
    cam_b = cameras[cam_b_name]

    if mode == "At same distance":
        cmp_min = int(max(cam_a["min_dist"], cam_b["min_dist"]))
        cmp_max = int(min(cam_a["max_dist"], cam_b["max_dist"]))
        if cmp_min > cmp_max:
            st.warning("These two models do not share a common valid installation distance range.")
            cmp_distance = max(cam_a["min_dist"], cam_b["min_dist"])
        else:
            cmp_distance = st.slider("Comparison distance (mm)", cmp_min, cmp_max, int(clamp(preferred_distance, cmp_min, cmp_max)), step=10)
        res_a = evaluate_application(cam_a, cmp_distance, part_w, part_h, feature_mm, req_px, margin_pct)
        res_b = evaluate_application(cam_b, cmp_distance, part_w, part_h, feature_mm, req_px, margin_pct)
    else:
        target_fov_x = st.number_input("Target FOV width (mm)", min_value=1.0, value=part_w * (1 + margin_pct / 100.0), step=1.0)
        dist_a = clamp(dist_from_fov(target_fov_x, cam_a), cam_a["min_dist"], cam_a["max_dist"])
        dist_b = clamp(dist_from_fov(target_fov_x, cam_b), cam_b["min_dist"], cam_b["max_dist"])
        res_a = evaluate_application(cam_a, dist_a, part_w, part_h, feature_mm, req_px, margin_pct)
        res_b = evaluate_application(cam_b, dist_b, part_w, part_h, feature_mm, req_px, margin_pct)

    left, right = st.columns(2, gap="large")
    for col, name, camx, resx in [(left, cam_a_name, cam_a, res_a), (right, cam_b_name, cam_b, res_b)]:
        with col:
            st.markdown('<div class="panel">', unsafe_allow_html=True)
            st.markdown(f'<div class="panel-title">{name}</div>', unsafe_allow_html=True)
            top1, top2 = st.columns(2)
            with top1:
                summary_card("Distance", fmt_mm(resx['distance'], 0))
                summary_card("FOV", fmt_pair_mm(resx['fov_x'], resx['fov_y']))
            with top2:
                summary_card("Resolution", fmt_mm_px(resx['mmpp_h']))
                summary_card("Feature px", f"{resx['px_on_feature']:.2f} px")
            compare_df = pd.DataFrame(
                [
                    ["Type", camx["type"]],
                    ["Sensor", "Colour" if camx["color"] else "Monochrome"],
                    ["Illumination", camx["illumination"]],
                    ["Fit margin", fmt_pct(resx["fit_margin_pct"])],
                    ["Detection margin", f"{resx['detect_margin_px']:.2f} px"],
                    ["Min feature @ 3 px", fmt_mm(resx['min_feature_3px'], 3)],
                ],
                columns=["Parameter", "Value"],
            )
            st.dataframe(compare_df, width="stretch", hide_index=True, height=220)
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">Comparison chart</div>', unsafe_allow_html=True)
    cmp_fig = go.Figure()
    metrics = ["FOV width (mm)", "FOV height (mm)", "Feature px", "Fit margin (%)"]
    cmp_fig.add_trace(go.Bar(name=cam_a_name, x=metrics, y=[res_a['fov_x'], res_a['fov_y'], res_a['px_on_feature'], res_a['fit_margin_pct']]))
    cmp_fig.add_trace(go.Bar(name=cam_b_name, x=metrics, y=[res_b['fov_x'], res_b['fov_y'], res_b['px_on_feature'], res_b['fit_margin_pct']]))
    cmp_fig.update_layout(height=320, barmode="group", paper_bgcolor="white", plot_bgcolor="white", margin=dict(l=20, r=20, t=10, b=20), legend=dict(orientation="h", y=1.05, x=0))
    st.plotly_chart(cmp_fig, width="stretch")
    st.markdown('</div>', unsafe_allow_html=True)


# ============================================================
# TAB 5 - FULL TECHNICAL SPECS
# ============================================================
with specs_tab:
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">Full comparison table</div>', unsafe_allow_html=True)
    differences_only = st.checkbox("Show only rows that differ between models", value=False)
    render_specs_html(specs_df, differences_only=differences_only)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown('<div class="panel-title">Footnotes</div>', unsafe_allow_html=True)
    for note in iv4_specs["footnotes"]:
        st.write(f"- {note}")
    st.markdown('</div>', unsafe_allow_html=True)


# ============================================================
# TAB 6 - REPORTS & EXPORT
# ============================================================
with reports_tab:
    rep_left, rep_right = st.columns([1, 1], gap="large")

    with rep_left:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">Generate engineering PDF report</div>', unsafe_allow_html=True)
        extra_notes = st.text_area("Additional notes", height=110, value="")

                recommended_range_text = (
            f"{range_info['min']} to {range_info['max']} mm" if range_info["valid"] else "No full pass range"
        )

        report_payload = {
            "created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "project": project_name,
            "engineer": engineer_name,
            "camera": camera_name,
            "distance": int(preferred_distance),
            "fov": fmt_pair_mm(current_eval["fov_x"], current_eval["fov_y"]),
            "resolution": fmt_mm_px(current_eval["mmpp_h"]),
            "min_feature_3px": fmt_mm(current_eval["min_feature_3px"], 3),
            "verdict_text": verdict_title.replace("✅ ", "").replace("⚠️ ", "").replace("❌ ", ""),
            "application_lines": [
                f"Part size: {fmt_pair_mm(part_w, part_h)}",
                f"Smallest feature: {fmt_mm(feature_mm, 2)}",
                f"Required pixels on feature: {req_px} px",
                f"Required fit margin: {fmt_pct(margin_pct)}",
                f"Recommended range: {recommended_range_text}",
            ],
            "notes_lines": [
                f"Fit margin at selected distance: {fmt_pct(current_eval['fit_margin_pct'])}",
                f"Feature size on sensor: {current_eval['px_on_feature']:.2f} px",
                f"Detection margin: {current_eval['detect_margin_px']:.2f} px",
                f"ROI coverage: {fmt_pct(current_eval['roi_coverage_pct'])}",
            ] + ([extra_notes] if extra_notes.strip() else []),
        }

        pdf_error = None
        pdf_bytes = None
        try:
            pdf_bytes = generate_pdf_report(report_payload)
        except Exception as exc:
            pdf_error = str(exc)

        if pdf_error:
            st.warning(pdf_error)
        else:
            st.download_button(
                "Download PDF report",
                data=pdf_bytes,
                file_name=f"IV4_Report_{camera_name}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                mime="application/pdf",
            )
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">Export current recommendation table</div>', unsafe_allow_html=True)
        if not recommendation_df.empty:
            xlsx_table = io.BytesIO()
            with pd.ExcelWriter(xlsx_table, engine="openpyxl") as writer:
                recommendation_df.to_excel(writer, index=False, sheet_name="Recommendations")
            xlsx_table.seek(0)
            st.download_button(
                "Download recommendations (.xlsx)",
                data=xlsx_table.getvalue(),
                file_name=f"IV4_Recommendations_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            st.download_button(
                "Download recommendations (.csv)",
                data=recommendation_df.to_csv(index=False).encode("utf-8"),
                file_name=f"IV4_Recommendations_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
            )
        st.markdown('</div>', unsafe_allow_html=True)

    with rep_right:
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">Session log</div>', unsafe_allow_html=True)
        history_count = len(st.session_state.history)
        if history_count == 0:
            st.info("No entries logged yet. Use the log buttons from the other tabs.")
        else:
            hist_df = pd.DataFrame(st.session_state.history)
            st.dataframe(hist_df, width="stretch", hide_index=True, height=380)
            st.download_button(
                "Download session log (.xlsx)",
                data=generate_excel_log(st.session_state.history),
                file_name=f"IV4_SessionLog_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
            st.download_button(
                "Download session log (.csv)",
                data=hist_df.to_csv(index=False).encode("utf-8"),
                file_name=f"IV4_SessionLog_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
            )
            if st.button("Clear session log"):
                st.session_state.history = []
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown('<div class="panel-title">Implementation note</div>', unsafe_allow_html=True)
        st.write("- This version is intentionally light and engineering-focused.")
        st.write("- The full specs table is now easier to compare and supports 'differences only'.")
        st.write("- The app now starts from the part and feature, then recommends a camera and working distance.")
        st.write("- You can later split this single file into modules once the layout is stable.")
        st.markdown('</div>', unsafe_allow_html=True)


# ============================================================
# FOOTER
# ============================================================
st.markdown("<div class='footer'>Keyence IV4 Smart Camera Engineering Tool · Light engineering layout · Made for fast fit / detectability decisions</div>", unsafe_allow_html=True)
