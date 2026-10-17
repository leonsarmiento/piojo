"""
PIOJÓ — Mapa Web Interactivo
Áreas de Vida del municipio de Piojó, Valle del Cauca (Colombia)
"""

import json
from pathlib import Path

import folium
import pandas as pd
import streamlit as st
from streamlit.components.v1 import html as st_html

st.set_page_config(
    page_title="PIOJÓ · Mapa Web",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_DIR = Path(__file__).parent / "data"

# ------------------------- Capas -------------------------
# Cada capa: color base, icono y descripción
LAYERS = [
    {
        "id": "Limite_Piojo",
        "name": "Límite Municipal",
        "color": "#FF0000",
        "icon": "🏛️",
        "desc": "Polígono del municipio de Piojó",
    },
    {
        "id": "Areas_de_Vida_Priorizadas",
        "name": "Áreas de Vida Priorizadas",
        "color": "#8E44AD",
        "icon": "🌱",
        "desc": "Áreas de vida priorizadas de PIOJÓ",
    },
    {
        "id": "humedales",
        "name": "Humedales",
        "color": "#00A8E8",
        "icon": "💧",
        "desc": "Humedales del municipio",
    },
    {
        "id": "SINAP",
        "name": "SINAP (Parques Naturales)",
        "color": "#27AE60",
        "icon": "🌳",
        "desc": "Sistema Nacional de Áreas Protegidas",
    },
    {
        "id": "Area_Zonas_Siembra",
        "name": "Zonas de Siembra",
        "color": "#F39C12",
        "icon": "🌾",
        "desc": "Áreas de zonas de siembra",
    },
    {
        "id": "Suceptibilidad_Erosion",
        "name": "Susceptibilidad a Erosión (ALTA y MUY ALTA)",
        "color": "#C0392B",
        "icon": "⚠️",
        "desc": "Polígonos con susceptibilidad ALTA o MUY ALTA a erosión",
    },
]

OPACITY = 0.5  # transparencia 50 % (opacidad 50 %)

# ------------------------- Carga de datos -------------------------
@st.cache_data
def load_layer(path: str):
    with open(DATA_DIR / f"{path}.geojson", "r", encoding="utf-8") as f:
        return json.load(f)

def _bbox(gj: dict):
    """Devuelve [[lat_min, lon_min], [lat_max, lon_max]] de un GeoJSON."""
    minx = miny = float("inf")
    maxx = maxy = float("-inf")

    def walk(coords):
        nonlocal minx, miny, maxx, maxy
        if isinstance(coords[0], (int, float)):
            minx, maxx = min(minx, coords[0]), max(maxx, coords[0])
            miny, maxy = min(miny, coords[1]), max(maxy, coords[1])
        else:
            for c in coords:
                walk(c)

    for feat in gj["features"]:
        walk(feat["geometry"]["coordinates"])
    return [[miny, minx], [maxy, maxx]]

def build_map(active_ids: tuple, basemap: str):
    gdf_map = folium.Map(
        location=[4.14, -76.30],  # centro aproximado de Piojó (respaldo)
        zoom_start=13,
        tiles=None,
    )

    # ---------- Centrar en el límite municipal ----------
    gdf_map.fit_bounds(_bbox(load_layer("Limite_Piojo")))

    # ---------- Fondo ----------
    if basemap == "OpenStreetMap":
        folium.TileLayer(
            tiles="OpenStreetMap",
            attr="© OpenStreetMap contributors",
            name="OpenStreetMap",
        ).add_to(gdf_map)
    else:  # Bing Satellite
        # plugin leaflet.bing (requerido para el esquema quadkey de Bing)
        gdf_map.get_root().html.add_child(
            folium.Element(
                '<script src="https://cdn.jsdelivr.net/npm/leaflet.bing@1.3.2/src/leaflet.bing.js"></script>'
            )
        )
        gdf_map.get_root().html.add_child(
            folium.Element(
                f"""
                <script>
                var bingSat = L.tileLayer.bing('Satellite', {{
                    name: 'Bing Satellite',
                    attribution: '© Microsoft Bing',
                    maxZoom: 20
                }});
                bingSat.addTo(map_{gdf_map._id});
                </script>
                """
            )
        )

    # ---------- Capas vectoriales ----------
    for lyr in LAYERS:
        if lyr["id"] not in active_ids:
            continue
        gj = load_layer(lyr["id"])
        folium.GeoJson(
            gj,
            style_function=lambda _f, c=lyr["color"]: {
                "color": c,
                "weight": 2,
                "fillColor": c,
                "fillOpacity": OPACITY,
                "opacity": OPACITY,
            },
        ).add_to(gdf_map)

    return gdf_map

# ------------------------- UI -------------------------
st.title("🗺️ PIOJÓ — Mapa Web de Áreas de Vida")
st.caption(
    "Municipio de Piojó, Valle del Cauca, Colombia · "
    "Capas vectoriales sobre fondo OpenStreetMap o Bing Satellite"
)

with st.sidebar:
    st.header("⚙️ Configuración")

    st.subheader("🗺️ Fondo del mapa")
    basemap = st.radio(
        "Selecciona el fondo",
        ["OpenStreetMap", "Bing Satellite"],
        index=1,
    )

    st.subheader("📚 Capas")
    st.caption("Activa o desactiva las capas (todas con 50 % de opacidad)")
    active = {}
    for lyr in LAYERS:
        active[lyr["id"]] = st.checkbox(
            f"{lyr['icon']} {lyr['name']}",
            value=True,
            help=lyr["desc"],
        )

    st.subheader("ℹ️ Leyenda")
    for lyr in LAYERS:
        if active[lyr["id"]]:
            st.markdown(
                f"<div style='display:flex;align-items:center;gap:8px'>"
                f"<span style='background:{lyr['color']};opacity:0.5;width:16px;height:16px;border-radius:3px;display:inline-block'></span>"
                f"{lyr['icon']} {lyr['name']}</div>",
                unsafe_allow_html=True,
            )

active_ids = tuple(k for k, v in active.items() if v)

st.info(
    "💡 Haz clic en los polígonos para ver sus atributos.",
    icon="💡",
)

if active_ids:
    m = build_map(active_ids, basemap)
    st.dataframe(
        pd.DataFrame(
            {
                "Capa": [l["name"] for l in LAYERS if l["id"] in active_ids],
                "Color": [l["color"] for l in LAYERS if l["id"] in active_ids],
                "Opacidad": ["50 %" for _ in active_ids],
            }
        ),
        width="stretch",
        hide_index=True,
    )
    st_html(m._repr_html_(), height=750)
else:
    st.warning("⚠️ Activa al menos una capa en el panel lateral para ver el mapa.")

st.divider()
st.caption(
    "Datos: Capas vectoriales del proyecto PIOJÓ · "
    "Desplegado en Streamlit Community Cloud"
)
