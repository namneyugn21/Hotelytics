import pandas as pd
from shapely.geometry import Point
from math import radians, cos, sin, asin, sqrt

# --- Haversine formula ---
def haversine(lon1, lat1, lon2, lat2):
    """Calculate the great circle distance between two points on the earth (specified in decimal degrees). Returns distance in kilometers."""
    # convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # haversine formula
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371  # Radius of earth in kilometers
    return c * r

# --- Main sorting function ---
def sort_attractions_by_distance(hotel_row, attractions_df):
    """Given one hotel row and attraction dataframe, return attractions sorted by distance from hotel."""
    hotel_lat = hotel_row.geometry.y
    hotel_lon = hotel_row.geometry.x

    # Calculate distances
    attractions_df = attractions_df.copy()
    attractions_df['distance_km'] = attractions_df.apply(
        lambda row: haversine(hotel_lon, hotel_lat, row['lon'], row['lat']), axis=1
    )

    sorted_attractions = attractions_df.sort_values(by='distance_km')
    return sorted_attractions

# Example usage (commented out)
# hotel = hotels_df.iloc[0]  # one selected hotel
# sorted_df = sort_attractions_by_distance(hotel, attractions_df)
# print(sorted_df[['name', 'distance_km']].head())
