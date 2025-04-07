import pandas as pd
import geopandas as gpd 
import streamlit as st
import pydeck as pdk

# === DATA CLEANING ===

gdf = gpd.read_file("data/vancouver_hotels.geojson")
df = pd.DataFrame(gdf.drop(columns='geometry'))

# Filter relevant columns
hotels = df[[
  'id',
  'name',
  'addr:housenumber',
  'addr:unit',
  'addr:street',
  'addr:city',
  'addr:province',
  'addr:postcode',
]]

hotels = hotels.rename(columns={
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

# === STREAMLIT APP ===

st.set_page_config(page_title="Vancouver Hotels Map", layout="wide")
st.title("🏨 Vancouver Hotels Map")
st.subheader(f"Total Hotels: {len(gdf)}")

if st.checkbox("Show raw hotel table"):
    st.dataframe(hotels)

# Re-load GeoJSON and filter to Points
gdf = gpd.read_file("data/vancouver_hotels.geojson")
gdf = gdf[gdf.geometry.type == 'Point']
gdf['lon'] = gdf.geometry.x
gdf['lat'] = gdf.geometry.y

# Create pydeck layer with smaller radius (30 instead of 60)
layer = pdk.Layer(
    "ScatterplotLayer",
    data=gdf,
    get_position='[lon, lat]',
    get_radius= 20,  # smaller circles 
    get_fill_color=[255, 0, 0, 160],
    pickable=True
)


# Optional tooltips
tooltip = {"html": "<b>Hotel:</b> {name}", "style": {"color": "white"}}

# Center map view
view_state = pdk.ViewState(
    latitude=gdf['lat'].mean(),
    longitude=gdf['lon'].mean(),
    zoom=12,
    pitch=0
)

# Display pydeck map
st.pydeck_chart(pdk.Deck(
    layers=[layer],
    initial_view_state=view_state,
    map_style="light",  # original map color

    tooltip=tooltip
))
