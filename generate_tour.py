import osmnx as ox
import networkx as nx
import streamlit as st

@st.cache_data(show_spinner="Finding the best route...")
def get_osmnx_graph(center, dist):
    """
    Download the OSMnx walking network graph centered at a given point.

    Arguments:
    - center: A tuple (latitude, longitude) for the center point.
    - dist: Distance in meters to download the OSMnx graph (default=5000).

    Returns:
    - G: The OSMnx graph object.
    """
    # Download the walking network using osmnx
    G = ox.graph_from_point(center, dist=dist, network_type='walk')
    return G

def generate_tsp_route(selected_hotel, attractions):
    """
    Generate a tour route using a Traveling Salesman Problem (TSP) solution.

    Arguments:
    - selected_hotel: A row from the hotels GeoDataFrame for the selected hotel.
    - attractions: A pandas DataFrame of attractions with 'lat' and 'lon' columns.
    - buffer_dist: Distance in meters to download the OSMnx walking network (default=5000).

    Returns:
    - List of coordinate tuples (lat, lon) representing the route.
    """
    # Get the hotel distance from the furthest attraction
    max_dist = attractions['distance_km'].max()
    buffer_dist = int(max_dist * 1000) + 500  # Add a buffer of 500m
    
    # Center the graph on the hotel location
    center = (selected_hotel.geometry.y, selected_hotel.geometry.x)

    # Download the walking network using osmnx
    G = get_osmnx_graph(center, dist=buffer_dist)
    
    # Prepare the list of points starting with the hotel and then all attractions
    tour_points = [(selected_hotel.geometry.y, selected_hotel.geometry.x)]
    stop_names = [selected_hotel['name']]
    tour_points += list(zip(attractions['lat'], attractions['lon']))
    stop_names += list(attractions['name'])
    
    # Map each point to the nearest node in the osmnx graph
    nodes = []
    for lat, lon in tour_points:
        # Note: osmnx.nearest_nodes expects (longitude, latitude)
        node = ox.distance.nearest_nodes(G, lon, lat)
        nodes.append(node)
    
    # Build a complete graph of these nodes using networkx
    complete_graph = nx.complete_graph(len(nodes))
    for i, u in enumerate(nodes):
        for j, v in enumerate(nodes):
            if i != j:
                # Compute the shortest path length between nodes u and v in G
                try:
                    length = nx.shortest_path_length(G, u, v, weight='length')
                except nx.NetworkXNoPath:
                    length = float('inf')
                complete_graph[i][j]['weight'] = length
    
    # Solve the TSP on the complete graph (using networkx's approximation algo)
    tsp_order = nx.approximation.traveling_salesman_problem(complete_graph, weight='weight')

    # Get the stops (names and original coordinates) in TSP order
    ordered_stop_names = [stop_names[i] for i in tsp_order]
    
    # Convert TSP order indices back to OSMnx node IDs
    ordered_nodes = [nodes[i] for i in tsp_order]
    
    # Generate the full route by concatenating shortest paths between successive nodes
    full_route = []
    segment_distances = [] # store the distances between segments
    for i in range(len(ordered_nodes) - 1):
        route_segment = nx.shortest_path(G, ordered_nodes[i], ordered_nodes[i+1], weight='length')
        # Get the distance of the segment
        distance_segment = nx.shortest_path_length(G, ordered_nodes[i], ordered_nodes[i+1], weight='length')
        segment_distances.append(distance_segment)
        # Avoid duplicating nodes between segments
        full_route.extend(route_segment[:-1])
    full_route.append(ordered_nodes[-1])
    
    # Extract coordinate pairs from the full route
    route_coords = [(G.nodes[node]['y'], G.nodes[node]['x']) for node in full_route]
    
    return route_coords, ordered_stop_names, segment_distances

def generate_nn_route(selected_hotel, attractions, buffer_dist=5000):
    """
    Generate a tour route using a greedy nearest neighbor approach.
    
    Arguments:
    - selected_hotel: A row from the hotels GeoDataFrame for the selected hotel.
    - attractions: A pandas DataFrame of attractions with 'lat' and 'lon' columns.
    - buffer_dist: Distance in meters to download the OSMnx walking network.
    
    Returns:
    - route_coords: List of coordinate tuples (lat, lon) representing the full route (for mapping).
    - ordered_stop_names: List of stop names (hotel + attractions) in the order visited.
    - segment_distances: List of distances (in meters) for each segment between consecutive stops.
    """
    # Get the hotel distance from the furthest attraction
    max_dist = attractions['distance_km'].max()
    buffer_dist = int(max_dist * 1000) + 500  # Add a buffer of 500m
    
    # Center the graph on the hotel location
    center = (selected_hotel.geometry.y, selected_hotel.geometry.x)

    # Download the walking network using osmnx
    G = get_osmnx_graph(center, dist=buffer_dist)
    
    # Build a list of points and stop names: hotel first, then all attractions
    tour_points = [(selected_hotel.geometry.y, selected_hotel.geometry.x)]
    stop_names = [selected_hotel['name']]
    tour_points += list(zip(attractions['lat'], attractions['lon']))
    stop_names += list(attractions['name'])
    
    # Map each point to its nearest node in the graph
    nodes = []
    for lat, lon in tour_points:
        # osmnx.nearest_nodes expects (longitude, latitude)
        node = ox.distance.nearest_nodes(G, lon, lat)
        nodes.append(node)
    
    n = len(nodes)
    visited = [False] * n
    order = []
    segment_distances = []
    
    # Start at the hotel (first index)
    current = 0
    order.append(current)
    visited[current] = True
    
    # Greedy loop: choose the nearest unvisited node at each step
    for _ in range(1, n):
        best_distance = float('inf')
        best_idx = None
        for j in range(n):
            if not visited[j]:
                try:
                    d = nx.shortest_path_length(G, nodes[current], nodes[j], weight='length')
                except nx.NetworkXNoPath:
                    d = float('inf')
                if d < best_distance:
                    best_distance = d
                    best_idx = j
        if best_idx is None:
            break  # no unvisited nodes remain
        order.append(best_idx)
        visited[best_idx] = True
        segment_distances.append(best_distance)
        current = best_idx

    # Build the full route by concatenating shortest paths between stops in the determined order
    full_route = []
    for i in range(len(order) - 1):
        route_segment = nx.shortest_path(G, nodes[order[i]], nodes[order[i+1]], weight='length')
        # Avoid duplicating the last node (except for the final segment)
        full_route.extend(route_segment[:-1])
    full_route.append(nodes[order[-1]])

    # Add cyclic return to the hotel
    return_segment = nx.shortest_path(G, nodes[order[-1]], nodes[0], weight='length')
    full_route.extend(return_segment[1:])  # avoid duplicating the first node
    segment_distances.append(nx.shortest_path_length(G, nodes[order[-1]], nodes[0], weight='length'))
    order.append(0)  # return to hotel in the order list
    
    # Convert node IDs to coordinate pairs (lat, lon) for mapping
    route_coords = [(G.nodes[node]['y'], G.nodes[node]['x']) for node in full_route]
    
    # Get the ordered stop names in the sequence determined by the greedy approach
    ordered_stop_names = [stop_names[i] for i in order]
    
    return route_coords, ordered_stop_names, segment_distances
