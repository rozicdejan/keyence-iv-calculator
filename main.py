import os
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from PIL import Image

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
# CUSTOM CSS – clean industrial look
# ─────────────────────────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'IBM Plex Sans', sans-serif;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: #0f1117;
    }
    [data-testid="stSidebar"] * {
        color: #e0e0e0 !important;
    }
    [data-testid="stSidebar"] .stSelectbox label,
    [data-testid="stSidebar"] p {
        color: #a0a0a0 !important;
        font-size: 0.8rem !important;
    }

    /* Metric cards */
    .metric-card {
        background: #f8f9fa;
        border: 1px solid #e0e0e0;
        border-left: 4px solid #1a73e8;
        border-radius: 6px;
        padding: 14px 18px;
        margin-bottom: 10px;
    }
    .metric-card.green  { border-left-color: #0d9c50; }
    .metric-card.orange { border-left-color: #e87e1a; }
    .metric-card.red    { border-left-color: #d93025; }
    .metric-card.blue   { border-left-color: #1a73e8; }

    .metric-label {
        font-size: 0.72rem;
        color: #666;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 2px;
    }
    .metric-value {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 1.35rem;
        font-weight: 600;
        color: #111;
    }
    .metric-unit {
        font-size: 0.75rem;
        color: #888;
        margin-left: 4px;
    }

    /* Section headers */
    .section-header {
        font-size: 0.68rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        color: #888;
        border-bottom: 1px solid #e0e0e0;
        padding-bottom: 4px;
        margin: 18px 0 12px 0;
    }

    /* Detect result banners */
    .detect-yes {
        background: #e6f4ea;
        border: 1px solid #0d9c50;
        border-radius: 6px;
        padding: 12px 18px;
        color: #0d5e30;
        font-weight: 600;
        margin-top: 10px;
    }
    .detect-no {
        background: #fce8e6;
        border: 1px solid #d93025;
        border-radius: 6px;
        padding: 12px 18px;
        color: #7f1e17;
        font-weight: 600;
        margin-top: 10px;
    }
    .detect-marginal {
        background: #fef7e0;
        border: 1px solid #e8940a;
        border-radius: 6px;
        padding: 12px 18px;
        color: #7f4b00;
        font-weight: 600;
        margin-top: 10px;
    }

    /* Footer */
    .footer {
        position: fixed;
        bottom: 0; left: 0;
        width: 100%;
        background: white;
        border-top: 1px solid #e6e6e6;
        padding: 6px 0;
        text-align: center;
        font-size: 0.75rem;
        color: #888;
        z-index: 999;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab"] {
        font-family: 'IBM Plex Sans', sans-serif;
        font-weight: 600;
        font-size: 0.85rem;
    }

    /* Number inputs & sliders */
    [data-testid="stNumberInput"] label,
    [data-testid="stSlider"] label {
        font-size: 0.8rem !important;
        font-weight: 600 !important;
        color: #444 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def clamp(value, min_value, max_value):
    return max(min_value, min(max_value, value))


def lerp(value, in_min, in_max, out_min, out_max):
    if (in_max - in_min) == 0:
        return float(out_min)
    return float(out_min + (value - in_min) * (out_max - out_min) / (in_max - in_min))


def fov_from_dist(dist, cam):
    fov_x = lerp(dist, cam["min_dist"], cam["max_dist"], cam["min_fov_x"], cam["max_fov_x"])
    fov_y = lerp(dist, cam["min_dist"], cam["max_dist"], cam["min_fov_y"], cam["max_fov_y"])
    return fov_x, fov_y


def dist_from_fov(fov_x, cam):
    return lerp(fov_x, cam["min_fov_x"], cam["max_fov_x"], cam["min_dist"], cam["max_dist"])


def resolution_metrics(fov_mm, pixels):
    if pixels <= 0 or fov_mm <= 0:
        return 0.0, 0.0
    mpp = fov_mm / pixels
    ppm = 1.0 / mpp
    return mpp, ppm


def metric_card(label, value, unit="", color="blue"):
    st.markdown(
        f"""
        <div class="metric-card {color}">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}<span class="metric-unit">{unit}</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section(title):
    st.markdown(f'<div class="section-header">{title}</div>', unsafe_allow_html=True)


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
            "min_dist": 50, "max_dist": 3000,
            "resolution_h": 1280, "resolution_v": 960,
            "color": True,
            "specs": {
                "Type": "Standard",
                "Installed Distance": "50 mm or more",
                "FOV @ 50 mm": "22 × 16 mm",
                "FOV @ 3000 mm": "1184 × 888 mm",
                "Image Sensor": "1/2.9\" colour CMOS",
                "Resolution": "1280 × 960 px",
                "Focus": "Auto",
                "Exposure": "12 μs – 9 ms",
                "Illumination": "White LED",
                "Lighting": "Pulse / continuous switchable",
                "IP Rating": "IP67",
                "Temp. Range": "0 – +50 °C",
                "Humidity": "35 – 85 % RH",
                "Weight": "≈ 75 g (no AI Lighting)",
            },
        },
        "IV3-G600MA": {
            "image": "iv4-g600ca.png",
            "min_fov_x": 51, "max_fov_x": 2730,
            "min_fov_y": 38, "max_fov_y": 2044,
            "min_dist": 50, "max_dist": 3000,
            "resolution_h": 1280, "resolution_v": 960,
            "color": False,
            "specs": {
                "Type": "Wide view",
                "Installed Distance": "50 mm or more",
                "FOV @ 50 mm": "51 × 38 mm",
                "FOV @ 3000 mm": "2730 × 2044 mm",
                "Image Sensor": "1/2.9\" monochrome CMOS",
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
                "Image Sensor": "1/2.9\" colour CMOS",
                "Resolution": "1280 × 960 px",
                "Focus": "Auto",
                "Exposure": "12 μs – 10 ms",
                "Illumination": "White LED",
                "Lighting": "Pulse / continuous switchable",
                "Network": "EtherNet/IP, PROFINET, TCP/IP",
                "Programs": "128 (SD card) / 32 (no SD)",
                "IP Rating": "IP67",
                "Temp. Range": "0 – +50 °C",
                "Weight": "≈ 300 g",
            },
        },
    }


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
cameras = get_camera_data()

with st.sidebar:
    st.markdown("### 🔍 Keyence IV3 Series")
    st.markdown("---")
    camera_name = st.selectbox("Camera Model", list(cameras.keys()), label_visibility="visible")
    cam = cameras[camera_name]

    st.markdown("---")
    section("SENSOR SPECS")
    st.markdown(f"**Resolution:** {cam['resolution_h']} × {cam['resolution_v']} px")
    st.markdown(f"**Colour:** {'Yes ✅' if cam['color'] else 'No (Mono)'}")
    st.markdown(f"**Min dist:** {cam['min_dist']} mm")
    st.markdown(f"**Max dist:** {cam['max_dist']} mm")
    st.markdown(f"**FOV min (H×V):** {cam['min_fov_x']} × {cam['min_fov_y']} mm")
    st.markdown(f"**FOV max (H×V):** {cam['max_fov_x']} × {cam['max_fov_y']} mm")

    st.markdown("---")
    # Camera image
    image_path = os.path.join(os.getcwd(), PICTURES_FOLDER, cam["image"])
    if os.path.exists(image_path):
        try:
            st.image(Image.open(image_path), caption=camera_name, use_container_width=True)
        except Exception:
            st.info("Image unavailable")
    else:
        st.info(f"📷 Place '{cam['image']}' in /{PICTURES_FOLDER}/")

    st.markdown("---")
    st.markdown("<small>Made by Dejan Rožič</small>", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# MAIN HEADER
# ─────────────────────────────────────────────
st.title("🔍 Keyence IV3 Camera Calculator")
st.markdown(
    f"<span style='color:#888;font-size:0.9rem;'>Active model: <b>{camera_name}</b> — "
    f"{cam['resolution_h']}×{cam['resolution_v']} px&nbsp;&nbsp;|&nbsp;&nbsp;"
    f"FOV range: {cam['min_fov_x']}–{cam['max_fov_x']} mm (H)</span>",
    unsafe_allow_html=True,
)
st.markdown("")

# ─────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(
    ["📐 FOV & Distance", "🔲 ROI Analysis", "🎯 Feature Detection", "⚖️ Compare Cameras"]
)

# ═══════════════════════════════════════════════════════════
# TAB 1 — FOV & Distance
# ═══════════════════════════════════════════════════════════
with tab1:
    col_calc, col_vis = st.columns([1, 1], gap="large")

    with col_calc:
        section("MOUNTING DISTANCE → FOV")
        distance = st.slider(
            "Mounting Distance (mm)",
            min_value=int(cam["min_dist"]),
            max_value=int(cam["max_dist"]),
            value=int(clamp(500, cam["min_dist"], cam["max_dist"])),
            step=10,
            key="dist_slider",
        )
        fov_x, fov_y = fov_from_dist(distance, cam)
        mpp_h, ppm_h = resolution_metrics(fov_x, cam["resolution_h"])
        mpp_v, ppm_v = resolution_metrics(fov_y, cam["resolution_v"])

        c1, c2 = st.columns(2)
        with c1:
            metric_card("FOV Horizontal", f"{fov_x:.1f}", "mm", "blue")
            metric_card("Resolution H", f"{mpp_h:.4f}", "mm/px", "green")
            metric_card("Resolution H", f"{ppm_h:.2f}", "px/mm", "green")
        with c2:
            metric_card("FOV Vertical", f"{fov_y:.1f}", "mm", "blue")
            metric_card("Resolution V", f"{mpp_v:.4f}", "mm/px", "orange")
            metric_card("Resolution V", f"{ppm_v:.2f}", "px/mm", "orange")

        st.markdown("")
        section("TARGET FOV → REQUIRED DISTANCE")
        target_h = st.number_input(
            "Target Horizontal FOV (mm)",
            min_value=float(cam["min_fov_x"]),
            max_value=float(cam["max_fov_x"]),
            value=float(clamp(200, cam["min_fov_x"], cam["max_fov_x"])),
            step=5.0,
            key="target_h",
        )
        req_dist = dist_from_fov(target_h, cam)
        metric_card("Required Mounting Distance", f"{req_dist:.1f}", "mm", "blue")

        st.markdown("")
        section("MANUAL RESOLUTION CHECK")
        m1, m2 = st.columns(2)
        with m1:
            man_fov_h = st.number_input(
                "Actual FOV Width (mm)",
                min_value=float(cam["min_fov_x"]),
                max_value=float(cam["max_fov_x"]),
                value=float(clamp(100, cam["min_fov_x"], cam["max_fov_x"])),
                step=1.0,
                key="man_h",
            )
        with m2:
            man_fov_v = st.number_input(
                "Actual FOV Height (mm)",
                min_value=float(cam["min_fov_y"]),
                max_value=float(cam["max_fov_y"]),
                value=float(clamp(100, cam["min_fov_y"], cam["max_fov_y"])),
                step=1.0,
                key="man_v",
            )
        mm_h, px_h = resolution_metrics(man_fov_h, cam["resolution_h"])
        mm_v, px_v = resolution_metrics(man_fov_v, cam["resolution_v"])
        r1, r2, r3, r4 = st.columns(4)
        with r1: metric_card("H mm/px", f"{mm_h:.4f}", "", "green")
        with r2: metric_card("H px/mm", f"{px_h:.2f}", "", "green")
        with r3: metric_card("V mm/px", f"{mm_v:.4f}", "", "orange")
        with r4: metric_card("V px/mm", f"{px_v:.2f}", "", "orange")

    with col_vis:
        section("FOV GEOMETRY DIAGRAM")
        # Draw camera + FOV trapezoid with Plotly
        cam_w = fov_x
        cam_h_val = fov_y
        scale = 1.0

        fig = go.Figure()

        # FOV rectangle (top view schematic)
        fig.add_shape(
            type="rect",
            x0=-cam_w / 2, x1=cam_w / 2,
            y0=0, y1=cam_h_val,
            fillcolor="rgba(26,115,232,0.10)",
            line=dict(color="#1a73e8", width=2),
        )
        # Camera body
        body_w = cam_w * 0.04
        fig.add_shape(
            type="rect",
            x0=-body_w, x1=body_w,
            y0=cam_h_val, y1=cam_h_val + cam_h_val * 0.08,
            fillcolor="#444",
            line=dict(color="#222", width=1),
        )
        # Distance arrow
        fig.add_annotation(
            x=cam_w / 2 * 1.05, y=cam_h_val / 2,
            ax=cam_w / 2 * 1.05, ay=cam_h_val,
            xref="x", yref="y", axref="x", ayref="y",
            text="", showarrow=True,
            arrowhead=2, arrowcolor="#888", arrowwidth=1.5,
        )
        fig.add_annotation(
            x=cam_w / 2 * 1.05, y=cam_h_val / 2,
            ax=cam_w / 2 * 1.05, ay=0,
            xref="x", yref="y", axref="x", ayref="y",
            text="", showarrow=True,
            arrowhead=2, arrowcolor="#888", arrowwidth=1.5,
        )
        fig.add_annotation(
            x=cam_w / 2 * 1.12, y=cam_h_val / 2,
            text=f"{distance} mm",
            showarrow=False,
            font=dict(size=11, color="#444"),
            xref="x", yref="y",
        )
        # FOV dimension label H
        fig.add_annotation(
            x=0, y=-cam_h_val * 0.06,
            text=f"← {fov_x:.1f} mm (H) →",
            showarrow=False,
            font=dict(size=12, color="#1a73e8"),
            xref="x", yref="y",
        )
        # FOV dimension label V
        fig.add_annotation(
            x=-cam_w / 2 * 1.12, y=cam_h_val / 2,
            text=f"{fov_y:.1f} mm (V)",
            showarrow=False,
            font=dict(size=12, color="#1a73e8", family="IBM Plex Sans"),
            xref="x", yref="y",
            textangle=-90,
        )

        fig.update_layout(
            height=340,
            margin=dict(l=20, r=60, t=20, b=40),
            xaxis=dict(
                showgrid=False, zeroline=False, showticklabels=False,
                range=[-cam_w * 0.8, cam_w * 0.8],
            ),
            yaxis=dict(
                showgrid=False, zeroline=False, showticklabels=False,
                scaleanchor="x", scaleratio=1,
                range=[-cam_h_val * 0.15, cam_h_val * 1.15],
            ),
            plot_bgcolor="white",
            paper_bgcolor="white",
        )
        st.plotly_chart(fig, use_container_width=True)

        section("CAMERA SPECIFICATIONS")
        df = pd.DataFrame(cam["specs"].items(), columns=["Parameter", "Value"])
        st.dataframe(df, use_container_width=True, hide_index=True, height=280)


# ═══════════════════════════════════════════════════════════
# TAB 2 — ROI Analysis
# ═══════════════════════════════════════════════════════════
with tab2:
    st.markdown("Define a **Region of Interest (ROI)** within the camera's field of view to see the effective pixel count and resolution inside that region.")
    st.markdown("")

    col_roi_in, col_roi_out = st.columns([1, 1], gap="large")

    with col_roi_in:
        section("MOUNTING DISTANCE")
        roi_dist = st.slider(
            "Mounting Distance (mm)",
            min_value=int(cam["min_dist"]),
            max_value=int(cam["max_dist"]),
            value=int(clamp(500, cam["min_dist"], cam["max_dist"])),
            step=10,
            key="roi_dist",
        )
        fov_x_roi, fov_y_roi = fov_from_dist(roi_dist, cam)

        metric_card("Full FOV (H × V)", f"{fov_x_roi:.1f} × {fov_y_roi:.1f}", "mm", "blue")

        section("ROI SIZE")
        roi_w_max = fov_x_roi
        roi_h_max = fov_y_roi

        roi_w = st.number_input(
            "ROI Width (mm)",
            min_value=1.0,
            max_value=float(roi_w_max),
            value=float(clamp(roi_w_max * 0.5, 1, roi_w_max)),
            step=1.0,
            key="roi_w",
        )
        roi_h = st.number_input(
            "ROI Height (mm)",
            min_value=1.0,
            max_value=float(roi_h_max),
            value=float(clamp(roi_h_max * 0.5, 1, roi_h_max)),
            step=1.0,
            key="roi_h",
        )

        section("ROI POSITION (offset from FOV center)")
        roi_x_offset = st.slider(
            "Horizontal offset (mm, 0 = centre)",
            min_value=-float((fov_x_roi - roi_w) / 2),
            max_value=float((fov_x_roi - roi_w) / 2),
            value=0.0,
            step=0.5,
            key="roi_x_off",
            disabled=(roi_w >= fov_x_roi),
        )
        roi_y_offset = st.slider(
            "Vertical offset (mm, 0 = centre)",
            min_value=-float((fov_y_roi - roi_h) / 2),
            max_value=float((fov_y_roi - roi_h) / 2),
            value=0.0,
            step=0.5,
            key="roi_y_off",
            disabled=(roi_h >= fov_y_roi),
        )

    with col_roi_out:
        # Derived ROI metrics
        px_per_mm_h = cam["resolution_h"] / fov_x_roi
        px_per_mm_v = cam["resolution_v"] / fov_y_roi

        roi_pixels_h = roi_w * px_per_mm_h
        roi_pixels_v = roi_h * px_per_mm_v
        roi_pixel_area = roi_pixels_h * roi_pixels_v
        fov_area = fov_x_roi * fov_y_roi
        roi_coverage = (roi_w * roi_h) / fov_area * 100

        section("ROI RESOLUTION METRICS")
        c1, c2 = st.columns(2)
        with c1:
            metric_card("ROI Width in Pixels", f"{roi_pixels_h:.0f}", "px", "blue")
            metric_card("ROI Height in Pixels", f"{roi_pixels_v:.0f}", "px", "blue")
            metric_card("Total ROI Pixels", f"{roi_pixel_area/1e6:.2f}", "MP", "green")
        with c2:
            metric_card("Resolution H", f"{1/px_per_mm_h:.4f}", "mm/px", "orange")
            metric_card("Resolution V", f"{1/px_per_mm_v:.4f}", "mm/px", "orange")
            metric_card("ROI Coverage", f"{roi_coverage:.1f}", "% of FOV", "blue")

        section("FOV + ROI DIAGRAM")
        # Coordinate system: FOV is centred at 0,0
        half_fov_x = fov_x_roi / 2
        half_fov_y = fov_y_roi / 2

        roi_cx = roi_x_offset
        roi_cy = roi_y_offset
        roi_x0 = roi_cx - roi_w / 2
        roi_x1 = roi_cx + roi_w / 2
        roi_y0 = roi_cy - roi_h / 2
        roi_y1 = roi_cy + roi_h / 2

        fig2 = go.Figure()

        # Full FOV
        fig2.add_shape(
            type="rect",
            x0=-half_fov_x, x1=half_fov_x,
            y0=-half_fov_y, y1=half_fov_y,
            fillcolor="rgba(26,115,232,0.07)",
            line=dict(color="#1a73e8", width=2, dash="dot"),
        )
        fig2.add_annotation(
            x=0, y=half_fov_y * 1.06,
            text=f"FOV  {fov_x_roi:.0f} × {fov_y_roi:.0f} mm",
            showarrow=False,
            font=dict(size=11, color="#1a73e8"),
        )

        # ROI fill
        fig2.add_shape(
            type="rect",
            x0=roi_x0, x1=roi_x1,
            y0=roi_y0, y1=roi_y1,
            fillcolor="rgba(217,48,37,0.18)",
            line=dict(color="#d93025", width=2),
        )
        fig2.add_annotation(
            x=roi_cx, y=roi_cy,
            text=f"ROI<br>{roi_w:.0f}×{roi_h:.0f} mm<br>{roi_pixels_h:.0f}×{roi_pixels_v:.0f} px",
            showarrow=False,
            font=dict(size=10, color="#7f1e17"),
            bgcolor="rgba(255,255,255,0.75)",
            bordercolor="#d93025",
            borderwidth=1,
        )

        # Crosshair at FOV centre
        fig2.add_shape(type="line", x0=-half_fov_x * 0.05, x1=half_fov_x * 0.05, y0=0, y1=0,
                       line=dict(color="#aaa", width=1))
        fig2.add_shape(type="line", x0=0, x1=0, y0=-half_fov_y * 0.05, y1=half_fov_y * 0.05,
                       line=dict(color="#aaa", width=1))

        pad = max(fov_x_roi, fov_y_roi) * 0.12
        fig2.update_layout(
            height=380,
            margin=dict(l=10, r=10, t=30, b=10),
            xaxis=dict(
                showgrid=False, zeroline=False, showticklabels=False,
                range=[-half_fov_x - pad, half_fov_x + pad],
            ),
            yaxis=dict(
                showgrid=False, zeroline=False, showticklabels=False,
                scaleanchor="x", scaleratio=1,
                range=[-half_fov_y - pad, half_fov_y + pad],
            ),
            plot_bgcolor="white",
            paper_bgcolor="white",
        )
        st.plotly_chart(fig2, use_container_width=True)


# ═══════════════════════════════════════════════════════════
# TAB 3 — Feature Detection
# ═══════════════════════════════════════════════════════════
with tab3:
    st.markdown(
        "Enter the **smallest feature size** you need to detect. The calculator tells you whether "
        "this camera can resolve it at your chosen mounting distance, and how many pixels cover it."
    )
    st.markdown("")

    col_fd1, col_fd2 = st.columns([1, 1], gap="large")

    with col_fd1:
        section("SETUP")
        fd_dist = st.slider(
            "Mounting Distance (mm)",
            min_value=int(cam["min_dist"]),
            max_value=int(cam["max_dist"]),
            value=int(clamp(500, cam["min_dist"], cam["max_dist"])),
            step=10,
            key="fd_dist",
        )
        fov_x_fd, fov_y_fd = fov_from_dist(fd_dist, cam)

        section("FEATURE TO DETECT")
        feature_size = st.number_input(
            "Minimum Feature Size (mm)",
            min_value=0.001,
            max_value=500.0,
            value=0.5,
            step=0.01,
            format="%.3f",
            key="feature_size",
        )
        reliability_px = st.select_slider(
            "Required pixels per feature (reliability factor)",
            options=[1, 2, 3, 5, 10],
            value=3,
            key="rel_px",
            help="Industry recommendation: 3–5 px per feature minimum for reliable detection",
        )

    with col_fd2:
        mpp_h_fd, ppm_h_fd = resolution_metrics(fov_x_fd, cam["resolution_h"])
        mpp_v_fd, ppm_v_fd = resolution_metrics(fov_y_fd, cam["resolution_v"])

        pixels_on_feature_h = feature_size * ppm_h_fd
        pixels_on_feature_v = feature_size * ppm_v_fd
        min_pixels = min(pixels_on_feature_h, pixels_on_feature_v)

        min_detectable_h = mpp_h_fd * 1  # 1 px
        min_detectable_3px = mpp_h_fd * 3
        min_detectable_5px = mpp_h_fd * 5

        section("RESOLUTION AT THIS DISTANCE")
        c1, c2 = st.columns(2)
        with c1:
            metric_card("FOV H", f"{fov_x_fd:.1f}", "mm", "blue")
            metric_card("Resolution H", f"{mpp_h_fd:.4f}", "mm/px", "orange")
        with c2:
            metric_card("FOV V", f"{fov_y_fd:.1f}", "mm", "blue")
            metric_card("Resolution V", f"{mpp_v_fd:.4f}", "mm/px", "orange")

        section("DETECTION RESULT")
        metric_card("Pixels on Feature (H)", f"{pixels_on_feature_h:.1f}", "px", "green")
        metric_card("Pixels on Feature (V)", f"{pixels_on_feature_v:.1f}", "px", "green")

        if min_pixels >= reliability_px:
            st.markdown(
                f"""<div class="detect-yes">
                ✅  <b>DETECTABLE</b> — {min_pixels:.1f} px cover the feature
                (threshold: {reliability_px} px). Detection is reliable.
                </div>""",
                unsafe_allow_html=True,
            )
        elif min_pixels >= 1.0:
            st.markdown(
                f"""<div class="detect-marginal">
                ⚠️  <b>MARGINAL</b> — Only {min_pixels:.1f} px cover the feature
                (threshold: {reliability_px} px). Detection may be unreliable.
                Consider moving closer or using a narrower-FOV model.
                </div>""",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""<div class="detect-no">
                ❌  <b>NOT DETECTABLE</b> — Feature is sub-pixel ({min_pixels:.3f} px).
                Minimum detectable feature at this distance: <b>{min_detectable_h:.4f} mm</b> (1 px),
                <b>{min_detectable_3px:.4f} mm</b> (3 px reliable).
                </div>""",
                unsafe_allow_html=True,
            )

        st.markdown("")
        section("DETECTION LIMITS AT THIS DISTANCE")
        limits = {
            "Threshold": ["1 px (theoretical)", "3 px (good)", "5 px (robust)"],
            "Min Feature (H)": [
                f"{mpp_h_fd * 1:.4f} mm",
                f"{mpp_h_fd * 3:.4f} mm",
                f"{mpp_h_fd * 5:.4f} mm",
            ],
            "Min Feature (V)": [
                f"{mpp_v_fd * 1:.4f} mm",
                f"{mpp_v_fd * 3:.4f} mm",
                f"{mpp_v_fd * 5:.4f} mm",
            ],
        }
        st.dataframe(pd.DataFrame(limits), use_container_width=True, hide_index=True)


# ═══════════════════════════════════════════════════════════
# TAB 4 — Compare Cameras
# ═══════════════════════════════════════════════════════════
with tab4:
    st.markdown("Select two cameras and a mounting distance to compare FOV and resolution side-by-side.")
    st.markdown("")

    cc1, cc2, cc3 = st.columns([1, 1, 1])
    with cc1:
        cam_a_name = st.selectbox("Camera A", list(cameras.keys()), index=0, key="cmp_a")
    with cc2:
        cam_b_name = st.selectbox("Camera B", list(cameras.keys()), index=1, key="cmp_b")
    with cc3:
        cmp_min = max(cameras[cam_a_name]["min_dist"], cameras[cam_b_name]["min_dist"])
        cmp_max = min(cameras[cam_a_name]["max_dist"], cameras[cam_b_name]["max_dist"])
        if cmp_min > cmp_max:
            st.warning("Selected cameras have no overlapping distance range.")
            cmp_dist = cmp_min
        else:
            cmp_dist = st.slider(
                "Comparison Distance (mm)",
                min_value=int(cmp_min),
                max_value=int(cmp_max),
                value=int(clamp(500, cmp_min, cmp_max)),
                step=10,
                key="cmp_dist",
            )

    cam_a = cameras[cam_a_name]
    cam_b = cameras[cam_b_name]
    fov_xa, fov_ya = fov_from_dist(cmp_dist, cam_a)
    fov_xb, fov_yb = fov_from_dist(cmp_dist, cam_b)
    mpp_ha, ppm_ha = resolution_metrics(fov_xa, cam_a["resolution_h"])
    mpp_hb, ppm_hb = resolution_metrics(fov_xb, cam_b["resolution_h"])

    st.markdown("")
    col_a, col_b = st.columns(2, gap="large")

    def render_cam_summary(cam_n, cam_data, fov_x, fov_y, mpp_h, ppm_h, dist):
        st.markdown(f"#### {cam_n}")
        metric_card("FOV Horizontal", f"{fov_x:.1f}", "mm", "blue")
        metric_card("FOV Vertical", f"{fov_y:.1f}", "mm", "blue")
        metric_card("Resolution H", f"{mpp_h:.4f}", "mm/px", "green")
        metric_card("Sensor", "Colour" if cam_data["color"] else "Monochrome", "", "orange")
        metric_card("Pixel Count", f"{cam_data['resolution_h']}×{cam_data['resolution_v']}", "px", "blue")

    with col_a:
        render_cam_summary(cam_a_name, cam_a, fov_xa, fov_ya, mpp_ha, ppm_ha, cmp_dist)
    with col_b:
        render_cam_summary(cam_b_name, cam_b, fov_xb, fov_yb, mpp_hb, ppm_hb, cmp_dist)

    # Comparison bar chart
    section("SIDE-BY-SIDE COMPARISON CHART")
    fig3 = go.Figure()
    metrics_labels = ["FOV H (mm)", "FOV V (mm)", "mm/px (H) ×1000"]
    vals_a = [fov_xa, fov_ya, mpp_ha * 1000]
    vals_b = [fov_xb, fov_yb, mpp_hb * 1000]

    fig3.add_trace(go.Bar(name=cam_a_name, x=metrics_labels, y=vals_a, marker_color="#1a73e8"))
    fig3.add_trace(go.Bar(name=cam_b_name, x=metrics_labels, y=vals_b, marker_color="#d93025"))
    fig3.update_layout(
        barmode="group",
        height=320,
        margin=dict(l=10, r=10, t=10, b=30),
        plot_bgcolor="white",
        paper_bgcolor="white",
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        font=dict(family="IBM Plex Sans"),
    )
    fig3.update_xaxes(showgrid=False)
    fig3.update_yaxes(showgrid=True, gridcolor="#f0f0f0")
    st.plotly_chart(fig3, use_container_width=True)

    section("FULL SPEC COMPARISON")
    all_keys = sorted(set(list(cam_a["specs"].keys()) + list(cam_b["specs"].keys())))
    cmp_rows = []
    for k in all_keys:
        cmp_rows.append({
            "Parameter": k,
            cam_a_name: cam_a["specs"].get(k, "—"),
            cam_b_name: cam_b["specs"].get(k, "—"),
        })
    st.dataframe(pd.DataFrame(cmp_rows), use_container_width=True, hide_index=True)


# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
st.markdown("<div style='margin-bottom:50px;'></div>", unsafe_allow_html=True)
st.markdown(
    """
    <div class="footer">
        Keyence IV3 Camera Calculator &nbsp;·&nbsp; Made by Dejan Rožič
    </div>
    """,
    unsafe_allow_html=True,
)
