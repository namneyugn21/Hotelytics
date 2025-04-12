import osmnx as ox
import networkx as nx
from sklearn.neighbors import NearestNeighbors
import numpy as np
import streamlit as st

@st.cache_data(show_spinner="Loading walking network...")
def get_osm_graph(lat, lon, dist=5000):
    return ox.graph_from_point((lat, lon), dist=dist, network_type='walk')

def generate_routes_from_hotel(hotel, attractions):
    """
    Generate optimized walking tour from a hotel to nearby attractions using sklearn NearestNeighbors.

    Parameters:
    - hotel: Hotel row with .geometry (GeoSeries).
    - attractions: GeoDataFrame with 'name', 'lon', 'lat' columns.

    Returns:
    - G: OSMnx walking graph
    - routes: list of (route_node_list, attraction_name)
    - tsp_name_path: ordered list of location names in tour
    """
    # Create a graph from the hotel location
    G = get_osm_graph(hotel.geometry.y, hotel.geometry.x, dist=5000)

    # Get the nearest node to the hotel
    hotel_node = ox.distance.nearest_nodes(G, hotel.geometry.x, hotel.geometry.y)
    attraction_nodes = []
    attraction_coords = []

    # Generate routes to each attraction
    for _, row in attractions.iterrows():
        node = ox.nearest_nodes(G, row['lon'], row['lat'])
        attraction_nodes.append((row['name'], node)) 
        attraction_coords.append((row['lon'], row['lat']))
    
    hotel_coords = (hotel.geometry.x, hotel.geometry.y)

    # Use sklearn to get nearest-neighbor tour
    coords = [hotel_coords] + attraction_coords
    coords_array = np.array(coords)

    nbrs = NearestNeighbors(n_neighbors=len(coords_array)).fit(coords_array)

    visited = [0]  # index of hotel
    current = 0

    while len(visited) < len(coords_array):
        dists, indices = nbrs.kneighbors([coords_array[current]])
        for idx in indices[0]:
            if idx not in visited:
                visited.append(idx)
                current = idx
                break

    # === Step 4: Reconstruct node path ===
    node_list = [hotel_node] + [node for _, node in attraction_nodes]
    tsp_node_path = [node_list[i] for i in visited]

    node_name_list = ['Hotel'] + [name for name, _ in attraction_nodes]
    tsp_name_path = [node_name_list[i] for i in visited]

    # === Step 5: Get real walking paths between tsp pairs ===
    routes = []
    for i in range(len(tsp_node_path) - 1):
        n1, n2 = tsp_node_path[i], tsp_node_path[i + 1]
        try:
            route = nx.shortest_path(G, n1, n2, weight='length')
            routes.append((route, tsp_name_path[i + 1]))  # (path, name)
        except:
            print(f"Could not find route between {tsp_name_path[i]} and {tsp_name_path[i + 1]}")

    return G, routes, tsp_name_path