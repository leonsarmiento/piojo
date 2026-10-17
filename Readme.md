# PIOJÓ — Mapa Web de Áreas de Vida

Visor online de las Áreas de Vida Priorizadas de Piojó (Valle del Cauca, Colombia),
con capas vectoriales adicionales (humedales, SINAP, zonas de siembra,
susceptibilidad a erosión ALTA/MUY ALTA y límite municipal).

## Estructura
- `app.py` — aplicación Streamlit + Folium
- `data/` — capas vectoriales en GeoJSON (WGS84)
- `requirements.txt` — dependencias

## Uso local
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Características
- 6 capas vectoriales, cada una con un color propio y 50 % de opacidad
- Fondos: OpenStreetMap y Google Satellite Hybrid
- Panel lateral para activar/desactivar capas y leyenda de colores

## Despliegue en Streamlit Community Cloud
1. Ir a [share.streamlit.io](https://share.streamlit.io) → New app
2. Conectar el repositorio `leonsarmiento/piojo`
3. Main file path: `app.py` → Deploy
