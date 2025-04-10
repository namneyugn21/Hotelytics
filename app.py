import streamlit as st
from streamlit_folium import st_folium
import folium
import pandas as pd
import geopandas as gpd
from shapely import wkt
from hotel_ranking import score_hotels, get_score_color
from shapely.geometry import Point
from sort_attractions_by_distance import sort_attractions_by_distance


st.set_page_config(page_title="Vancouver Hotels", layout="wide")

# === Load Vancouver Hotels Data  ===
@st.cache_data
def load_hotels():
    hotels = pd.read_csv("data/vancouver_hotels.csv")
    hotels['geometry'] = hotels['geometry'].apply(wkt.loads)
    hotels = gpd.GeoDataFrame(hotels, geometry='geometry', crs="EPSG:4326") # convert to crs: EPSG:4326 for folium
    return hotels
hotels = load_hotels() 

# === Load Vancouver Attractions Data  ===
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
st.markdown(
    """
    <style>
    /* Sidebar background color */
    [data-testid="stSidebar"] {
        background-color: #5e0000;
        color: white;
    }

    [data-testid="stSidebar"] * {
        color: white !important;
    }

    [data-testid="stExpander"] * {
        border-color: rgb(163, 168, 184, 50%) !important;
    }

    [data-testid="tooltipHoverTarget"] svg {
        stroke: white !important;
    }

    /* Slider handle and track color */
    .stSlider > div > div > div > div {
        background: #ffffff; /* white handle */
    }

    .stSlider > div > div > div:nth-child(1) > div {
        background: #c0c0c0; /* light grey track */
    }

    /* Button styling in sidebar */
    [data-testid="stSidebar"] button {
        background-color: #a52a2a;
        color: white;
        border: none;
        border-radius: 4px;
        width: 100%;
    }

    [data-testid="stSidebar"] button:hover {
        background-color: #9b1b1b;
    }
    </style>
    """,
    unsafe_allow_html=True
)
st.title("Hotelytics: Vancouver Hotel and Tour Generator")
st.write("Hotelytics helps visitors find the most suitable hotel in Vancouver based on surrounding amenities and also generates a personalized walking tour from the selected hotel to nearby attractions using real street network data.")
st.subheader("Map of Hotels and Attractions")
st.write(f"There are {len(hotels)} hotels in Vancouver, and the following map shows both hotels and curated attractions around the city.")
st.write("Rank hotels based on your preferences and find the best match for your stay by using the sliders in the sidebar.")

# Optional: Show raw hotel data and/or attraction data
st.sidebar.header("Data Options")
if st.sidebar.checkbox("Show raw hotel data"):
    df = hotels[['name', 'housenumber', 'unit', 'street', 'city', 'province', 'postcode']]
    st.subheader("Raw Hotel Data")
    st.dataframe(df, use_container_width=True)

if st.sidebar.checkbox("Show attraction data"):
    st.subheader("Attraction Data")
    st.dataframe(attractions[['name', 'street name', 'short description']], use_container_width=True)

# === Create the Ranking sidebar ===
# check if session state exists for ranked hotels, if not then the map will show all hotels and attractions
if "ranked_hotels" not in st.session_state:
    st.session_state['ranked_hotels'] = None
    
# === Sidebar Header ===
st.sidebar.header("Rank Hotels")
st.sidebar.write("Customize your preferences by ranking the following categories from **0 (not important)** to **5 (very important)**.")

# === Scoring Explanation ===
with st.sidebar.expander("How scoring works"):
    st.markdown("""
    - Hotels are ranked based on amenities within 300m.
    - Each category is weighted based on your slider input.
    - Higher scores = better matches for your preferences.
    """)

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
    st.session_state['ranked_hotels'] = ranked_hotels # save ranked hotels to session state
    st.success("Hotels successfully ranked based on your preferences!")

# === Sidebar Select Hotel & Generate Tour ===
if st.session_state['ranked_hotels'] is not None:
    st.sidebar.markdown("---")
    st.sidebar.header("Generate Tour")

    # Dropdown list of ranked hotel names
    selected_hotel_name = st.sidebar.selectbox(
        "Choose a hotel to generate a walking tour:",
        options=st.session_state['ranked_hotels']['name'].tolist()
    )

    if st.sidebar.button("Generate Tour"):
        selected_hotel = st.session_state['ranked_hotels'][
            st.session_state['ranked_hotels']['name'] == selected_hotel_name
        ].iloc[0]

        st.success(f"🏨 Selected Hotel: {selected_hotel['name']}")
        sorted_attractions = sort_attractions_by_distance(selected_hotel, attractions)

        st.subheader(f"Top 10 Nearby Attractions from: {selected_hotel['name']}")
        st.dataframe(
            sorted_attractions[['name', 'distance_km', 'street name', 'short description']].head(10).reset_index(drop=True),
            use_container_width=True
        )

# always display ranked table if exists
selected_hotel = None
if st.session_state['ranked_hotels'] is not None:
    st.subheader("Top 10 Hotels")
    st.write("Ranked by your preferences! Click on the hotel markers to see more details.")
    # top 10 hotels to show
    top_10_df = st.session_state['ranked_hotels'][['name', 'total_score']].head(10).copy()
    selected_row = st.data_editor(top_10_df, use_container_width=True, hide_index=True, num_rows="fixed")

    # get the selected hotel (simulate click by filtering row with max score)
    if isinstance(selected_row, pd.DataFrame) and not selected_row.empty:
        selected_hotel_name = selected_row.iloc[0]['name']
        selected_hotel = st.session_state['ranked_hotels'][st.session_state['ranked_hotels']['name'] == selected_hotel_name].iloc[0]

# === Set map center based on selected hotel or default ===
if selected_hotel is not None:
    center_lat, center_lon = selected_hotel.geometry.y, selected_hotel.geometry.x
    zoom_lvl = 17
else:
    center_lat, center_lon = 49.2827, -123.1207
    zoom_lvl = 13

m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom_lvl)

# === Create Feature Groups ===
hotel_layer = folium.FeatureGroup(name="Hotels", show=True)
attraction_layer = folium.FeatureGroup(name="Tourist Attractions", show=True)

# === Define map_hotels early ===
map_hotels = st.session_state['ranked_hotels'] if st.session_state['ranked_hotels'] is not None else hotels

# === Ensure map_hotels is a GeoDataFrame with correct CRS ===
if 'geometry' in map_hotels.columns:
    map_hotels = gpd.GeoDataFrame(map_hotels, geometry='geometry', crs="EPSG:4326")

# === Add Hotel Markers and invisible click targets ===
max_score = map_hotels['total_score'].max() if 'total_score' in map_hotels.columns else 1

for _, row in map_hotels.iterrows():
    score = row.get('total_score', None)
    color = get_score_color(score, max_score) if score is not None else 'cadetblue'

    # Add visible icon marker with popup
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
hotel_layer.add_to(m)
attraction_layer.add_to(m)
folium.LayerControl(collapsed=False).add_to(m)

# === Render map and capture click ===
map_data = st_folium(m, width="100%", returned_objects=["last_clicked"])

# === Handle clicks on the map ===
clicked_location = map_data.get("last_clicked")
if clicked_location:
    st.success(f"📍 You clicked: {clicked_location}")
    clicked_point = Point(clicked_location["lng"], clicked_location["lat"])

    # Project both hotel geometries and clicked point to UTM for accurate distance calc
    hotels_proj = hotels.to_crs(epsg=26910)
    clicked_point_proj = gpd.GeoSeries([clicked_point], crs="EPSG:4326").to_crs(epsg=26910).iloc[0]

    hotels_proj["diff"] = hotels_proj["geometry"].distance(clicked_point_proj)
    closest_match = hotels_proj[hotels_proj["diff"] < 50]  # meters

    if not closest_match.empty:
        hotel_name = closest_match.iloc[0]["name"]
        selected_hotel = hotels[hotels["name"] == hotel_name].iloc[0]
        st.success(f"🏨 Selected Hotel: {selected_hotel['name']}")

        # Show sorted nearby attractions
        sorted_attractions = sort_attractions_by_distance(selected_hotel, attractions)
        st.subheader(f"Top 10 Nearby Attractions from: {selected_hotel['name']}")
        st.dataframe(
            sorted_attractions[['name', 'distance_km', 'street name', 'short description']].head(10).reset_index(drop=True),
            use_container_width=True
        )

    else:
        st.warning("No hotel found near your click. Try zooming in or clicking more precisely.")