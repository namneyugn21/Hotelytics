import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import geopandas as gpd
from shapely import wkt

# load the vancouver_hotels.csv file
df = pd.read_csv("data/vancouver_hotels.csv")
df['centroid'] = df['centroid'].apply(wkt.loads)

# convert to GeoDataFrame with EPSG:4326
hotels = gpd.GeoDataFrame(df, geometry='centroid', crs="EPSG:4326")

# === STREAMLIT APP ===
st.set_page_config(
  page_title="Vancouver Hotels",
  layout="wide",
)
st.title("Hotelytics: Vancouver Hotel and Tour Generator")


# show hotel data
st.subheader("Map of Hotels")
st.write(f"There are {len(hotels)} hotels in Vancouver, BC, Canada. The data is obtained from OpenStreetMap and filtered for hotels in Vancouver only.")

df = hotels[['id', 'name', 'housenumber', 'unit', 'street', 'city', 'province', 'postcode']]
if st.checkbox("Show raw hotel data"):
  st.dataframe(df, use_container_width=True)

m = folium.Map(location=[49.2827, -123.1207], zoom_start=14)

for _, row in hotels.iterrows():
  folium.Marker(
    location=[row['centroid'].y, row['centroid'].x],
    popup=folium.Popup(f"<strong>{row['name']}</strong><br>{row['housenumber']} {row['street']}, {row['city']}, {row['province']} {row['postcode']}", max_width=300),
    icon=folium.Icon(color='cadetblue', icon='bed', prefix='fa')
  ).add_to(m)

st_folium(m, width="100%")
