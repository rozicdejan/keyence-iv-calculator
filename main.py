import os

import pandas as pd
import streamlit as st
from PIL import Image

PICTURES_FOLDER = "Pictures"


def clamp(value, min_value, max_value):
    return max(min_value, min(max_value, value))


def calculate_resolution_metrics(fov_mm, pixel_dimension):
    """Return (mm_per_pixel, pixels_per_mm)."""
    if pixel_dimension <= 0 or fov_mm <= 0:
        return 0.0, 0.0
    mm_per_pixel = fov_mm / pixel_dimension
    px_per_mm = 1 / mm_per_pixel if mm_per_pixel != 0 else 0.0
    return mm_per_pixel, px_per_mm


def linear_interpolation(value, min_val_in, max_val_in, min_val_out, max_val_out):
    """Linear interpolation with protection against zero range."""
    if (max_val_in - min_val_in) == 0:
        return float(min_val_out)
    return float(
        min_val_out
        + (value - min_val_in) * (max_val_out - min_val_out) / (max_val_in - min_val_in)
    )


def calculate_mounting_distance(target_fov, min_fov, max_fov, min_dist, max_dist):
    return linear_interpolation(target_fov, min_fov, max_fov, min_dist, max_dist)


def calculate_fov_from_distance(distance, min_fov, max_fov, min_dist, max_dist):
    return linear_interpolation(distance, min_dist, max_dist, min_fov, max_fov)


def calculate_fov_x_y(distance, min_fov_x, max_fov_x, min_fov_y, max_fov_y, min_dist, max_dist):
    fov_x = calculate_fov_from_distance(distance, min_fov_x, max_fov_x, min_dist, max_dist)
    fov_y = calculate_fov_from_distance(distance, min_fov_y, max_fov_y, min_dist, max_dist)
    return fov_x, fov_y


@st.cache_data
def get_camera_data():
    return {
        "IV3-G500CA": {
            "image": "iv4-g500ca.png",
            "min_fov_x": 22,
            "max_fov_x": 1184,
            "min_fov_y": 16,
            "max_fov_y": 888,
            "min_dist": 50,
            "max_dist": 3000,
            "resolution_h": 1280,
            "resolution_v": 960,
            "specs": {
                "Type": "Standard",
                "Installed Distance": "50 mm or more",
                "Field of View (50 mm)": "22 (H) × 16 (V) mm",
                "Field of View (3000 mm)": "1184 (H) × 888 (V) mm",
                "Image Sensor": "1/2.9 inch colour CMOS",
                "Resolution": "1280 (H) × 960 (V)",
                "Focus Adjustment": "Auto",
                "Exposure Time": "12 μs to 9 ms",
                "Illumination": "White LED",
                "Lighting Method": "Pulse / continuous lighting is switchable",
                "Enclosure Rating": "IP67",
                "Temperature Range": "0 to +50°C (No freezing)",
                "Relative Humidity": "35 to 85% RH (No condensation)",
                "Vibration Resistance": "10 to 55 Hz; double amplitude 1.5 mm, 2 hours in each direction",
                "Shock Resistance": "500 m/s², 3 times in each of the 6 directions",
                "Material": "Main unit case: Zinc die-casting, Front cover: Acrylic, Operation indicator cover: TPU",
                "Weight": "Approx. 75 g (without AI Lighting), Approx. 225 g (with AI Lighting)",
            },
        },
        "IV3-G600MA": {
            "image": "iv4-g600ca.png",
            "min_fov_x": 51,
            "max_fov_x": 2730,
            "min_fov_y": 38,
            "max_fov_y": 2044,
            "min_dist": 50,
            "max_dist": 3000,
            "resolution_h": 1280,
            "resolution_v": 960,
            "specs": {
                "Type": "Wide view",
                "Installed Distance": "50 mm or more",
                "Field of View (50 mm)": "51 (H) × 38 (V) mm",
                "Field of View (3000 mm)": "2730 (H) × 2044 (V) mm",
                "Image Sensor": "1/2.9 inch monochrome CMOS",
                "Resolution": "1280 (H) × 960 (V)",
                "Focus Adjustment": "Auto",
                "Exposure Time": "12 μs to 9 ms",
                "Illumination": "Infrared LED",
                "Lighting Method": "Pulse lighting",
                "Enclosure Rating": "IP67",
                "Temperature Range": "0 to +50°C (No freezing)",
                "Vibration Resistance": "10 to 55 Hz; amplitude 1.5 mm",
                "Shock Resistance": "500 m/s², 3 times in each direction",
                "Weight": "Approx. 75 g (without AI Lighting)",
            },
        },
        "IV3-400CA": {
            "image": "iv4-g600ca.png",  # same picture as IV3-G600MA
            "min_fov_x": 58,
            "max_fov_x": 464,
            "min_fov_y": 44,
            "max_fov_y": 348,
            "min_dist": 400,
            "max_dist": 3000,
            "resolution_h": 1280,
            "resolution_v": 960,
            "specs": {
                "Type": "Narrow view",
                "Installed Distance": "400 mm or more",
                "Field of View (400 mm)": "58 (H) × 44 (V) mm",
                "Field of View (3000 mm)": "464 (H) × 348 (V) mm",
                "Image Sensor": "1/2.9 inch colour CMOS",
                "Resolution": "1280 (H) × 960 (V)",
                "Focus Adjustment": "Auto",
                "Exposure Time": "12 μs to 10 ms",
                "Illumination": "White LED",
                "Lighting Method": "Pulse lighting / continuously lighting is switchable",
                "Available Modes": "Standard mode / Sorting mode",
                "Number of Tools": "Total: 65 tools",
                "Programs": "128 programs (with SD card) / 32 programs (without SD card)",
                "Ethernet": "1000BASE-T / 100BASE-TX",
                "Network": "EtherNet/IP, PROFINET, TCP/IP non-procedure communication",
                "Enclosure Rating": "IP67",
                "Temperature Range": "0 to +50°C (No freezing)",
                "Relative Humidity": "35 to 85% RH (No condensation)",
                "Vibration Resistance": "10 to 55 Hz; double amplitude 1.5 mm; 2 hours in X, Y, Z directions",
                "Shock Resistance": "500 m/s², 3 times in each of the 6 directions",
                "Weight": "Approx. 300 g (without AI Lighting unit) / Approx. 495 g (with AI Lighting unit)",
            },
        },
    }


FOOTER_HTML = """
<style>
.footer {
    position: fixed;
    left: 0;
    bottom: 0;
    width: 100%;
    background-color: white;
    color: #666;
    text-align: center;
    padding: 5px 0;
    border-top: 1px solid #e6e6e6;
    z-index: 999;
}
</style>
<div class="footer">
    <p>Made by Dejan Rožič</p>
</div>
"""

st.set_page_config(page_title="Keyence Camera Calculator", layout="wide")
st.title("🔍 Keyence Camera Resolution & Mounting Distance Calculator")

cameras = get_camera_data()
display_camera = st.selectbox("Select Camera Model:", list(cameras.keys()))
camera = cameras[display_camera]

# Safe defaults so IV3-400CA does not crash
default_distance = clamp(250, camera["min_dist"], camera["max_dist"])
default_target_fov_h = clamp(100, camera["min_fov_x"], camera["max_fov_x"])
default_target_fov_v = clamp(100, camera["min_fov_y"], camera["max_fov_y"])
default_resolution_fov_h = clamp(100, camera["min_fov_x"], camera["max_fov_x"])
default_resolution_fov_v = clamp(100, camera["min_fov_y"], camera["max_fov_y"])

col1, col2 = st.columns([2, 1])

with col1:
    st.header("Calculations")

    calc_fov = st.checkbox("Calculate FOV from Mounting Distance", value=True)
    calc_distance = st.checkbox("Calculate Mounting Distance for Target FOV", value=False)

    if calc_distance:
        st.subheader("🎯 Mounting Distance for Target FOV")

        target_fov_h = st.number_input(
            "Desired Horizontal FOV (mm):",
            min_value=int(camera["min_fov_x"]),
            max_value=int(camera["max_fov_x"]),
            value=int(default_target_fov_h),
            step=5,
            key="target_fov_h",
        )
        distance_h = calculate_mounting_distance(
            target_fov_h,
            camera["min_fov_x"],
            camera["max_fov_x"],
            camera["min_dist"],
            camera["max_dist"],
        )
        st.success(f"📏 Required mounting distance for horizontal FOV: {distance_h:.2f} mm")

        target_fov_v = st.number_input(
            "Desired Vertical FOV (mm):",
            min_value=int(camera["min_fov_y"]),
            max_value=int(camera["max_fov_y"]),
            value=int(default_target_fov_v),
            step=5,
            key="target_fov_v",
        )
        distance_v = calculate_mounting_distance(
            target_fov_v,
            camera["min_fov_y"],
            camera["max_fov_y"],
            camera["min_dist"],
            camera["max_dist"],
        )
        st.success(f"📏 Required mounting distance for vertical FOV: {distance_v:.2f} mm")

    if calc_fov:
        st.subheader("📸 FOV from Mounting Distance")

        distance = st.number_input(
            "Mounting Distance (mm):",
            min_value=int(camera["min_dist"]),
            max_value=int(camera["max_dist"]),
            value=int(default_distance),
            step=10,
            key="distance_input",
        )

        fov_x, fov_y = calculate_fov_x_y(
            distance,
            camera["min_fov_x"],
            camera["max_fov_x"],
            camera["min_fov_y"],
            camera["max_fov_y"],
            camera["min_dist"],
            camera["max_dist"],
        )

        st.success(f"📸 Estimated FOV Horizontal (X): {fov_x:.2f} mm")
        st.success(f"📸 Estimated FOV Vertical (Y): {fov_y:.2f} mm")

        res_mm_h_auto, res_px_h_auto = calculate_resolution_metrics(fov_x, camera["resolution_h"])
        res_mm_v_auto, res_px_v_auto = calculate_resolution_metrics(fov_y, camera["resolution_v"])

        st.write("### 🔬 Resolution at this distance")
        st.write(f"**Horizontal:** {res_mm_h_auto:.4f} mm/px  |  {res_px_h_auto:.2f} px/mm")
        st.write(f"**Vertical:** {res_mm_v_auto:.4f} mm/px  |  {res_px_v_auto:.2f} px/mm")

    st.markdown("---")

    st.subheader("🧮 Manual Resolution Calculation")

    actual_fov_h = st.number_input(
        "Actual Horizontal FOV Width (mm):",
        min_value=int(camera["min_fov_x"]),
        max_value=int(camera["max_fov_x"]),
        value=int(default_resolution_fov_h),
        step=5,
        key="actual_fov_h",
    )
    res_mm_h, res_px_h = calculate_resolution_metrics(actual_fov_h, camera["resolution_h"])

    actual_fov_v = st.number_input(
        "Actual Vertical FOV Height (mm):",
        min_value=int(camera["min_fov_y"]),
        max_value=int(camera["max_fov_y"]),
        value=int(default_resolution_fov_v),
        step=5,
        key="actual_fov_v",
    )
    res_mm_v, res_px_v = calculate_resolution_metrics(actual_fov_v, camera["resolution_v"])

    st.write("### 🔬 Resolution Results")
    st.success(f"Horizontal: {res_mm_h:.4f} mm/px")
    st.success(f"Horizontal: {res_px_h:.2f} px/mm")
    st.success(f"Vertical: {res_mm_v:.4f} mm/px")
    st.success(f"Vertical: {res_px_v:.2f} px/mm")

    if "specs" in camera:
        with st.expander("📋 Camera Specifications", expanded=False):
            df = pd.DataFrame(camera["specs"].items(), columns=["Specification", "Value"])
            st.table(df)

with col2:
    st.header("Camera Model")

    image_path = os.path.join(os.getcwd(), PICTURES_FOLDER, camera["image"])
    if os.path.exists(image_path):
        try:
            image = Image.open(image_path)
            st.image(image, caption=f"{display_camera} Camera", width="stretch")
        except Exception as exc:
            st.error(f"Failed to load image: {exc}")
    else:
        st.error(
            f"Image not found: '{camera['image']}'. Put it in the '{PICTURES_FOLDER}' folder."
        )

st.markdown("<div style='margin-bottom:50px;'></div>", unsafe_allow_html=True)
st.markdown(FOOTER_HTML, unsafe_allow_html=True)
