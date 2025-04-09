import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd
import geopandas as gpd
from shapely import wkt
from folium.plugins import MarkerCluster
from haversine import haversine

# === Load Vancouver Hotel Data ===
df = pd.read_csv("data/vancouver_hotels.csv")
df['centroid'] = df['centroid'].apply(wkt.loads)
hotels = gpd.GeoDataFrame(df, geometry='centroid', crs="EPSG:4326")

# === Load Amenity Data ===
amenities = pd.read_csv("data/vancouver_amenities.csv")
amenities.columns = amenities.columns.str.strip()
amenities = amenities.dropna(subset=['lat', 'lon'])
amenities['lat'] = amenities['lat'].astype(float)
amenities['lon'] = amenities['lon'].astype(float)

# === Streamlit Config ===
st.set_page_config(page_title="Hotelytics", layout="wide")
st.title("Hotelytics: Hotel & Nearby Amenities Explorer")

# === Map ===
m = folium.Map(location=[49.2827, -123.1207], zoom_start=14)
hotel_layer = folium.FeatureGroup(name="Hotels", show=True)
amenity_layer = folium.FeatureGroup(name="Nearby Amenities", show=True)

# === Hotel Marker Layer ===
for _, row in hotels.iterrows():
    folium.Marker(
        location=[row['centroid'].y, row['centroid'].x],
        popup=f"<b>{row['name']}</b><br>{row['housenumber']} {row['street']}, {row['city']} {row['province']} {row['postcode']}",
        icon=folium.Icon(color='cadetblue', icon='bed', prefix='fa')
    ).add_to(hotel_layer)

# === Hotel Selection ===
hotel_names = hotels['name'].dropna().unique()
selected_hotel_name = st.selectbox("Select a hotel to explore nearby amenities:", sorted(hotel_names))
selected_hotel = hotels[hotels['name'] == selected_hotel_name].iloc[0]
hotel_coord = (selected_hotel['centroid'].y, selected_hotel['centroid'].x)

# Center map on selected hotel
m.location = hotel_coord
m.zoom_start = 16

# === Radius Slider ===
radius_km = st.slider("Search radius (km)", 0.1, 2.0, 0.5)

# === Amenity Category Filter ===
st.subheader("Filter Amenities")
amenity_categories = {
    "food & drink": ['cafe', 'fast_food', 'bbq', 'restaurant', 'pub', 'bar', 'food_court', 'ice_cream', 'bistro', 'juice_bar', 'internet_cafe', 'disused:restaurant', 'water_point', 'biergarten'],
    "transportation": ['fuel', 'parking_entrance', 'bicycle_parking', 'parking', 'ferry_terminal', 'car_rental', 'car_sharing', 'bicycle_rental', 'seaplane terminal', 'charging_station', 'parking_space', 'taxi', 'bus_station', 'motorcycle_parking', 'boat_rental', 'EVSE', 'motorcycle_rental'],
    "entertainments & culture": ['place_of_worship', 'cinema', 'theatre', 'library', 'arts_centre', 'fountain', 'photo_booth', 'nightclub', 'clock', 'stripclub', 'gambling', 'playground', 'meditation_centre', 'spa', 'lounge', 'gym', 'park', 'casino', 'leisure'],
    "health & emergency": ['pharmacy', 'dentist', 'doctors', 'clinic', 'veterinary', 'hospital', 'first_aid', 'healthcare', 'chiropractor', 'Pharmacy'],
    "shop & services": ['post_office', 'atm', 'childcare', 'bank', 'car_wash', 'luggage_locker', 'bureau_de_change', 'marketplace', 'atm;bank', 'shop|clothes'],
    "others": ['toilets', 'post_box', 'telephone', 'vending_machine', 'school', 'bench', 'community_centre', 'waste_basket', 'public_building', 'drinking_water', 'shelter', 'recycling', 'public_bookcase', 'university', 'dojo', 'bicycle_repair_station', 'waste_disposal', 'social_facility', 'college', 'construction', 'post_depot', 'nursery', 'kindergarten', 'conference_centre', 'shower', 'trolley_bay', 'fire_station', 'police', 'compressed_air', 'family_centre', 'townhall', 'music_school', 'scrapyard', 'language_school', 'courthouse', 'events_venue', 'prep_school', 'cram_school', 'science', 'ATLAS_clean_room', 'workshop', 'safety', 'lobby', 'animal_shelter', 'social_centre', 'vacuum_cleaner', 'smoking_area', 'studio', 'ranger_station', 'storage_rental', 'watering_place', 'trash', 'sanitary_dump_station', 'Observation Platform', 'housing co-op', 'driving_school', 'loading_dock', 'monastery', 'storage', 'payment_terminal', 'waste_transfer_station', 'office|financial', 'hunting_stand', 'money_transfer', 'letter_box', 'training', 'car_rep', 'research_institute']
}
selected_cats = st.multiselect("Select categories:", list(amenity_categories.keys()), default=[])
selected_types = [a for cat in selected_cats for a in amenity_categories[cat]]

# === Filter Amenities Near Hotel ===
nearby = amenities[
    (amenities['amenity'].isin(selected_types)) &
    (amenities.apply(lambda r: haversine(hotel_coord, (r['lat'], r['lon'])) <= radius_km, axis=1))
]

# === Show Sample Data (Optional) ===
if st.checkbox("Show nearby amenities data"):
    st.dataframe(nearby[['name', 'amenity', 'category', 'lat', 'lon']].head(), use_container_width=True)

# === Add Nearby Amenity Markers ===
cluster = MarkerCluster()
for _, row in nearby.iterrows():
    folium.Marker(
        location=[row['lat'], row['lon']],
        popup=f"<b>{row.get('name', 'Unnamed')}</b><br>{row['amenity']} ({row['category']})",
        icon=folium.Icon(color='green', icon='info-sign')
    ).add_to(cluster)
cluster.add_to(amenity_layer)

# === Add Layers and Render ===
hotel_layer.add_to(m)
amenity_layer.add_to(m)
folium.LayerControl(collapsed=False).add_to(m)

st_folium(m, width="100%")
