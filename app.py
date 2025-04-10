import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import geopandas as gpd
from shapely import wkt

# === Load Vancouver Hotels Data  ===
df = pd.read_csv("data/vancouver_hotels.csv")
df['centroid'] = df['centroid'].apply(wkt.loads)
hotels = gpd.GeoDataFrame(df, geometry='centroid', crs="EPSG:4326")

# === Load Vancouver Attractions Data  ===
attractions = pd.read_csv("data/vancouver_attractions.csv")
attractions.columns = attractions.columns.str.strip()
attractions = attractions.dropna(subset=['lat', 'lon'])
attractions['lat'] = attractions['lat'].astype(float)
attractions['lon'] = attractions['lon'].astype(float)

# === Streamlit Setup ===
st.set_page_config(page_title="Vancouver Hotels", layout="wide")
st.title("Hotelytics: Vancouver Hotel and Tour Generator")

st.subheader("Map of Hotels and Attractions")
st.write(f"There are {len(hotels)} hotels in Vancouver. This map shows both hotels and curated attractions around the city.")

# Optional: Show raw hotel data and/or attraction data
if st.checkbox("Show raw hotel data"):
    df = hotels[['id', 'name', 'housenumber', 'unit', 'street', 'city', 'province', 'postcode']]
    st.dataframe(df, use_container_width=True)

if st.checkbox("Show attraction data"):
    st.dataframe(attractions, use_container_width=True)

# === Create Base Map ===
m = folium.Map(location=[49.2827, -123.1207], zoom_start=14)

# === Create Feature Groups ===
hotel_layer = folium.FeatureGroup(name="Hotels", show=True)
attraction_layer = folium.FeatureGroup(name="Tourist Attractions", show=True)

# === Add Hotel Markers ===
for _, row in hotels.iterrows():
    folium.Marker(
        location=[row['centroid'].y, row['centroid'].x],
        popup=folium.Popup(
            f"<strong>{row['name']}</strong><br>{row['housenumber']} {row['street']}, {row['city']}, {row['province']} {row['postcode']}", 
            max_width=300
        ),
        icon=folium.Icon(color='cadetblue', icon='bed', prefix='fa')
    ).add_to(hotel_layer)

# === Add Attraction Markers ===
for _, row in attractions.iterrows():
    folium.Marker(
        location=[row['lat'], row['lon']],
        popup=folium.Popup(
            f"<strong>{row['name']}</strong><br>{row['street name']}<br>{row['short description']}",
            max_width=300
        ),
        icon=folium.Icon(color='red', icon='star', prefix='fa')
    ).add_to(attraction_layer)

# === Add layers to map ===
hotel_layer.add_to(m)
attraction_layer.add_to(m)
folium.LayerControl(collapsed=False).add_to(m)

# === Render map ===
st_folium(m, width="100%")
