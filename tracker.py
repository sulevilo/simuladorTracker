 # ========================================
# Tracker interactivo con bitácora avanzada y mapa
# ========================================

!pip install folium --quiet


import folium              # Mapas interactivos
import math                # Cálculos matemáticos (haversine, trigonometría)
import pandas as pd        # Tablas (bitácora de posiciones)
from datetime import datetime, timezone  # Manejo de fechas con zona horaria (UTC)
from ipywidgets import widgets, Button, VBox, HBox, Output, Layout
from IPython.display import display, clear_output


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


# --- BITÁCORA VACÍA ---
df = pd.DataFrame(columns=[
    "timestamp", "lat", "lon", "speed_knots", "course",
    "distancia_km", "ETA_h", "bearing"
])


# --- WIDGETS ---
lat_input = widgets.FloatText(description="Lat:", value=31.9621)
lon_input = widgets.FloatText(description="Lon:", value=33.2487)
speed_input = widgets.FloatText(description="Vel (knots):", value=8.86)
course_input = widgets.FloatText(description="Course (°):", value=112.5)


add_button = Button(description="➕ Agregar posición", button_style="success", layout=Layout(width="200px"))
out = Output()




# --- FUNCIÓN DE MAPA ---
def mostrar_mapa():
    global df
    with out:
        clear_output(wait=True)

        if df.empty:
            print("No hay posiciones registradas todavía.")
            return


        # Último registro
        lat, lon = df.iloc[-1][["lat", "lon"]]


        # Crear mapa
        m = folium.Map(location=[lat, lon], zoom_start=6)


        # Marcadores de referencia
        folium.Marker([start_lat, start_lon], popup="Inicio (Salida)", icon=folium.Icon(color="blue")).add_to(m)
        folium.Marker([dest_lat, dest_lon], popup="Destino (Gaza)", icon=folium.Icon(color="red")).add_to(m)


        # Recorrido con posiciones ingresadas
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


        # Línea conectando el trayecto
        folium.PolyLine(
            [(start_lat, start_lon)] + df[["lat","lon"]].values.tolist() + [(dest_lat, dest_lon)],
            color="purple", weight=3
        ).add_to(m)


        # Mostrar mapa y bitácora
        display(m)
        print("\n=== Bitácora de posiciones ===")
        display(df)




# --- FUNCIÓN PARA AGREGAR POSICIÓN ---
def add_position(b):
    global df
    # Timestamp correcto con zona horaria UTC
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    # Datos ingresados
    lat, lon = lat_input.value, lon_input.value
    spd, course = speed_input.value, course_input.value

    # Cálculos
    dist_rest = haversine_km(lat, lon, dest_lat, dest_lon)
    v_kmh = knots_to_kmh(spd)
    eta_h = dist_rest / v_kmh if v_kmh > 0 else float("inf")
    bearing = bearing_deg(lat, lon, dest_lat, dest_lon)

    # Guardar en bitácora
    df.loc[len(df)] = [now, lat, lon, spd, course, dist_rest, eta_h, bearing]

    # Refrescar mapa
    mostrar_mapa()




# --- ENLACE BOTÓN ---
add_button.on_click(add_position)


# --- INTERFAZ ---
display(VBox([
    HBox([lat_input, lon_input]),
    HBox([speed_input, course_input]),
    add_button,
    out
]))
