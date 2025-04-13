import streamlit as st
from streamlit_folium import st_folium
import folium
import pandas as pd
import geopandas as gpd
from shapely import MultiPoint, wkt
from generate_tour import generate_tsp_route, generate_nn_route
from hotel_ranking import score_hotels, get_score_color
from shapely.geometry import Point
from calculate_distance import calculate_distance
from amenities_cluster import get_clusters

# === Set page config ===
st.set_page_config(page_title="Hotelytics", layout="wide")

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
    "food & drink": st.sidebar.slider("Food & Drink", 0, 5, 3, help="Cafes, restaurants, ice cream, etc."),
    "transportation": st.sidebar.slider("Transportation", 0, 5, 3, help="Bus stops, bike parking, fuel, etc."),
    "entertainments & culture": st.sidebar.slider("Entertainment & Culture", 0, 5, 3, help="Museums, parks, theatres"),
    "health & emergency": st.sidebar.slider("Health & Emergency", 0, 5, 3, help="Pharmacies, clinics, hospitals"),
    "shop & services": st.sidebar.slider("Shop & Services", 0, 5, 3, help="ATMs, post offices, markets"),
}

# === Sidebar Button ===
if st.sidebar.button("Rank Hotels"):
    ranked_hotels = score_hotels(hotels, ranking)
    ranked_hotels = ranked_hotels.sort_values(by='total_score', ascending=False, ignore_index=True)
    st.session_state['ranked_hotels'] = ranked_hotels  # save ranked hotels to session state

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
    st.session_state['selected_hotel'] = hotel_row

# === Always display ranked table if exists ===
best_hotel = None
if st.session_state['ranked_hotels'] is not None:
    st.success("Hotels successfully ranked based on your preferences!")
    st.subheader("Top 10 Hotels")
    st.write("The following table shows the top 10 hotels based on your preferences. Click on a hotel to see its score breakdown.")

    # === Scoring Explanation ===
    with st.expander("How does scoring work?"):
        st.markdown("""
        Hotelytics ranks each hotel based on how many useful amenities are nearby, using the following method:

        - A **350-meter radius** is drawn around each hotel.
        - We **count** how many amenities fall into each category within that radius (e.g., 5 cafes, 3 clinics), with each category is **weighted** according to your sliders (e.g., food = 4, health = 2).
        - For each hotel:
            ```
            Total Score = (count_food × weight_food) + (count_transport × weight_transport) + ...
            ```
        - After scoring, we **normalize** all scores to a 0–100 scale for easy comparison.

        **Example**:
        - A hotel has 6 food & drink, 3 transport, 2 health spots within 350m.
        - If you set food=5, transport=3, health=2, then:
            ```
            Total Score = (6×5) + (3×3) + (2×2) = 30 + 9 + 4 = 43
            ```
        - This raw score is then scaled relative to other hotels.

        **Higher scores mean the hotel better fits your priorities.**
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
  
# === Add Clusters to Map ===
clusters = get_clusters()

CATEGORY_COLORS = {
    'food & drink': 'red',
    'transportation': 'blue',
    'entertainments & culture': 'purple',
    'health & emergency': 'orange',
    'shop & services': 'green'
}

for category, df in clusters.items():
    category_layer = folium.FeatureGroup(name=f"{category.title()} Clusters", show=False)
    color = CATEGORY_COLORS.get(category, 'gray')

    # Group by cluster label
    for cluster_id, group in df.groupby('cluster'):
        points = group[['lat', 'lon']].values
        multipoint = MultiPoint([(lon, lat) for lat, lon in points])
        
        # Draw convex hull around points in cluster (if more than 2)
        if len(points) >= 3:
            hull = multipoint.convex_hull
            folium.Polygon(
                locations=[(pt[1], pt[0]) for pt in hull.exterior.coords],
                color=color,
                fill=True,
                fill_color=color,
                fill_opacity=0.25,
                weight=1,
                popup=folium.Popup(
                    f"<strong>{category.title()} Cluster</strong><br>"
                    f"Cluster ID: {cluster_id}<br>"
                    f"Number of Points: {len(group)}",
                    max_width=300
                )
            ).add_to(category_layer)

    # Add this category layer to map
    category_layer.add_to(ranking_map)
            
# === Add layers to map ===
hotel_layer.add_to(ranking_map)
attraction_layer.add_to(ranking_map)
folium.LayerControl(collapsed=False).add_to(ranking_map)

# === Render map and capture click ===
map_data = st_folium(ranking_map, width="100%")

# === Tour generation ===
if st.session_state.get("tour_generated"):
    st.subheader("Walking Tour Path Result")
    st.success(f"Generated a walking tour path from {selected_hotel} to nearby attractions")

    selected_hotel_row = st.session_state.get("selected_hotel")
    sorted_attractions = st.session_state.get("sorted_attractions")

    if selected_hotel_row is not None and sorted_attractions is not None:
        try:
            # === Traveling Salesman Problem (TSP) ===
            # get the routes coords
            tsp_route_coords, tsp_ordered_stop_names, tsp_segment_distances = generate_tsp_route(selected_hotel_row, sorted_attractions)
            
            # Create a new map centered on the selected hotel for the TSP algorithm
            tsp_tour_map = folium.Map(location=[selected_hotel_row.geometry.y, selected_hotel_row.geometry.x], zoom_start=14)

            # build an itinerary for the tour
            # note: If there are N stops, there are N-1 segments.
            itinerary_data = []
            for i in range(len(tsp_segment_distances)):
                from_stop = tsp_ordered_stop_names[i]
                to_stop   = tsp_ordered_stop_names[i+1]
                # Convert meters to kilometers
                distance_km = tsp_segment_distances[i] / 1000
                itinerary_data.append({
                    "From": from_stop,
                    "To": to_stop,
                    "Distance (km)": f"{distance_km:.2f}"
                })
            itinerary_df = pd.DataFrame(itinerary_data)
            st.subheader("Traveling Salesman Problem Itinerary (Total Distance: {:.2f} km)".format(sum(tsp_segment_distances) / 1000))
            with st.expander("How does Traveling Salesman Problem work?"):
                st.markdown("""
                - This algorithm finds the **shortest possible route** that visits all attractions **once** and returns to the starting point (hotel).
                - It considers **real walking paths** using OpenStreetMap data.
                - It guarantees a near-optimal route but may take slightly longer to compute.
                
                **Steps:**
                1. Convert each attraction into a network node.
                2. Build a distance graph between all points.
                3. Use a TSP solver to find the shortest possible path.
                4. Calculate the real walking route between each stop.
                """)

            st.dataframe(itinerary_df, use_container_width=True, hide_index=True)

            # Add a marker for the starting hotel
            unit = selected_hotel_row['unit'] if pd.notna(selected_hotel_row['unit']) else ""
            postcode = selected_hotel_row['postcode'] if pd.notna(selected_hotel_row['postcode']) else ""
            popup_html = (
                f"<strong>{selected_hotel_row['name']}</strong><br>"
                f"{selected_hotel_row['housenumber']} {selected_hotel_row['street']}{(' ' + unit) if unit else ''}, "
                f"{selected_hotel_row['city']}, {selected_hotel_row['province']} {postcode}<br>"
            )
            folium.Marker(
                location=[selected_hotel_row.geometry.y, selected_hotel_row.geometry.x],
                popup=folium.Popup(popup_html, max_width=300),
                icon=folium.Icon(color="black", icon="bed", prefix="fa")
            ).add_to(tsp_tour_map)

            # Add markers for the attractions
            for attraction in sorted_attractions.itertuples():
                # Build an HTML popup containing the attraction's info:
                popup_html = (
                    f"<strong>{attraction.name}</strong><br>"
                    f"{attraction._4}<br>"
                    f"{attraction._5}<br>"
                    f"<em>Distance: {attraction.distance_km:.2f} km</em>"
                )
                folium.Marker(
                    location=[attraction.lat, attraction.lon],
                    popup=folium.Popup(popup_html, max_width=300),
                    icon=folium.Icon(color="darkblue", icon="star", prefix="fa")
                ).add_to(tsp_tour_map)

            # Add the walking tour path
            folium.PolyLine(
                locations=tsp_route_coords,
                color="blue",
                weight=5,
                opacity=0.7
            ).add_to(tsp_tour_map)

            # Display the tour map
            st_folium(tsp_tour_map, width="100%")


            # === Nearest Neighbor (Greedy) ===
            greedy_route_coords, greedy_ordered_stop_names, greedy_segment_distances = generate_nn_route(selected_hotel_row, sorted_attractions)

            greedy_tour_map = folium.Map(location=[selected_hotel_row.geometry.y, selected_hotel_row.geometry.x], zoom_start=14)

            # build an itinerary for the tour
            # note: If there are N stops, there are N-1 segments.
            greedy_itinerary_data = []
            for i in range(len(greedy_segment_distances)):
                from_stop = greedy_ordered_stop_names[i]
                to_stop   = greedy_ordered_stop_names[i+1]
                # Convert meters to kilometers
                distance_km = greedy_segment_distances[i] / 1000
                greedy_itinerary_data.append({
                    "From": from_stop,
                    "To": to_stop,
                    "Distance (km)": f"{distance_km:.2f}"
                })
            greedy_itinerary_df = pd.DataFrame(greedy_itinerary_data)
            st.subheader("Nearest Neighbour (Greedy) Itinerary (Total Distance: {:.2f} km)".format(sum(greedy_segment_distances) / 1000))
            with st.expander("How does Nearest Neighbour (Greedy) work?"):
                st.markdown("""
                - This simpler method starts at the hotel and **always goes to the closest unvisited attraction**.
                - It is **fast** and intuitive but doesn't always give the shortest total route.
                
                **Steps:**
                1. Start at the hotel.
                2. Find the nearest attraction not yet visited.
                3. Repeat until all are visited.
                
                **Best for:** Quick route planning with decent efficiency.
                """)
            st.dataframe(greedy_itinerary_df, use_container_width=True, hide_index=True)

            # Add a marker for the starting hotel
            unit = selected_hotel_row['unit'] if pd.notna(selected_hotel_row['unit']) else ""
            postcode = selected_hotel_row['postcode'] if pd.notna(selected_hotel_row['postcode']) else ""
            popup_html = (
                f"<strong>{selected_hotel_row['name']}</strong><br>"
                f"{selected_hotel_row['housenumber']} {selected_hotel_row['street']}{(' ' + unit) if unit else ''}, "
                f"{selected_hotel_row['city']}, {selected_hotel_row['province']} {postcode}<br>"
            )
            folium.Marker(
                location=[selected_hotel_row.geometry.y, selected_hotel_row.geometry.x],
                popup=folium.Popup(popup_html, max_width=300),
                icon=folium.Icon(color="black", icon="bed", prefix="fa")
            ).add_to(greedy_tour_map)

            # Add markers for the attractions
            for attraction in sorted_attractions.itertuples():
                # Build an HTML popup containing the attraction's info:
                popup_html = (
                    f"<strong>{attraction.name}</strong><br>"
                    f"{attraction._4}<br>"
                    f"{attraction._5}<br>"
                    f"<em>Distance: {attraction.distance_km:.2f} km</em>"
                )
                folium.Marker(
                    location=[attraction.lat, attraction.lon],
                    popup=folium.Popup(popup_html, max_width=300),
                    icon=folium.Icon(color="darkblue", icon="star", prefix="fa")
                ).add_to(greedy_tour_map)

            # Add the walking tour path
            folium.PolyLine(
                locations=greedy_route_coords,
                color="blue",
                weight=5,
                opacity=0.7
            ).add_to(greedy_tour_map)

            # Display the tour map
            st_folium(greedy_tour_map, width="100%")
        except Exception as e:
            st.error(f"Could not generate walking tour path: {e}")