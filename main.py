import streamlit as st
from PIL import Image
import os
import pandas as pd

# Define constants for better readability and maintainability
PICTURES_FOLDER = "Pictures"

# --- Calculation Functions ---

def calculate_resolution_metrics(fov_mm, pixel_dimension):
    """Calculates resolution in mm/pixel and pixels/mm for a given dimension."""
    if pixel_dimension == 0:
        return 0.0, 0.0 # Avoid division by zero
    resolution_mm_per_pixel = fov_mm / pixel_dimension
    resolution_pixels_per_mm = 1 / resolution_mm_per_pixel if resolution_mm_per_pixel != 0 else 0.0
    return resolution_mm_per_pixel, resolution_pixels_per_mm

def linear_interpolation(value, min_val_in, max_val_in, min_val_out, max_val_out):
    """Performs linear interpolation."""
    if (max_val_in - min_val_in) == 0:
        return min_val_out # Avoid division by zero, return min_val_out if range is zero
    
    # Clamp the input value to stay within the known range
    value = max(min_val_in, min(max_val_in, value))
    
    # Calculate the interpolated value
    return min_val_out + (value - min_val_in) * (max_val_out - min_val_out) / (max_val_in - min_val_in)

# --- Camera Data ---
@st.cache_data
def get_camera_data():
    return {
        "IV3-G500CA": {
            "image": "iv4-g500ca.png",
            "min_fov_x": 22, "max_fov_x": 1184,
            "min_fov_y": 16, "max_fov_y": 888,
            "min_dist": 50, "max_dist": 3000,
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
                 "Lighting Method": "Pulse /continuous lighting is switchable",
                 "Enclosure Rating": "IP67",
                 "Temperature Range": "0 to +50°C (No freezing)",
                 "Relative Humidity": "35 to 85% RH (No condensation)",
                 "Vibration Resistance": "10 to 55 Hz; double amplitude 1.5 mm, 2 hours in each direction",
                 "Shock Resistance": "500 m/s², 3 times in each of the 6 directions",
                 "Material": "Main unit case: Zinc die-casting, Front cover: Acrylic, Operation indicator cover: TPU",
                 "Weight": "Approx. 75 g (without AI Lighting), Approx. 225 g (with AI Lighting)"
            }
        },
        "IV3-G600MA": {
            "image": "iv4-g600ca.png",
            "min_fov_x": 51, "max_fov_x": 2730,
            "min_fov_y": 38, "max_fov_y": 2044,
            "min_dist": 50, "max_dist": 3000,
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
                "Weight": "Approx. 75 g (without AI Lighting)"
            }
        }
    }

# Add custom CSS for fixed footer
footer_html = """
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

# --- Streamlit App UI ---
st.set_page_config(page_title="Keyence Camera Calculator", layout="wide")
st.title("🔍 Keyence Camera Resolution & Mounting Distance Calculator")

cameras = get_camera_data()
display_camera = st.selectbox("Select Camera Model:", list(cameras.keys()))
camera = cameras[display_camera]

# Calculate the pixel aspect ratio for the selected camera
# This is used to maintain aspect ratio when one FOV is changed
if camera["resolution_v"] != 0:
    pixel_aspect_ratio = camera["resolution_h"] / camera["resolution_v"]
else:
    pixel_aspect_ratio = 1.0 # Default to 1:1 if vertical resolution is zero (shouldn't happen)

col1, col2 = st.columns([2, 1])

with col1:
    st.header("Calculations")

    # Primary Input: Mounting Distance for FOV & Resolution Calculations
    current_distance = st.number_input(
        "Enter Current Mounting Distance (mm):",
        min_value=camera["min_dist"],
        max_value=camera["max_dist"],
        value=100,
        step=5,
        help=f"Enter the actual distance from the camera to the target. Min: {camera['min_dist']}mm, Max: {camera['max_dist']}mm."
    )

    # Clamp the current_distance to ensure it's within the camera's operating range
    current_distance_clamped = max(camera["min_dist"], min(camera["max_dist"], current_distance))

    # Calculate FOV based on the entered distance
    fov_x_at_dist = linear_interpolation(
        current_distance_clamped, camera["min_dist"], camera["max_dist"],
        camera["min_fov_x"], camera["max_fov_x"]
    )
    fov_y_at_dist = linear_interpolation(
        current_distance_clamped, camera["min_dist"], camera["max_dist"],
        camera["min_fov_y"], camera["max_fov_y"]
    )

    st.subheader("📸 Estimated Field of View (FoV) at current distance:")
    st.info(f"**Horizontal (X):** {fov_x_at_dist:.2f} mm")
    st.info(f"**Vertical (Y):** {fov_y_at_dist:.2f} mm")

    st.subheader("🔬 Resolution Results at current distance:")
    res_mm_h, res_px_h = calculate_resolution_metrics(fov_x_at_dist, camera["resolution_h"])
    res_mm_v, res_px_v = calculate_resolution_metrics(fov_y_at_dist, camera["resolution_v"])

    st.success(f"**Horizontal Resolution (aligned with H FOV):**")
    st.write(f"&nbsp;&nbsp;&nbsp;&nbsp;**{res_mm_h:.4f} mm/px** (Millimeters per pixel)")
    st.write(f"&nbsp;&nbsp;&nbsp;&nbsp;**{res_px_h:.2f} px/mm** (Pixels per millimeter)")

    st.success(f"**Vertical Resolution (aligned with V FOV):**")
    st.write(f"&nbsp;&nbsp;&nbsp;&nbsp;**{res_mm_v:.4f} mm/px** (Millimeters per pixel)")
    st.write(f"&nbsp;&nbsp;&nbsp;&nbsp;**{res_px_v:.2f} px/mm** (Pixels per millimeter)")


    st.markdown("---") # Separator for better visual grouping

    # Option to calculate required distance for a target FOV (for both H and V)
    st.subheader("🎯 Calculate Mounting Distance for a Target FOV:")
    target_fov_enable = st.checkbox("Enable Target FOV Calculation Mode")

    if target_fov_enable:
        st.info("Enter your desired FOV for one dimension. The other dimension will update automatically based on the camera's aspect ratio.")
        
        # Initialize session state for target FOVs if not already present
        if 'target_fov_h_input' not in st.session_state:
            st.session_state.target_fov_h_input = camera["min_fov_x"]
        if 'target_fov_y_input' not in st.session_state:
            st.session_state.target_fov_y_input = camera["min_fov_y"]
        
        # Callback to update vertical FOV when horizontal is changed
        def update_vertical_from_horizontal():
            if 'target_fov_h_input' in st.session_state:
                new_h = st.session_state.target_fov_h_input
                # Calculate corresponding vertical FOV
                new_y = new_h / pixel_aspect_ratio
                # Clamp to camera's min/max vertical FOV range
                st.session_state.target_fov_y_input = max(camera["min_fov_y"], min(camera["max_fov_y"], new_y))

        # Callback to update horizontal FOV when vertical is changed
        def update_horizontal_from_vertical():
            if 'target_fov_y_input' in st.session_state:
                new_y = st.session_state.target_fov_y_input
                # Calculate corresponding horizontal FOV
                new_h = new_y * pixel_aspect_ratio
                # Clamp to camera's min/max horizontal FOV range
                st.session_state.target_fov_h_input = max(camera["min_fov_x"], min(camera["max_fov_x"], new_h))

        # Allow user to choose which FOV they want to input directly
        primary_input_choice = st.radio(
            "Which FOV do you want to set?",
            ("Horizontal FOV", "Vertical FOV"),
            key="primary_fov_choice"
        )

        if primary_input_choice == "Horizontal FOV":
            st.number_input(
                "Desired Horizontal FOV (mm):",
                min_value=camera["min_fov_x"],
                max_value=camera["max_fov_x"],
                value=st.session_state.target_fov_h_input,
                step=5,
                key="target_fov_h_input", # Link to session state
                on_change=update_vertical_from_horizontal, # Call this when input changes
                help=f"Set the desired horizontal field of view. The vertical FOV will adjust automatically. Min: {camera['min_fov_x']}mm, Max: {camera['max_fov_x']}mm."
            )
            # Display the automatically updated vertical FOV
            st.info(f"**Corresponding Vertical FOV (Y):** {st.session_state.target_fov_y_input:.2f} mm (auto-calculated)")
        else: # primary_input_choice == "Vertical FOV"
            st.number_input(
                "Desired Vertical FOV (mm):",
                min_value=camera["min_fov_y"],
                max_value=camera["max_fov_y"],
                value=st.session_state.target_fov_y_input,
                step=5,
                key="target_fov_y_input", # Link to session state
                on_change=update_horizontal_from_vertical, # Call this when input changes
                help=f"Set the desired vertical field of view. The horizontal FOV will adjust automatically. Min: {camera['min_fov_y']}mm, Max: {camera['max_fov_y']}mm."
            )
            # Display the automatically updated horizontal FOV
            st.info(f"**Corresponding Horizontal FOV (X):** {st.session_state.target_fov_h_input:.2f} mm (auto-calculated)")

        # Display the calculated mounting distances for both FOVs (based on session state values)
        # Calculate distance for Target Horizontal FOV
        estimated_distance_h = linear_interpolation(
            st.session_state.target_fov_h_input, camera["min_fov_x"], camera["max_fov_x"],
            camera["min_dist"], camera["max_dist"]
        )
        st.success(f"📏 **Distance for {st.session_state.target_fov_h_input:.2f}mm Horizontal FOV:** {estimated_distance_h:.2f} mm")

        # Calculate distance for Target Vertical FOV
        estimated_distance_y = linear_interpolation(
            st.session_state.target_fov_y_input, camera["min_fov_y"], camera["max_fov_y"],
            camera["min_dist"], camera["max_dist"]
        )
        st.success(f"📏 **Distance for {st.session_state.target_fov_y_input:.2f}mm Vertical FOV:** {estimated_distance_y:.2f} mm")


    # Camera Specifications as an Expander
    if "specs" in camera:
        with st.expander("📋 View Camera Specifications"):
            df = pd.DataFrame(camera["specs"].items(), columns=["Specification", "Value"])
            st.table(df)

with col2:
    st.header("Camera Model")
    # Display Camera Image
    image_path = os.path.join(os.getcwd(), PICTURES_FOLDER, camera["image"])

    if not os.path.exists(image_path):
        st.error(f"Error loading image. Please ensure '{camera['image']}' is in the '{PICTURES_FOLDER}/' folder.")
    else:
        try:
            image = Image.open(image_path)
            st.image(image, caption=f"{display_camera} Camera", use_column_width=True) # Use_column_width for better scaling
        except Exception as e:
            st.error(f"Failed to display image. Error: {e}")

# Add some space before footer to ensure content isn't hidden
st.markdown("<div style='margin-bottom:50px;'></div>", unsafe_allow_html=True)

# Inject CSS and HTML for fixed footer
st.markdown(footer_html, unsafe_allow_html=True)
