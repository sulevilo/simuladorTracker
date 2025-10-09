import streamlit as st
import folium
import math
import pandas as pd
from datetime import datetime, timezone
from streamlit_folium import st_folium

# --- FUNCIONES MATEMÁTICAS ---
R = 6371.0  # Radio promedio de la Tierra en km

def haversine_km(lat1, lon1, lat2, lon2):
    """Distancia entre dos puntos geográficos (km)."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.asin(math.sqrt(a))

def bearing_deg(lat1, lon1, lat2, lon2):
    """Rumbo inicial desde punto 1 hacia punto 2 (grados)."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dlambda = math.radians(lon2 - lon1)
    x = math.sin(dlambda) * math.cos(phi2)
    y = math.cos(phi1)*math.sin(phi2) - math.sin(phi1)*math.cos(phi2)*math.cos(dlambda)
    return (math.degrees(math.atan2(x, y)) + 360) % 360

def knots_to_kmh(knots):
    """Conversión de velocidad: nudos → km/h."""
    return knots * 1.852


# --- PUNTOS DE REFERENCIA ---
start_lat, start_lon = 37.2311, 15.2242  # Salida (ejemplo)
dest_lat, dest_lon = 31.5, 34.47         # Destino: Gaza

# --- INICIALIZAR BITÁCORA ---
if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame(columns=[
        "timestamp", "lat", "lon", "speed_knots", "course",
        "distancia_km", "ETA_h", "bearing"
    ])

# --- TÍTULO ---
st.title("Tracker interactivo con bitácora y mapa")

# --- FORMULARIO DE ENTRADA ---
with st.form("input_form"):
    col1, col2 = st.columns(2)
    lat = col1.number_input("Latitud", value=31.9621, format="%.4f")
    lon = col2.number_input("Longitud", value=33.2487, format="%.4f")

    col3, col4 = st.columns(2)
    speed = col3.number_input("Velocidad (knots)", value=8.86, format="%.2f")
    course = col4.number_input("Course (°)", value=112.5, format="%.2f")

    submitted = st.form_submit_button("➕ Agregar posición")

# --- LÓGICA DE CÁLCULO ---
if submitted:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    dist_rest = haversine_km(lat, lon, dest_lat, dest_lon)
    v_kmh = knots_to_kmh(speed)
    eta_h = dist_rest / v_kmh if v_kmh > 0 else float("inf")
    bearing = bearing_deg(lat, lon, dest_lat, dest_lon)

    # Guardar en bitácora
    st.session_state.df.loc[len(st.session_state.df)] = [
        now, lat, lon, speed, course, dist_rest, eta_h, bearing
    ]

# --- MOSTRAR MAPA ---
if not st.session_state.df.empty:
    df = st.session_state.df
    lat_last, lon_last = df.iloc[-1][["lat", "lon"]]

    m = folium.Map(location=[lat_last, lon_last], zoom_start=6)

    # Marcadores de referencia
    folium.Marker([start_lat, start_lon], popup="Inicio (Salida)", icon=folium.Icon(color="blue")).add_to(m)
    folium.Marker([dest_lat, dest_lon], popup="Destino (Gaza)", icon=folium.Icon(color="red")).add_to(m)

    # Trayectoria
    for i, row in df.iterrows():
        folium.Marker(
            [row["lat"], row["lon"]],
            popup=(f"Registro {i+1}<br>"
                   f"Hora: {row['timestamp']}<br>"
                   f"Vel: {row['speed_knots']} kn<br>"
                   f"Course: {row['course']}°<br>"
                   f"Dist: {row['distancia_km']:.2f} km<br>"
                   f"ETA: {row['ETA_h']:.2f} h<br>"
                   f"Bearing: {row['bearing']:.2f}°"),
            icon=folium.Icon(color="green")
        ).add_to(m)

    folium.PolyLine(
        [(start_lat, start_lon)] + df[["lat","lon"]].values.tolist() + [(dest_lat, dest_lon)],
        color="purple", weight=3
    ).add_to(m)

    st.subheader("Mapa del trayecto")
    st_folium(m, width=700, height=500)

    st.subheader("Bitácora de posiciones")
    st.dataframe(df)
else:
    st.info("Aún no hay posiciones registradas.")
