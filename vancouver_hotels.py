import pandas as pd
import geopandas as gpd
import streamlit as st
import pydeck as pdk

# === PAGE CONFIG ===
st.set_page_config(page_title="Vancouver Hotels + Amenities Map", layout="wide")

st.title("🏨 Vancouver Hotels & Amenities Map")

# === LOAD HOTELS ===
gdf = gpd.read_file("data/vancouver_hotels.geojson")
gdf = gdf[gdf.geometry.notnull()]
gdf['lon'] = gdf.geometry.centroid.x
gdf['lat'] = gdf.geometry.centroid.y

# Clean hotel DataFrame for display
df = pd.DataFrame(gdf.drop(columns='geometry'))
hotels = df[[
    'id', 'name', 'addr:housenumber', 'addr:unit', 'addr:street',
    'addr:city', 'addr:province', 'addr:postcode'
]].rename(columns={
    'addr:housenumber': 'housenumber',
    'addr:unit': 'unit',
    'addr:street': 'street',
    'addr:city': 'city',
    'addr:province': 'province',
    'addr:postcode': 'postcode'
})
hotels['id'] = hotels.index + 1
hotels['province'] = hotels['province'].fillna('BC')
hotels['city'] = hotels['city'].fillna('Vancouver')
hotels['postcode'] = hotels['postcode'].fillna('N/A')
hotels.to_csv('data/vancouver_hotels.csv', index=False)

st.subheader(f"Total Hotels: {len(hotels)}")

if st.checkbox("Show raw hotel table"):
    st.dataframe(hotels)

# === LOAD AMENITIES CSV ===
amenities_df = pd.read_csv("data/vancouver_amenities.csv")

# Drop rows with missing coordinates
amenities_df = amenities_df.dropna(subset=["lat", "lon"])

# === DEFINE MAP LAYERS ===

# Hotel layer (red)
hotel_layer = pdk.Layer(
    "ScatterplotLayer",
    data=gdf,
    get_position='[lon, lat]',
    get_radius=20,
    get_fill_color=[255, 0, 0, 160],
    pickable=True
)

# Amenity layer (blue)
amenities_layer = pdk.Layer(
    "ScatterplotLayer",
    data=amenities_df,
    get_position='[lon, lat]',
    get_radius=10,
    get_fill_color=[0, 102, 255, 160],
    pickable=True
)

# === TOOLTIP HANDLING ===
tooltip = {
    "html": """
    {% if name %}
        <b>Hotel:</b> {name}
    {% elif amenity %}
        <b>Amenity:</b> {amenity}
    {% endif %}
    """,
    "style": {"color": "white"}
}

# === SET MAP VIEW ===
view_state = pdk.ViewState(
    latitude=gdf['lat'].mean(),
    longitude=gdf['lon'].mean(),
    zoom=12,
    pitch=0
)

# === RENDER THE MAP ===
st.pydeck_chart(pdk.Deck(
    layers=[hotel_layer, amenities_layer],
    initial_view_state=view_state,
    map_style="light",
    tooltip=tooltip
))
