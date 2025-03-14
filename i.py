import streamlit as st
from PIL import Image
import os
import pandas as pd

def calculate_resolution(fov_h, image_width=1280):
    """Calculates resolution in mm/pixel and pixels/mm."""
    resolution_mm_per_pixel = fov_h / image_width
    resolution_pixels_per_mm = 1 / resolution_mm_per_pixel
    return resolution_mm_per_pixel, resolution_pixels_per_mm

def calculate_mounting_distance(target_fov, min_fov, max_fov, min_dist, max_dist):
    """Estimates mounting distance for a given FOV."""
    slope = (max_fov - min_fov) / (max_dist - min_dist)
    distance = ((target_fov - min_fov) / slope) + min_dist
    return distance

def calculate_fov_from_distance(distance, min_fov, max_fov, min_dist, max_dist):
    """Estimates FOV for a given mounting distance."""
    slope = (max_fov - min_fov) / (max_dist - min_dist)
    fov = (distance - min_dist) * slope + min_fov
    return fov

def calculate_fov_x_y(distance, min_fov_x, max_fov_x, min_fov_y, max_fov_y, min_dist, max_dist):
    """Calculates FOV in X (horizontal) and Y (vertical) directions."""
    slope_x = (max_fov_x - min_fov_x) / (max_dist - min_dist)
    slope_y = (max_fov_y - min_fov_y) / (max_dist - min_dist)
    
    fov_x = (distance - min_dist) * slope_x + min_fov_x
    fov_y = (distance - min_dist) * slope_y + min_fov_y
    
    return fov_x, fov_y

# Camera Options
cameras = {
    "IV3-G500CA": {
        "image": "iv4.png",
        "min_fov_x": 22, "max_fov_x": 1184,
        "min_fov_y": 16, "max_fov_y": 888,
        "min_dist": 50, "max_dist": 3000
    },
    "IV3-G600MA": {
        "image": "iv3.png",
        "min_fov_x": 51, "max_fov_x": 2730,
        "min_fov_y": 38, "max_fov_y": 2044,
        "min_dist": 50, "max_dist": 3000,
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
            "Weight": "Approx. 75 g (without AI Lighting)"
        }
    }
}

# Streamlit App UI
st.set_page_config(page_title="Keyence Camera Calculator", layout="wide")
st.title("🔍 Keyence Camera Resolution & Mounting Distance Calculator")

# Camera Selection
display_camera = st.selectbox("Select Camera Model:", list(cameras.keys()))
camera = cameras[display_camera]

col1, col2 = st.columns([2, 1])

with col1:
    # User options
    calculate_fov = st.checkbox("Calculate FOV from Mounting Distance")
    calculate_distance = st.checkbox("Calculate Mounting Distance for Target FOV")

    # User inputs
    if calculate_distance:
        target_fov = st.number_input("Enter Desired Horizontal FOV (mm):", min_value=camera["min_fov_x"], max_value=camera["max_fov_x"], value=100, step=5)
        distance = calculate_mounting_distance(target_fov, camera["min_fov_x"], camera["max_fov_x"], camera["min_dist"], camera["max_dist"])
        st.success(f"📏 Required Mounting Distance: {distance:.2f} mm")

    if calculate_fov:
        distance = st.number_input("Enter Mounting Distance (mm):", min_value=camera["min_dist"], max_value=camera["max_dist"], value=250, step=10)
        fov_h = calculate_fov_from_distance(distance, camera["min_fov_x"], camera["max_fov_x"], camera["min_dist"], camera["max_dist"])
        fov_x, fov_y = calculate_fov_x_y(distance, camera["min_fov_x"], camera["max_fov_x"], camera["min_fov_y"], camera["max_fov_y"], camera["min_dist"], camera["max_dist"])
        st.success(f"📸 Estimated FOV Width: {fov_h:.2f} mm")
        st.success(f"📸 Estimated FOV (X: Horizontal) = {fov_x:.2f} mm")
        st.success(f"📸 Estimated FOV (Y: Vertical) = {fov_y:.2f} mm")

    # Resolution Calculation
    fov_h = st.number_input("Enter Actual FOV Width (mm) for Resolution Calculation:", min_value=camera["min_fov_x"], max_value=camera["max_fov_x"], value=100, step=5)
    resolution_mm, resolution_px = calculate_resolution(fov_h)

    st.write("### 🔬 Resolution Results:")
    st.success(f"🖥️ Resolution (mm per pixel): {resolution_mm:.4f} mm/px")
    st.success(f"📊 Resolution (pixels per mm): {resolution_px:.2f} px/mm")

    if "specs" in camera:
        st.write("### 📋 Camera Specifications:")
        df = pd.DataFrame(camera["specs"].items(), columns=["Specification", "Value"])
        st.table(df)

with col2:
    # Display Camera Image
    image_path = os.path.join(os.getcwd(), "Pictures", camera["image"])
    if os.path.exists(image_path):
        image = Image.open(image_path)
        st.image(image, caption=f"{display_camera} Camera", width=250)
    else:
        st.error("Error loading image. Make sure the file exists in the 'Pictures/' folder and is accessible.")
