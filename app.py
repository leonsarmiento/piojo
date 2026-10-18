"""
PIOJÓ — Mapa Web Interactivo
Áreas de Vida del municipio de Piojó, Atlántico (Colombia)
"""

import json
from pathlib import Path

import folium
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
# Symbology por capa: outline (borde), fill (relleno, None = sin relleno),
# dash (trazo punteado) y opacity (opacidad global de la capa)
LAYERS = [
    {
        "id": "Limite_Piojo",
        "name": "Límite Municipal",
        "outline": "#000000",
        "fill": None,
        "dash": "2,8",
        "opacity": 1.0,
        "icon": "🏛️",
        "desc": "Polígono del municipio de Piojó (borde negro punteado, sin relleno)",
    },
    {
        "id": "Areas_de_Vida_Priorizadas",
        "name": "Áreas de Vida Priorizadas",
        "outline": "#FF0000",
        "fill": None,
        "dash": None,
        "opacity": 1.0,
        "icon": "🌱",
        "desc": "Áreas de vida priorizadas de PIOJÓ (borde rojo, sin relleno)",
    },
    {
        "id": "humedales",
        "name": "Humedales",
        "outline": "#ADD8E6",
        "fill": "#90EE90",
        "dash": None,
        "opacity": 0.5,
        "icon": "💧",
        "desc": "Humedales (relleno verde claro, borde azul claro, 50 %)",
    },
    {
        "id": "SINAP",
        "name": "SINAP (Parques Naturales)",
        "outline": "#FFFFFF",
        "fill": "#006400",
        "dash": None,
        "opacity": 0.5,
        "icon": "🌳",
        "desc": "Sistema Nacional de Áreas Protegidas (relleno verde oscuro, borde blanco, 50 %)",
    },
    {
        "id": "Area_Zonas_Siembra",
        "name": "Zonas de Siembra",
        "outline": "#008000",
        "fill": None,
        "dash": None,
        "opacity": 1.0,
        "icon": "🌾",
        "desc": "Áreas de zonas de siembra (borde verde, sin relleno)",
    },
    {
        "id": "Suceptibilidad_Erosion",
        "name": "Susceptibilidad a Erosión (ALTA y MUY ALTA)",
        "outline": None,  # se define por categoría de susceptibilidad
        "fill": None,
        "dash": None,
        "opacity": 0.5,
        "icon": "⚠️",
        "desc": "Polígonos con susceptibilidad ALTA (amarillo) o MUY ALTA (naranja), 50 %",
    },
]

# Relleno por categoría de susceptibilidad a erosión
EROSION_FILLS = {
    "ALTA": "#FFD700",       # amarillo
    "MUY ALTA": "#FF8C00",   # naranja
}

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

def _layer_style(outline: str, fill, opacity: float, dash=None):
    """Estilo de polígono: sin relleno si fill=None."""
    style = {
        "color": outline,
        "weight": 2,
        "opacity": opacity,
        "fill": fill is not None,
        "fillColor": fill if fill is not None else outline,
        "fillOpacity": opacity if fill is not None else 0,
    }
    if dash:
        style["dashArray"] = dash
    return style

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
    else:  # Esri World Imagery (sin API key)
        folium.TileLayer(
            tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            attr="© Esri, Maxar, Earthstar Geographics",
            name="Esri World Imagery",
            max_zoom=19,
        ).add_to(gdf_map)

    # ---------- Capas vectoriales ----------
    for lyr in LAYERS:
        if lyr["id"] not in active_ids:
            continue
        gj = load_layer(lyr["id"])

        if lyr["id"] == "Suceptibilidad_Erosion":
            # relleno según categoría de susceptibilidad (ALTA / MUY ALTA)
            for feat in gj["features"]:
                prop = feat["properties"] or {}
                cat = str(prop.get("suscep", "")).upper()
                color = EROSION_FILLS.get(cat, "#FFD700")
                folium.GeoJson(
                    feat,
                    style_function=lambda _f, c=color: _layer_style(
                        c, c, lyr["opacity"], lyr["dash"]
                    ),
                ).add_to(gdf_map)
        else:
            folium.GeoJson(
                gj,
                style_function=lambda _f, l=lyr: _layer_style(
                    l["outline"], l["fill"], l["opacity"], l["dash"]
                ),
            ).add_to(gdf_map)

    # ---------- Conservar zoom/centro al re-renderizar (localStorage) ----------
    gdf_map.get_root().html.add_child(
        folium.Element(
            f"""
            <script>
            (function () {{
                var KEY = 'piojo_map_view';
                function init() {{
                    var mapObj = window['map_{gdf_map._id}'];
                    if (!mapObj) return;
                    try {{
                        var saved = JSON.parse(localStorage.getItem(KEY) || 'null');
                        if (saved && saved.lat != null) {{
                            mapObj.setView([saved.lat, saved.lng], saved.zoom, {{ animate: false }});
                        }}
                    }} catch (e) {{}}
                    var save = function () {{
                        try {{
                            var c = mapObj.getCenter();
                            localStorage.setItem(KEY, JSON.stringify({{
                                lat: c.lat, lng: c.lng, zoom: mapObj.getZoom()
                            }}));
                        }} catch (e) {{}}
                    }};
                    mapObj.on('moveend', save);
                    mapObj.on('zoomend', save);
                }}
                if (document.readyState === 'loading') {{
                    document.addEventListener('DOMContentLoaded', init);
                }} else {{
                    init();
                }}
            }})();
            </script>
            """
        )
    )

    return gdf_map

# ------------------------- UI -------------------------
st.title("🗺️ PIOJÓ — Mapa Web de Áreas de Vida")
st.caption(
    "Municipio de Piojó, Valle del Cauca, Colombia · "
    "Capas vectoriales sobre fondo OpenStreetMap o Esri World Imagery"
)

with st.sidebar:
    st.header("⚙️ Configuración")

    st.subheader("🗺️ Fondo del mapa")
    basemap = st.radio(
        "Selecciona el fondo",
        ["OpenStreetMap", "Esri World Imagery"],
        index=1,
    )

    st.subheader("📚 Capas")
    st.caption("Activa o desactiva las capas")
    active = {}
    for lyr in LAYERS:
        active[lyr["id"]] = st.checkbox(
            f"{lyr['icon']} {lyr['name']}",
            value=True,
            help=lyr["desc"],
        )

    st.subheader("ℹ️ Leyenda")
    for lyr in LAYERS:
        if not active[lyr["id"]]:
            continue
        if lyr["id"] == "Suceptibilidad_Erosion":
            for cat, c in EROSION_FILLS.items():
                st.markdown(
                    f"<div style='display:flex;align-items:center;gap:8px;margin-left:8px'>"
                    f"<span style='background:{c};opacity:0.5;width:14px;height:14px;border-radius:3px;display:inline-block'></span>"
                    f"<small>{cat}</small></div>",
                    unsafe_allow_html=True,
                )
            st.markdown(
                f"<div style='display:flex;align-items:center;gap:8px'>"
                f"{lyr['icon']} {lyr['name']}</div>",
                unsafe_allow_html=True,
            )
        else:
            swatch = lyr["fill"] or lyr["outline"]
            op = 1 if lyr["fill"] is None else 0.5
            st.markdown(
                f"<div style='display:flex;align-items:center;gap:8px'>"
                f"<span style='background:{swatch};opacity:{op};width:16px;height:16px;border-radius:3px;display:inline-block;border:2px solid {lyr['outline']}'></span>"
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
    st_html(m._repr_html_(), height=750)
else:
    st.warning("⚠️ Activa al menos una capa en el panel lateral para ver el mapa.")

st.divider()
st.caption(
    "Datos: Capas vectoriales del proyecto PIOJÓ · "
    "Desplegado en Streamlit Community Cloud"
)
