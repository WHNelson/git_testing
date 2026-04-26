import streamlit as st
import numpy as np
import math
import simplekml
import base64

def calculate_hata_range(freq, erp_watts, sensitivity, h_t, h_r):
    # 1. Convert ERP Watts to dBm
    tx_power_dbm = 10 * np.log10(erp_watts * 1000)
    max_path_loss = tx_power_dbm - sensitivity

    # 2. Hata Correction factor for small/medium city (a_hr)
    a_hr = (1.1 * np.log10(freq) - 0.7) * h_r - (1.56 * np.log10(freq) - 0.8)
    
    # 3. Hata Constant Parts (Urban Model)
    # L = A + B * log10(d)
    A = 69.55 + 26.16 * np.log10(freq) - 13.82 * np.log10(h_t) - a_hr
    B = 44.9 - 6.55 * np.log10(h_t)
    
    # 4. Solve for distance d (km)
    d_km = 10**((max_path_loss - A) / B)
    
    # 5. Calculate Radio Horizon (The physical "Hard Limit")
    # Formula: d = 1.41 * (sqrt(h_t_ft) + sqrt(h_r_ft))
    h_t_ft = h_t * 3.28084
    h_r_ft = h_r * 3.28084
    horizon_miles = 1.41 * (math.sqrt(h_t_ft) + math.sqrt(h_r_ft))
    horizon_km = horizon_miles * 1.60934
    
    # Use the smaller of the two (Physics vs. Power)
    final_radius = min(d_km, horizon_km)
    return final_radius, horizon_km

def create_kml(lat, lon, radius_km):
    kml = simplekml.Kml()
    points = []
    # Create 72 points for a smooth circle (every 5 degrees)
    for i in range(0, 365, 5):
        angle = math.radians(i)
        # Lat/Lon distance approximation
        dy = (radius_km / 111.32) * math.sin(angle)
        dx = (radius_km / (111.32 * math.cos(math.radians(lat)))) * math.cos(angle)
        points.append((lon + dx, lat + dy))
    
    pol = kml.newpolygon(name="RF Coverage Area")
    pol.outerboundaryis = points
    # KML color format: AABBGGRR (Alpha, Blue, Green, Red)
    pol.style.polystyle.color = '660000ff'  # Semi-transparent red
    pol.style.linestyle.width = 2
    pol.style.linestyle.color = 'ff0000ff'  # Solid red border
    return kml.kml()

# --- STREAMLIT UI ---
st.set_page_config(page_title="RF Coverage Mapper", layout="centered")
st.title("📡 RF Coverage Estimator")
st.markdown("Generates a **Hata-Okumura** coverage circle for Google Earth.")

# Input Layout
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Location")
    lat = st.number_input("Latitude", value=34.0522, format="%.6f")
    lon = st.number_input("Longitude", value=-118.2437, format="%.6f")
    h_t = st.number_input("TX Antenna Height (Meters)", value=30.0)
    h_r = st.number_input("RX Antenna Height (Meters)", value=1.5)

with col_b:
    st.subheader("Hardware")
    freq = st.number_input("Frequency (MHz)", value=800.0)
    erp = st.number_input("Transmitter ERP (Watts)", value=20.0)
    sens = st.number_input("Receiver Sensitivity (dBm)", value=-116.0)

# Calculations
radius_km, horizon_km = calculate_hata_range(freq, erp, sens, h_t, h_r)
radius_mi = radius_km * 0.621371

# Results Display
st.divider()
c1, c2 = st.columns(2)
c1.metric("Coverage Radius", f"{radius_mi:.2f} miles")
c2.metric("Radio Horizon", f"{horizon_km * 0.621371:.2f} miles")

# KML Download
kml_data = create_kml(lat, lon, radius_km)
b64 = base64.b64encode(kml_data.encode()).decode()
href = f'<a href="data:application/vnd.google-earth.kml+xml;base64,{b64}" download="coverage.kml" style="text-decoration:none;"><button style="width:100%; height:50px; background-color:#ff4b4b; color:white; border:none; border-radius:5px; cursor:pointer;">Download KML for Google Earth</button></a>'
st.markdown(href, unsafe_allow_html=True)

st.caption("Note: This model assumes a 'small-to-medium city' urban environment.")
