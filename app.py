import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import geopandas as gpd
from shapely import wkt

# === Load Vancouver Hotels Data ===
df = pd.read_csv("data/vancouver_hotels.csv")
df['centroid'] = df['centroid'].apply(wkt.loads)

# Convert to GeoDataFrame with EPSG:4326
hotels = gpd.GeoDataFrame(df, geometry='centroid', crs="EPSG:4326")

# === STREAMLIT APP SETUP ===
st.set_page_config(
  page_title="Vancouver Hotels",
  layout="wide",
)
st.title("Hotelytics: Vancouver Hotel and Tour Generator")

# === Show Hotel Info ===
st.subheader("Map of Hotels")
st.write(f"There are {len(hotels)} hotels in Vancouver, BC, Canada. The data is obtained from OpenStreetMap and filtered for hotels in Vancouver only.")

df = hotels[['id', 'name', 'housenumber', 'unit', 'street', 'city', 'province', 'postcode']]
if st.checkbox("Show raw hotel data"):
  st.dataframe(df, use_container_width=True)

# === Initialize Map ===
m = folium.Map(location=[49.2827, -123.1207], zoom_start=14)

# === Add Hotel Markers ===
for _, row in hotels.iterrows():
  folium.Marker(
    location=[row['centroid'].y, row['centroid'].x],
    popup=folium.Popup(
      f"<strong>{row['name']}</strong><br>{row['housenumber']} {row['street']}, {row['city']}, {row['province']} {row['postcode']}", 
      max_width=300
    ),
    icon=folium.Icon(color='cadetblue', icon='bed', prefix='fa')
  ).add_to(m)

# === Load and Display Tourist Attractions ===
st.subheader("Tourist Attractions")

# Load attraction data
try:
    attractions = pd.read_csv("data/vancouver_attractions.csv")
    attractions.columns = attractions.columns.str.strip()  # Strip whitespace
    attractions = attractions.dropna(subset=['lat', 'lon'])  # Drop bad rows
    attractions['lat'] = attractions['lat'].astype(float)
    attractions['lon'] = attractions['lon'].astype(float)

    # Optional: Show sample data
    if st.checkbox("Show attraction data"):
        st.dataframe(attractions.head(), use_container_width=True)

    # Add attraction markers
    for _, row in attractions.iterrows():
        folium.Marker(
            location=[row['lat'], row['lon']],
            popup=folium.Popup(
                f"<strong>{row['name']}</strong><br>{row['street name']}<br>{row['short description']}", 
                max_width=300
            ),
            icon=folium.Icon(color='red', icon='star', prefix='fa')
        ).add_to(m)

except Exception as e:
    st.error(f"Failed to load attractions data: {e}")

# === Final Render of Map ===
st_folium(m, width="100%")
