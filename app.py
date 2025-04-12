import streamlit as st
from streamlit_folium import st_folium
import folium
import pandas as pd
import geopandas as gpd
from shapely import wkt
from hotel_ranking import score_hotels, get_score_color
from shapely.geometry import Point
from calculate_distance import calculate_distance
from generate_tour import generate_routes_from_hotel

# === Set page config ===
st.set_page_config(page_title="Vancouver Hotels", layout="wide")

# === Load Vancouver Hotels Data ===
@st.cache_data
def load_hotels():
    hotels = pd.read_csv("data/vancouver_hotels.csv")
    hotels['geometry'] = hotels['geometry'].apply(wkt.loads)
    hotels = gpd.GeoDataFrame(hotels, geometry='geometry', crs="EPSG:4326")  # convert to crs: EPSG:4326 for folium
    return hotels

hotels = load_hotels()

# === Load Vancouver Attractions Data ===
@st.cache_data
def load_attractions():
    attractions = pd.read_csv("data/vancouver_attractions.csv")
    attractions.columns = attractions.columns.str.strip()
    attractions = attractions.dropna(subset=['lat', 'lon'])
    attractions['lat'] = attractions['lat'].astype(float)
    attractions['lon'] = attractions['lon'].astype(float)
    return attractions

attractions = load_attractions()

# === Streamlit Setup ===
st.title("Hotelytics: Vancouver Hotel and Tour Generator")
st.write("Hotelytics helps visitors find the most suitable hotel in Vancouver based on surrounding amenities and also generates a personalized walking tour from the selected hotel to nearby attractions using real street network data.")

if st.session_state.get("ranked_hotels") is None:
    st.subheader("Map of Hotels and Attractions")
    st.write(f"There are {len(hotels)} hotels in Vancouver, and the following map shows both hotels and curated attractions around the city.")

# === Optional: Show raw hotel data and/or attraction data ===
st.sidebar.header("Data Options")

if st.sidebar.checkbox("Show raw hotel data"):
    df = hotels[['name', 'housenumber', 'unit', 'street', 'city', 'province', 'postcode']]
    st.subheader("Raw Hotel Data")
    st.dataframe(df, use_container_width=True)

if st.sidebar.checkbox("Show attraction data"):
    st.subheader("Attraction Data")
    st.dataframe(attractions[['name', 'street name', 'short description']], use_container_width=True)

# === Create the Ranking sidebar ===
if "ranked_hotels" not in st.session_state:
    st.session_state['ranked_hotels'] = None

# === Sidebar Header ===
st.sidebar.header("Rank Hotels")
st.sidebar.write("Rank hotels based on your preferences and find the best match for your stay by using the sliders in the sidebar. 5 is the highest score and 1 is the lowest score. The higher the score, the better the match for your preferences.")

# === Ranking Sliders ===
ranking = {
    "food & drink": st.sidebar.slider("Food & Drink", 1, 5, 3, help="Cafes, restaurants, ice cream, etc."),
    "transportation": st.sidebar.slider("Transportation", 1, 5, 3, help="Bus stops, bike parking, fuel, etc."),
    "entertainments & culture": st.sidebar.slider("Entertainment & Culture", 1, 5, 3, help="Museums, parks, theatres"),
    "health & emergency": st.sidebar.slider("Health & Emergency", 1, 5, 3, help="Pharmacies, clinics, hospitals"),
    "shop & services": st.sidebar.slider("Shop & Services", 1, 5, 3, help="ATMs, post offices, markets"),
}

# === Sidebar Button ===
if st.sidebar.button("Rank Hotels"):
    ranked_hotels = score_hotels(hotels, ranking)
    ranked_hotels = ranked_hotels.sort_values(by='total_score', ascending=False, ignore_index=True)
    st.session_state['ranked_hotels'] = ranked_hotels  # save ranked hotels to session state
    st.success("Hotels successfully ranked based on your preferences!")

# === Sidebar Select Hotel & Generate Tour ===
st.sidebar.header("Generate Walking Tour")
selected_hotel = st.sidebar.selectbox(
    "Choose a hotel to generate a walking tour:",
    options=hotels['name'].tolist()
)
if st.sidebar.button("Generate Tour"):
    hotel_row = hotels[hotels['name'] == selected_hotel].iloc[0]
    sorted_attractions = calculate_distance(hotel_row, attractions)

    st.session_state['sorted_attractions'] = sorted_attractions
    st.session_state['tour_generated'] = True
    st.session_state['selected_hotel'] = hotel_row  # <-- Store actual row

# === Always display ranked table if exists ===
best_hotel = None
if st.session_state['ranked_hotels'] is not None:
    st.subheader("Top 10 Hotels")
    st.write("The following table shows the top 10 hotels based on your preferences. Click on a hotel to see its score breakdown.")

    # === Scoring Explanation ===
    with st.expander("How scoring works"):
        st.markdown("""
        - Hotels are ranked based on amenities within 300m.
        - Each category is weighted based on your slider input.
        - Higher scores = better matches for your preferences.
        """)

    # top 10 hotels to show
    top_10_df = st.session_state['ranked_hotels'][['name', 'total_score']].head(10).copy()
    selected_row = st.data_editor(top_10_df, use_container_width=True, hide_index=True, num_rows="fixed")

    # get the selected hotel (simulate click by filtering row with max score)
    if isinstance(selected_row, pd.DataFrame) and not selected_row.empty:
        best_hotel_name = selected_row.iloc[0]['name']
        best_hotel = st.session_state['ranked_hotels'][st.session_state['ranked_hotels']['name'] == best_hotel_name].iloc[0]

# === Set map center based on selected hotel or default ===
if best_hotel is not None:
    center_lat, center_lon = best_hotel.geometry.y, best_hotel.geometry.x
    zoom_lvl = 17
else:
    center_lat, center_lon = 49.2827, -123.1207
    zoom_lvl = 13
    
# === Create Feature Groups ===
ranking_map = folium.Map(location=[center_lat, center_lon], zoom_start=zoom_lvl)
hotel_layer = folium.FeatureGroup(name="Hotels", show=True)
attraction_layer = folium.FeatureGroup(name="Tourist Attractions", show=True)

# === Ensure map_hotels is a GeoDataFrame with correct CRS ===
map_hotels = st.session_state['ranked_hotels'] if st.session_state['ranked_hotels'] is not None else hotels
if 'geometry' in map_hotels.columns:
    map_hotels = gpd.GeoDataFrame(map_hotels, geometry='geometry', crs="EPSG:4326")

# === Add Hotel Markers ===
max_score = map_hotels['total_score'].max() if 'total_score' in map_hotels.columns else 1

for _, row in map_hotels.iterrows():
    score = row.get('total_score', None)
    color = get_score_color(score, max_score) if score is not None else 'cadetblue'

    folium.Marker(
        location=[row.geometry.y, row.geometry.x],
        popup=folium.Popup(
            f"""
            <strong>{row['name']}</strong><br>
            {row['housenumber']} {row['street']}, {row['city']}, {row['province']} {row['postcode']}<br>
            {'<strong>Score:</strong> {:.1f}'.format(score) if score is not None else ''}
            """,
            max_width=300
        ),
        icon=folium.Icon(color=color, icon='bed', prefix='fa')
    ).add_to(hotel_layer)

# === Add Attraction Markers ===
for _, row in attractions.iterrows():
    folium.Marker(
        location=[row['lat'], row['lon']],
        popup=folium.Popup(
            f"<strong>{row['name']}</strong><br>{row['street name']}<br>{row['short description']}",
            max_width=300
        ),
        icon=folium.Icon(color='darkblue', icon='star', prefix='fa')
    ).add_to(attraction_layer)
            
# === Add layers to map ===
hotel_layer.add_to(ranking_map)
attraction_layer.add_to(ranking_map)
folium.LayerControl(collapsed=False).add_to(ranking_map)

# === Render map and capture click ===
map_data = st_folium(ranking_map, width="100%")

# === Add Generated Tour Path ===
if st.session_state.get('tour_generated'):
    st.subheader("Generated Walking Tour Path")
    st.write(f"Walking tour path from {selected_hotel} to nearby attractions:")
    st.success(f"Walking tour generated from {selected_hotel} to nearby attractions!")

    selected_hotel_row = st.session_state.get("selected_hotel")
    sorted_attractions = st.session_state.get("sorted_attractions")
    
    if selected_hotel_row is not None and sorted_attractions is not None:
        try:
            G, tsp_routes, tsp_order = generate_routes_from_hotel(selected_hotel_row, sorted_attractions)
            
            tour_map = folium.Map(location=[selected_hotel_row.geometry.y, selected_hotel_row.geometry.x], zoom_start=15)

            # Add hotel marker (start point)
            folium.Marker(
                location=[selected_hotel_row.geometry.y, selected_hotel_row.geometry.x],
                popup="Start: Hotel",
                icon=folium.Icon(color="black", icon="bed", prefix="fa")
            ).add_to(tour_map)
            
			      # draw the path on the map
            for route_nodes, label in tsp_routes:
                coords = [(G.nodes[n]['y'], G.nodes[n]['x']) for n in route_nodes]
                folium.PolyLine(coords, color="red", weight=3, opacity=0.8).add_to(tour_map)

                # Optional: mark final destination point
                folium.Marker(
                    location=coords[-1],
                    popup=label,
                    icon=folium.Icon(color="darkblue", icon="star", prefix="fa")
                ).add_to(tour_map)
            
            st_folium(tour_map, width="100%")
        except Exception as e:
            st.error(f"Could not generate walking tour path: {e}")
            
