import os
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from PIL import Image

from report_generator import generate_excel_log, generate_pdf_report

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
PICTURES_FOLDER = "Pictures"

st.set_page_config(
    page_title="Keyence IV3 Camera Calculator",
    layout="wide",
    page_icon="🔍",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600;700&display=swap');

    html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }

    [data-testid="stSidebar"] { background: #0f1117; }
    [data-testid="stSidebar"] * { color: #e0e0e0 !important; }
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] p { color: #a0a0a0 !important; font-size: 0.8rem !important; }

    .metric-card {
        background: #f8f9fa; border: 1px solid #e0e0e0;
        border-left: 4px solid #1a73e8; border-radius: 6px;
        padding: 14px 18px; margin-bottom: 10px;
    }
    .metric-card.green  { border-left-color: #0d9c50; }
    .metric-card.orange { border-left-color: #e87e1a; }
    .metric-card.red    { border-left-color: #d93025; }
    .metric-card.blue   { border-left-color: #1a73e8; }
    .metric-label {
        font-size: 0.72rem; color: #666;
        text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 2px;
    }
    .metric-value {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 1.35rem; font-weight: 600; color: #111;
    }
    .metric-unit { font-size: 0.75rem; color: #888; margin-left: 4px; }

    .section-header {
        font-size: 0.68rem; font-weight: 700;
        text-transform: uppercase; letter-spacing: 0.12em; color: #888;
        border-bottom: 1px solid #e0e0e0; padding-bottom: 4px; margin: 18px 0 12px 0;
    }
    .detect-yes {
        background: #e6f4ea; border: 1px solid #0d9c50; border-radius: 6px;
        padding: 12px 18px; color: #0d5e30; font-weight: 600; margin-top: 10px;
    }
    .detect-no {
        background: #fce8e6; border: 1px solid #d93025; border-radius: 6px;
        padding: 12px 18px; color: #7f1e17; font-weight: 600; margin-top: 10px;
    }
    .detect-marginal {
        background: #fef7e0; border: 1px solid #e8940a; border-radius: 6px;
        padding: 12px 18px; color: #7f4b00; font-weight: 600; margin-top: 10px;
    }
    .report-box {
        background: linear-gradient(135deg, #0d1b2a 0%, #1a3a5c 100%);
        border-radius: 10px; padding: 24px 28px; color: white; margin-bottom: 18px;
    }
    .report-box h3 { margin: 0 0 6px 0; font-size: 1.1rem; }
    .report-box p  { margin: 0; font-size: 0.82rem; color: #aac8f0; }
    .history-badge {
        display: inline-block; background: #1a73e8; color: white;
        border-radius: 12px; padding: 2px 10px;
        font-size: 0.72rem; font-weight: 700; margin-left: 6px;
    }
    .footer {
        position: fixed; bottom: 0; left: 0; width: 100%;
        background: white; border-top: 1px solid #e6e6e6;
        padding: 6px 0; text-align: center;
        font-size: 0.75rem; color: #888; z-index: 999;
    }
    .stTabs [data-baseweb="tab"] {
        font-family: 'IBM Plex Sans', sans-serif;
        font-weight: 600; font-size: 0.85rem;
    }
    [data-testid="stNumberInput"] label,
    [data-testid="stSlider"] label {
        font-size: 0.8rem !important; font-weight: 600 !important; color: #444 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def clamp(value, lo, hi):
    return max(lo, min(hi, value))

def lerp(v, in0, in1, out0, out1):
    if (in1 - in0) == 0:
        return float(out0)
    return float(out0 + (v - in0) * (out1 - out0) / (in1 - in0))

def fov_from_dist(dist, cam):
    fx = lerp(dist, cam["min_dist"], cam["max_dist"], cam["min_fov_x"], cam["max_fov_x"])
    fy = lerp(dist, cam["min_dist"], cam["max_dist"], cam["min_fov_y"], cam["max_fov_y"])
    return fx, fy

def dist_from_fov(fov_x, cam):
    return lerp(fov_x, cam["min_fov_x"], cam["max_fov_x"], cam["min_dist"], cam["max_dist"])

def resolution_metrics(fov_mm, pixels):
    if pixels <= 0 or fov_mm <= 0:
        return 0.0, 0.0
    mpp = fov_mm / pixels
    return mpp, 1.0 / mpp

def metric_card(label, value, unit="", color="blue"):
    st.markdown(
        f'<div class="metric-card {color}">'
        f'<div class="metric-label">{label}</div>'
        f'<div class="metric-value">{value}<span class="metric-unit">{unit}</span></div>'
        f'</div>',
        unsafe_allow_html=True,
    )

def section(title):
    st.markdown(f'<div class="section-header">{title}</div>', unsafe_allow_html=True)

def log_calculation(label: str, data: dict):
    """Append a row to session history."""
    if "history" not in st.session_state:
        st.session_state.history = []
    row = {"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "type": label}
    row.update(data)
    st.session_state.history.append(row)


# ─────────────────────────────────────────────
# CAMERA DATA
# ─────────────────────────────────────────────
@st.cache_data
def get_camera_data():
    return {
        "IV3-G500CA": {
            "image": "iv4-g500ca.png",
            "min_fov_x": 22, "max_fov_x": 1184,
            "min_fov_y": 16, "max_fov_y": 888,
            "min_dist": 50,  "max_dist": 3000,
            "resolution_h": 1280, "resolution_v": 960,
            "color": True,
            "specs": {
                "Type": "Standard",
                "Installed Distance": "50 mm or more",
                "FOV @ 50 mm": "22 × 16 mm",
                "FOV @ 3000 mm": "1184 × 888 mm",
                "Image Sensor": '1/2.9" colour CMOS',
                "Resolution": "1280 × 960 px",
                "Focus": "Auto",
                "Exposure": "12 μs – 9 ms",
                "Illumination": "White LED",
                "Lighting": "Pulse / continuous switchable",
                "IP Rating": "IP67",
                "Temp. Range": "0 – +50 °C",
                "Humidity": "35 – 85 % RH",
                "Weight": "≈ 75 g",
            },
        },
        "IV3-G600MA": {
            "image": "iv4-g600ca.png",
            "min_fov_x": 51, "max_fov_x": 2730,
            "min_fov_y": 38, "max_fov_y": 2044,
            "min_dist": 50,  "max_dist": 3000,
            "resolution_h": 1280, "resolution_v": 960,
            "color": False,
            "specs": {
                "Type": "Wide view",
                "Installed Distance": "50 mm or more",
                "FOV @ 50 mm": "51 × 38 mm",
                "FOV @ 3000 mm": "2730 × 2044 mm",
                "Image Sensor": '1/2.9" monochrome CMOS',
                "Resolution": "1280 × 960 px",
                "Focus": "Auto",
                "Exposure": "12 μs – 9 ms",
                "Illumination": "Infrared LED",
                "Lighting": "Pulse lighting",
                "IP Rating": "IP67",
                "Temp. Range": "0 – +50 °C",
                "Weight": "≈ 75 g",
            },
        },
        "IV3-400CA": {
            "image": "iv4-g600ca.png",
            "min_fov_x": 58, "max_fov_x": 464,
            "min_fov_y": 44, "max_fov_y": 348,
            "min_dist": 400, "max_dist": 3000,
            "resolution_h": 1280, "resolution_v": 960,
            "color": True,
            "specs": {
                "Type": "Narrow view",
                "Installed Distance": "400 mm or more",
                "FOV @ 400 mm": "58 × 44 mm",
                "FOV @ 3000 mm": "464 × 348 mm",
                "Image Sensor": '1/2.9" colour CMOS',
                "Resolution": "1280 × 960 px",
                "Focus": "Auto",
                "Exposure": "12 μs – 10 ms",
                "Illumination": "White LED",
                "Lighting": "Pulse / continuous switchable",
                "Network": "EtherNet/IP, PROFINET, TCP/IP",
                "Programs": "128 (SD) / 32 (no SD)",
                "IP Rating": "IP67",
                "Temp. Range": "0 – +50 °C",
                "Weight": "≈ 300 g",
            },
        },
    }


# ─────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────
if "history" not in st.session_state:
    st.session_state.history = []


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
cameras     = get_camera_data()

with st.sidebar:
    st.markdown("### 🔍 Keyence IV3 Series")
    st.markdown("---")
    camera_name = st.selectbox("Camera Model", list(cameras.keys()))
    cam         = cameras[camera_name]

    st.markdown("---")
    section("SENSOR SPECS")
    st.markdown(f"**Resolution:** {cam['resolution_h']} × {cam['resolution_v']} px")
    st.markdown(f"**Colour:** {'Yes ✅' if cam['color'] else 'No (Mono)'}")
    st.markdown(f"**Min dist:** {cam['min_dist']} mm")
    st.markdown(f"**Max dist:** {cam['max_dist']} mm")

    st.markdown("---")
    image_path = os.path.join(os.getcwd(), PICTURES_FOLDER, cam["image"])
    if os.path.exists(image_path):
        try:
            st.image(Image.open(image_path), caption=camera_name, use_container_width=True)
        except Exception:
            st.info("Image unavailable")
    else:
        st.info(f"📷 Place '{cam['image']}' in /{PICTURES_FOLDER}/")

    st.markdown("---")
    history_count = len(st.session_state.history)
    st.markdown(
        f"**Session log:** {history_count} entr{'y' if history_count==1 else 'ies'}",
        help="Go to the 📊 Reports tab to export or view.",
    )
    st.markdown("<small>Made by Dejan Rožič</small>", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# MAIN HEADER
# ─────────────────────────────────────────────
st.title("🔍 Keyence IV3 Camera Calculator")
st.markdown(
    f"<span style='color:#888;font-size:0.9rem;'>Active: <b>{camera_name}</b> — "
    f"{cam['resolution_h']}×{cam['resolution_v']} px&nbsp;|&nbsp;"
    f"FOV: {cam['min_fov_x']}–{cam['max_fov_x']} mm (H)</span>",
    unsafe_allow_html=True,
)
st.markdown("")


# ─────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📐 FOV & Distance",
    "🔲 ROI Analysis",
    "🎯 Feature Detection",
    "⚖️ Compare Cameras",
    "📊 Reports & Export",
])


# ══════════════════════════════════════════════════════════════════
# TAB 1 — FOV & Distance
# ══════════════════════════════════════════════════════════════════
with tab1:
    col_calc, col_vis = st.columns([1, 1], gap="large")

    with col_calc:
        section("MOUNTING DISTANCE → FOV")
        distance = st.slider(
            "Mounting Distance (mm)",
            min_value=int(cam["min_dist"]), max_value=int(cam["max_dist"]),
            value=int(clamp(500, cam["min_dist"], cam["max_dist"])),
            step=10, key="dist_slider",
        )
        fov_x, fov_y = fov_from_dist(distance, cam)
        mpp_h, ppm_h = resolution_metrics(fov_x, cam["resolution_h"])
        mpp_v, ppm_v = resolution_metrics(fov_y, cam["resolution_v"])

        c1, c2 = st.columns(2)
        with c1:
            metric_card("FOV Horizontal",  f"{fov_x:.1f}", "mm",    "blue")
            metric_card("Resolution H",    f"{mpp_h:.4f}", "mm/px", "green")
            metric_card("Resolution H",    f"{ppm_h:.2f}", "px/mm", "green")
        with c2:
            metric_card("FOV Vertical",    f"{fov_y:.1f}", "mm",    "blue")
            metric_card("Resolution V",    f"{mpp_v:.4f}", "mm/px", "orange")
            metric_card("Resolution V",    f"{ppm_v:.2f}", "px/mm", "orange")

        if st.button("➕ Log this calculation", key="log_fov"):
            log_calculation("FOV", {
                "camera": camera_name, "distance_mm": distance,
                "fov_h_mm": round(fov_x, 2), "fov_v_mm": round(fov_y, 2),
                "res_h_mm_px": round(mpp_h, 4), "res_v_mm_px": round(mpp_v, 4),
            })
            st.success("Logged ✓")

        st.markdown("")
        section("TARGET FOV → REQUIRED DISTANCE")
        target_h = st.number_input(
            "Target Horizontal FOV (mm)",
            min_value=float(cam["min_fov_x"]), max_value=float(cam["max_fov_x"]),
            value=float(clamp(200, cam["min_fov_x"], cam["max_fov_x"])),
            step=5.0, key="target_h",
        )
        req_dist = dist_from_fov(target_h, cam)
        metric_card("Required Mounting Distance", f"{req_dist:.1f}", "mm", "blue")

        st.markdown("")
        section("MANUAL RESOLUTION CHECK")
        m1, m2 = st.columns(2)
        with m1:
            man_fov_h = st.number_input(
                "Actual FOV Width (mm)",
                min_value=float(cam["min_fov_x"]), max_value=float(cam["max_fov_x"]),
                value=float(clamp(100, cam["min_fov_x"], cam["max_fov_x"])),
                step=1.0, key="man_h",
            )
        with m2:
            man_fov_v = st.number_input(
                "Actual FOV Height (mm)",
                min_value=float(cam["min_fov_y"]), max_value=float(cam["max_fov_y"]),
                value=float(clamp(100, cam["min_fov_y"], cam["max_fov_y"])),
                step=1.0, key="man_v",
            )
        mm_h, px_h = resolution_metrics(man_fov_h, cam["resolution_h"])
        mm_v, px_v = resolution_metrics(man_fov_v, cam["resolution_v"])
        r1, r2, r3, r4 = st.columns(4)
        with r1: metric_card("H mm/px", f"{mm_h:.4f}", "", "green")
        with r2: metric_card("H px/mm", f"{px_h:.2f}",  "", "green")
        with r3: metric_card("V mm/px", f"{mm_v:.4f}", "", "orange")
        with r4: metric_card("V px/mm", f"{px_v:.2f}",  "", "orange")

    with col_vis:
        section("FOV GEOMETRY DIAGRAM")
        half_w = fov_x / 2
        fig = go.Figure()
        fig.add_shape(type="rect", x0=-half_w, x1=half_w, y0=0, y1=fov_y,
                      fillcolor="rgba(26,115,232,0.10)", line=dict(color="#1a73e8", width=2))
        bw = fov_x * 0.04
        fig.add_shape(type="rect", x0=-bw, x1=bw, y0=fov_y, y1=fov_y + fov_y * 0.08,
                      fillcolor="#444", line=dict(color="#222", width=1))
        arr = 1.5
        dim_x = half_w * 1.18
        fig.add_shape(type="line", x0=dim_x, x1=dim_x, y0=0, y1=fov_y,
                      line=dict(color="#e87e1a", width=1.5))
        fig.add_annotation(x=0, y=-fov_y * 0.06, text=f"← {fov_x:.1f} mm (H) →",
                           showarrow=False, font=dict(size=12, color="#1a73e8"))
        fig.add_annotation(x=-half_w * 1.18, y=fov_y / 2, text=f"{fov_y:.1f} mm (V)",
                           showarrow=False, font=dict(size=12, color="#1a73e8"), textangle=-90)
        fig.add_annotation(x=dim_x + fov_x * 0.06, y=fov_y / 2, text=f"{distance} mm",
                           showarrow=False, font=dict(size=11, color="#e87e1a"))
        fig.update_layout(
            height=320, margin=dict(l=20, r=60, t=20, b=40),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False,
                       range=[-fov_x * 0.75, fov_x * 0.75]),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False,
                       scaleanchor="x", scaleratio=1,
                       range=[-fov_y * 0.15, fov_y * 1.15]),
            plot_bgcolor="white", paper_bgcolor="white",
        )
        st.plotly_chart(fig, use_container_width=True)

        section("CAMERA SPECIFICATIONS")
        df_specs = pd.DataFrame(cam["specs"].items(), columns=["Parameter", "Value"])
        st.dataframe(df_specs, use_container_width=True, hide_index=True, height=280)


# ══════════════════════════════════════════════════════════════════
# TAB 2 — ROI Analysis
# ══════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("Define a **Region of Interest (ROI)** within the camera's FOV.")

    col_roi_in, col_roi_out = st.columns([1, 1], gap="large")
    with col_roi_in:
        section("MOUNTING DISTANCE")
        roi_dist = st.slider(
            "Mounting Distance (mm)",
            min_value=int(cam["min_dist"]), max_value=int(cam["max_dist"]),
            value=int(clamp(500, cam["min_dist"], cam["max_dist"])),
            step=10, key="roi_dist",
        )
        fov_x_roi, fov_y_roi = fov_from_dist(roi_dist, cam)
        metric_card("Full FOV (H × V)", f"{fov_x_roi:.1f} × {fov_y_roi:.1f}", "mm", "blue")

        section("ROI SIZE")
        roi_w = st.number_input("ROI Width (mm)", min_value=1.0, max_value=float(fov_x_roi),
                                value=float(clamp(fov_x_roi * 0.5, 1, fov_x_roi)), step=1.0, key="roi_w")
        roi_h = st.number_input("ROI Height (mm)", min_value=1.0, max_value=float(fov_y_roi),
                                value=float(clamp(fov_y_roi * 0.5, 1, fov_y_roi)), step=1.0, key="roi_h")

        section("ROI POSITION (offset from FOV centre)")
        max_off_x = max(0.0, (fov_x_roi - roi_w) / 2)
        max_off_y = max(0.0, (fov_y_roi - roi_h) / 2)
        roi_x_off = st.slider("Horizontal offset (mm)", min_value=-max_off_x, max_value=max_off_x,
                              value=0.0, step=0.5, key="roi_x_off", disabled=(roi_w >= fov_x_roi))
        roi_y_off = st.slider("Vertical offset (mm)",   min_value=-max_off_y, max_value=max_off_y,
                              value=0.0, step=0.5, key="roi_y_off", disabled=(roi_h >= fov_y_roi))

    with col_roi_out:
        ppm_h_roi = cam["resolution_h"] / fov_x_roi
        ppm_v_roi = cam["resolution_v"] / fov_y_roi
        roi_px_h  = roi_w * ppm_h_roi
        roi_px_v  = roi_h * ppm_v_roi
        roi_cov   = (roi_w * roi_h) / (fov_x_roi * fov_y_roi) * 100

        section("ROI RESOLUTION METRICS")
        c1, c2 = st.columns(2)
        with c1:
            metric_card("ROI Width (px)",   f"{roi_px_h:.0f}", "px", "blue")
            metric_card("ROI Height (px)",  f"{roi_px_v:.0f}", "px", "blue")
            metric_card("Total ROI Pixels", f"{roi_px_h*roi_px_v/1e6:.2f}", "MP", "green")
        with c2:
            metric_card("Resolution H",  f"{1/ppm_h_roi:.4f}", "mm/px", "orange")
            metric_card("Resolution V",  f"{1/ppm_v_roi:.4f}", "mm/px", "orange")
            metric_card("ROI Coverage",  f"{roi_cov:.1f}", "% of FOV", "blue")

        if st.button("➕ Log ROI", key="log_roi"):
            log_calculation("ROI", {
                "camera": camera_name, "distance_mm": roi_dist,
                "fov_h": round(fov_x_roi, 2), "fov_v": round(fov_y_roi, 2),
                "roi_w_mm": round(roi_w, 2), "roi_h_mm": round(roi_h, 2),
                "roi_px_h": round(roi_px_h), "roi_px_v": round(roi_px_v),
                "roi_coverage_pct": round(roi_cov, 1),
            })
            st.success("Logged ✓")

        section("FOV + ROI DIAGRAM")
        hfx, hfy = fov_x_roi / 2, fov_y_roi / 2
        rx0, rx1 = roi_x_off - roi_w/2, roi_x_off + roi_w/2
        ry0, ry1 = roi_y_off - roi_h/2, roi_y_off + roi_h/2
        fig2 = go.Figure()
        fig2.add_shape(type="rect", x0=-hfx, x1=hfx, y0=-hfy, y1=hfy,
                       fillcolor="rgba(26,115,232,0.07)", line=dict(color="#1a73e8", width=2, dash="dot"))
        fig2.add_annotation(x=0, y=hfy*1.07, text=f"FOV  {fov_x_roi:.0f}×{fov_y_roi:.0f} mm",
                            showarrow=False, font=dict(size=11, color="#1a73e8"))
        fig2.add_shape(type="rect", x0=rx0, x1=rx1, y0=ry0, y1=ry1,
                       fillcolor="rgba(217,48,37,0.18)", line=dict(color="#d93025", width=2))
        fig2.add_annotation(x=(rx0+rx1)/2, y=(ry0+ry1)/2,
                            text=f"ROI<br>{roi_w:.0f}×{roi_h:.0f} mm<br>{roi_px_h:.0f}×{roi_px_v:.0f} px",
                            showarrow=False, font=dict(size=10, color="#7f1e17"),
                            bgcolor="rgba(255,255,255,0.75)", bordercolor="#d93025", borderwidth=1)
        pad = max(fov_x_roi, fov_y_roi) * 0.12
        fig2.update_layout(
            height=360, margin=dict(l=10, r=10, t=30, b=10),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False,
                       range=[-hfx-pad, hfx+pad]),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False,
                       scaleanchor="x", scaleratio=1, range=[-hfy-pad, hfy+pad]),
            plot_bgcolor="white", paper_bgcolor="white",
        )
        st.plotly_chart(fig2, use_container_width=True)


# ══════════════════════════════════════════════════════════════════
# TAB 3 — Feature Detection
# ══════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("Check whether the selected camera can resolve a given feature size.")

    col_fd1, col_fd2 = st.columns([1, 1], gap="large")
    with col_fd1:
        section("SETUP")
        fd_dist = st.slider(
            "Mounting Distance (mm)",
            min_value=int(cam["min_dist"]), max_value=int(cam["max_dist"]),
            value=int(clamp(500, cam["min_dist"], cam["max_dist"])),
            step=10, key="fd_dist",
        )
        fov_x_fd, fov_y_fd = fov_from_dist(fd_dist, cam)

        section("FEATURE TO DETECT")
        feature_size = st.number_input(
            "Minimum Feature Size (mm)",
            min_value=0.001, max_value=500.0, value=0.5, step=0.01,
            format="%.3f", key="feature_size",
        )
        reliability_px = st.select_slider(
            "Required pixels per feature",
            options=[1, 2, 3, 5, 10], value=3, key="rel_px",
            help="3–5 px per feature is the industry minimum for reliable detection.",
        )

    with col_fd2:
        mpp_h_fd, ppm_h_fd = resolution_metrics(fov_x_fd, cam["resolution_h"])
        mpp_v_fd, ppm_v_fd = resolution_metrics(fov_y_fd, cam["resolution_v"])
        px_on_h = feature_size * ppm_h_fd
        px_on_v = feature_size * ppm_v_fd
        min_px  = min(px_on_h, px_on_v)

        section("RESOLUTION AT THIS DISTANCE")
        c1, c2 = st.columns(2)
        with c1:
            metric_card("FOV H",         f"{fov_x_fd:.1f}", "mm",    "blue")
            metric_card("Resolution H",  f"{mpp_h_fd:.4f}", "mm/px", "orange")
        with c2:
            metric_card("FOV V",         f"{fov_y_fd:.1f}", "mm",    "blue")
            metric_card("Resolution V",  f"{mpp_v_fd:.4f}", "mm/px", "orange")

        section("DETECTION RESULT")
        metric_card("Pixels on Feature (H)", f"{px_on_h:.1f}", "px", "green")
        metric_card("Pixels on Feature (V)", f"{px_on_v:.1f}", "px", "green")

        if min_px >= reliability_px:
            verdict_key = "ok"
            st.markdown(
                f'<div class="detect-yes">✅ <b>DETECTABLE</b> — {min_px:.1f} px cover the feature '
                f'(threshold: {reliability_px} px). Detection is reliable.</div>',
                unsafe_allow_html=True,
            )
        elif min_px >= 1.0:
            verdict_key = "marginal"
            st.markdown(
                f'<div class="detect-marginal">⚠️ <b>MARGINAL</b> — Only {min_px:.1f} px cover the feature '
                f'(threshold: {reliability_px} px). Detection may be unreliable.</div>',
                unsafe_allow_html=True,
            )
        else:
            verdict_key = "fail"
            st.markdown(
                f'<div class="detect-no">❌ <b>NOT DETECTABLE</b> — Feature is sub-pixel '
                f'({min_px:.3f} px). Min detectable: <b>{mpp_h_fd:.4f} mm</b> (1 px), '
                f'<b>{mpp_h_fd*3:.4f} mm</b> (3 px).</div>',
                unsafe_allow_html=True,
            )

        if st.button("➕ Log detection result", key="log_detect"):
            log_calculation("Detection", {
                "camera": camera_name, "distance_mm": fd_dist,
                "feature_size_mm": feature_size, "pixels_on_feature": round(min_px, 2),
                "verdict": verdict_key, "reliability_threshold_px": reliability_px,
            })
            st.success("Logged ✓")

        st.markdown("")
        section("DETECTION LIMITS AT THIS DISTANCE")
        limits_df = pd.DataFrame({
            "Threshold": ["1 px (theoretical)", "3 px (good)", "5 px (robust)"],
            "Min Feature H": [f"{mpp_h_fd*1:.4f} mm", f"{mpp_h_fd*3:.4f} mm", f"{mpp_h_fd*5:.4f} mm"],
            "Min Feature V": [f"{mpp_v_fd*1:.4f} mm", f"{mpp_v_fd*3:.4f} mm", f"{mpp_v_fd*5:.4f} mm"],
        })
        st.dataframe(limits_df, use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════
# TAB 4 — Compare Cameras
# ══════════════════════════════════════════════════════════════════
with tab4:
    st.markdown("Compare two camera models at the same mounting distance.")
    cc1, cc2, cc3 = st.columns([1, 1, 1])
    with cc1:
        cam_a_name = st.selectbox("Camera A", list(cameras.keys()), index=0, key="cmp_a")
    with cc2:
        cam_b_name = st.selectbox("Camera B", list(cameras.keys()), index=1, key="cmp_b")
    with cc3:
        cam_a_d = cameras[cam_a_name]
        cam_b_d = cameras[cam_b_name]
        cmp_min = max(cam_a_d["min_dist"], cam_b_d["min_dist"])
        cmp_max = min(cam_a_d["max_dist"], cam_b_d["max_dist"])
        if cmp_min > cmp_max:
            st.warning("No overlapping distance range.")
            cmp_dist = cmp_min
        else:
            cmp_dist = st.slider("Comparison Distance (mm)", int(cmp_min), int(cmp_max),
                                 int(clamp(500, cmp_min, cmp_max)), step=10, key="cmp_dist")

    fov_xa, fov_ya = fov_from_dist(cmp_dist, cam_a_d)
    fov_xb, fov_yb = fov_from_dist(cmp_dist, cam_b_d)
    mpp_ha, ppm_ha = resolution_metrics(fov_xa, cam_a_d["resolution_h"])
    mpp_hb, ppm_hb = resolution_metrics(fov_xb, cam_b_d["resolution_h"])

    col_a, col_b = st.columns(2, gap="large")
    for col, cn, fx, fy, mp, cd in [
        (col_a, cam_a_name, fov_xa, fov_ya, mpp_ha, cam_a_d),
        (col_b, cam_b_name, fov_xb, fov_yb, mpp_hb, cam_b_d),
    ]:
        with col:
            st.markdown(f"#### {cn}")
            metric_card("FOV Horizontal",  f"{fx:.1f}", "mm", "blue")
            metric_card("FOV Vertical",    f"{fy:.1f}", "mm", "blue")
            metric_card("Resolution H",    f"{mp:.4f}", "mm/px", "green")
            metric_card("Sensor",          "Colour" if cd["color"] else "Monochrome", "", "orange")
            metric_card("Resolution",      f"{cd['resolution_h']}×{cd['resolution_v']}", "px", "blue")

    section("SIDE-BY-SIDE COMPARISON CHART")
    fig3 = go.Figure()
    labels = ["FOV H (mm)", "FOV V (mm)", "mm/px (H) ×1000"]
    fig3.add_trace(go.Bar(name=cam_a_name, x=labels, y=[fov_xa, fov_ya, mpp_ha*1000], marker_color="#1a73e8"))
    fig3.add_trace(go.Bar(name=cam_b_name, x=labels, y=[fov_xb, fov_yb, mpp_hb*1000], marker_color="#d93025"))
    fig3.update_layout(
        barmode="group", height=300,
        margin=dict(l=10, r=10, t=10, b=30),
        plot_bgcolor="white", paper_bgcolor="white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        font=dict(family="IBM Plex Sans"),
    )
    fig3.update_xaxes(showgrid=False)
    fig3.update_yaxes(showgrid=True, gridcolor="#f0f0f0")
    st.plotly_chart(fig3, use_container_width=True)

    section("FULL SPEC COMPARISON")
    all_keys = sorted(set(list(cam_a_d["specs"]) + list(cam_b_d["specs"])))
    cmp_rows = [{"Parameter": k, cam_a_name: cam_a_d["specs"].get(k, "—"),
                 cam_b_name: cam_b_d["specs"].get(k, "—")} for k in all_keys]
    st.dataframe(pd.DataFrame(cmp_rows), use_container_width=True, hide_index=True)


# ══════════════════════════════════════════════════════════════════
# TAB 5 — Reports & Export
# ══════════════════════════════════════════════════════════════════
with tab5:

    # ── Left: PDF Report config ──────────────────────────────────
    col_rep, col_hist = st.columns([1, 1], gap="large")

    with col_rep:
        st.markdown(
            '<div class="report-box">'
            '<h3>📄 PDF Installation Report</h3>'
            '<p>Professional report including FOV data, installation drawing, '
            'ROI analysis and feature detection verdict — ready to hand to your team.</p>'
            '</div>',
            unsafe_allow_html=True,
        )

        section("REPORT DETAILS")
        rep_operator = st.text_input("Operator / Engineer name", value="Dejan Rožič", key="rep_op")
        rep_project  = st.text_input("Project / Machine name",   value="",            key="rep_proj")
        rep_notes    = st.text_area("Additional notes (optional)", height=80,          key="rep_notes")

        section("INCLUDE IN REPORT")
        inc_roi    = st.checkbox("ROI Analysis",         value=True,  key="inc_roi")
        inc_detect = st.checkbox("Feature Detection",    value=True,  key="inc_detect")

        section("REPORT PARAMETERS — FOV & DISTANCE")
        rep_dist = st.slider(
            "Mounting Distance for report (mm)",
            min_value=int(cam["min_dist"]), max_value=int(cam["max_dist"]),
            value=int(clamp(500, cam["min_dist"], cam["max_dist"])),
            step=10, key="rep_dist",
        )
        rep_fov_x, rep_fov_y = fov_from_dist(rep_dist, cam)
        rep_mpp_h, rep_ppm_h = resolution_metrics(rep_fov_x, cam["resolution_h"])
        rep_mpp_v, rep_ppm_v = resolution_metrics(rep_fov_y, cam["resolution_v"])
        st.caption(f"FOV: {rep_fov_x:.1f} × {rep_fov_y:.1f} mm  |  "
                   f"Resolution: {rep_mpp_h:.4f} mm/px (H)")

        if inc_roi:
            section("ROI PARAMETERS")
            rr1, rr2 = st.columns(2)
            with rr1:
                rep_roi_w = st.number_input("ROI Width (mm)", 1.0, float(rep_fov_x),
                                            float(clamp(rep_fov_x*0.5, 1, rep_fov_x)), 1.0, key="rep_roi_w")
            with rr2:
                rep_roi_h = st.number_input("ROI Height (mm)", 1.0, float(rep_fov_y),
                                            float(clamp(rep_fov_y*0.5, 1, rep_fov_y)), 1.0, key="rep_roi_h")
            rep_roi_px_h = rep_roi_w * (cam["resolution_h"] / rep_fov_x)
            rep_roi_px_v = rep_roi_h * (cam["resolution_v"] / rep_fov_y)
            rep_roi_cov  = (rep_roi_w * rep_roi_h) / (rep_fov_x * rep_fov_y) * 100
        else:
            rep_roi_w = rep_roi_h = rep_roi_px_h = rep_roi_px_v = rep_roi_cov = 0.0

        if inc_detect:
            section("FEATURE DETECTION PARAMETERS")
            rep_feat  = st.number_input("Feature size (mm)", 0.001, 500.0, 0.5, 0.01,
                                        format="%.3f", key="rep_feat")
            rep_rel   = st.select_slider("Reliability threshold (px)", [1,2,3,5,10], 3, key="rep_rel")
            rep_det_px = rep_feat * rep_ppm_h
            if rep_det_px >= rep_rel:
                rep_verdict = "ok"
            elif rep_det_px >= 1.0:
                rep_verdict = "marginal"
            else:
                rep_verdict = "fail"
        else:
            rep_feat = rep_det_px = 0.0
            rep_verdict = "ok"

        st.markdown("")
        if st.button("⬇️ Generate & Download PDF Report", type="primary", key="gen_pdf"):
            with st.spinner("Building report..."):
                params = {
                    "camera_name":   camera_name,
                    "camera_specs":  cam["specs"],
                    "distance":      rep_dist,
                    "fov_x":         rep_fov_x,
                    "fov_y":         rep_fov_y,
                    "mpp_h":         rep_mpp_h,
                    "ppm_h":         rep_ppm_h,
                    "mpp_v":         rep_mpp_v,
                    "ppm_v":         rep_ppm_v,
                    "res_h":         cam["resolution_h"],
                    "res_v":         cam["resolution_v"],
                    "roi_enabled":   inc_roi,
                    "roi_w":         rep_roi_w,
                    "roi_h":         rep_roi_h,
                    "roi_px_h":      rep_roi_px_h,
                    "roi_px_v":      rep_roi_px_v,
                    "roi_coverage":  rep_roi_cov,
                    "detection_enabled": inc_detect,
                    "feature_size":  rep_feat,
                    "detect_px":     rep_det_px,
                    "detect_verdict":rep_verdict,
                    "detect_min_1px":rep_mpp_h * 1,
                    "detect_min_3px":rep_mpp_h * 3,
                    "operator":      rep_operator,
                    "project":       rep_project,
                    "notes":         rep_notes,
                }
                pdf_bytes = generate_pdf_report(params)
                fname = f"Keyence_{camera_name}_{rep_dist}mm_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
            st.download_button(
                label="📥 Download PDF",
                data=pdf_bytes,
                file_name=fname,
                mime="application/pdf",
                key="dl_pdf",
            )
            st.success(f"Report ready: **{fname}**")

    # ── Right: Session history ───────────────────────────────────
    with col_hist:
        history_count = len(st.session_state.history)
        st.markdown(
            f'<div class="report-box" style="background: linear-gradient(135deg,#0d3b1f,#1a6b3c);">'
            f'<h3>📋 Session Log '
            f'<span class="history-badge">{history_count}</span></h3>'
            f'<p>Every calculation you log is stored here for the session. '
            f'Export the full log as a formatted Excel file.</p>'
            f'</div>',
            unsafe_allow_html=True,
        )

        if history_count == 0:
            st.info("No calculations logged yet. Use the **➕ Log** buttons on the other tabs.")
        else:
            df_hist = pd.DataFrame(st.session_state.history)
            st.dataframe(df_hist, use_container_width=True, hide_index=True, height=320)

            st.markdown("")
            col_dl1, col_dl2 = st.columns(2)
            with col_dl1:
                xlsx_bytes = generate_excel_log(st.session_state.history)
                st.download_button(
                    label="⬇️ Export as Excel (.xlsx)",
                    data=xlsx_bytes,
                    file_name=f"Keyence_SessionLog_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="dl_xlsx",
                )
            with col_dl2:
                csv_bytes = df_hist.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="⬇️ Export as CSV",
                    data=csv_bytes,
                    file_name=f"Keyence_SessionLog_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                    key="dl_csv",
                )

            if st.button("🗑️ Clear session log", key="clear_hist"):
                st.session_state.history = []
                st.rerun()

        st.markdown("")
        section("QUICK REPORT FROM LAST LOG ENTRY")
        if history_count > 0:
            last = st.session_state.history[-1]
            st.json(last)
        else:
            st.caption("Nothing logged yet.")


# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
st.markdown("<div style='margin-bottom:50px;'></div>", unsafe_allow_html=True)
st.markdown(
    '<div class="footer">Keyence IV3 Camera Calculator&nbsp;·&nbsp;Made by Dejan Rožič</div>',
    unsafe_allow_html=True,
)
