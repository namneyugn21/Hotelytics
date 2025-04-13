import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

def load_amenities():
    amenities = pd.read_csv("data/vancouver_amenities.csv")
    amenities['geometry'] = amenities.apply(lambda row: Point(row['lon'], row['lat']), axis=1)
    amenities = gpd.GeoDataFrame(amenities, geometry='geometry', crs="EPSG:4326") # convert to crs: EPSG:4326 for folium
    return amenities

def get_score_color(score, max_score):
    ratio = score / max_score if max_score > 0 else 0
    if ratio > 0.75:
        return 'green'
    elif ratio > 0.5:
        return 'orange'
    elif ratio > 0.25:
        return 'red'
    else:
        return 'darkred'

def score_hotels(hotels_gdf, ranking, buffer_m=350):
    """
    Score hotels based on the number of amenities within a certain buffer distance.

    Parameters:
    - hotels_gdf: GeoDataFrame containing hotel data with geometry.
    - amenities_gdf: GeoDataFrame containing amenities data with geometry.
    - ranking: List of amenity categories to rank by.
    - buffer_m: Buffer distance in meters.

    Returns:
    - DataFrame with hotels and their scores for each amenity category.
    """
    # convert the gdf crs to EPSG:26910 for distance calculations
    hotels_gdf = hotels_gdf.to_crs(epsg=26910)
    amenities_gdf = load_amenities()
    amenities_gdf = amenities_gdf.to_crs(epsg=26910)
    
    # create a result that stores the scores (total and each categories) of each hotel
    results = hotels_gdf.copy()
    results['total_score'] = 0
    category_scores = {category: [] for category in ranking.keys()}

    for _, hotel in results.iterrows():
        buffer = hotel.geometry.buffer(buffer_m) # create a buffer around the hotel
        total_score = 0
        temp_scores = {}

        for category, weight in ranking.items():
            # count amenities in the buffer
            count = amenities_gdf[
                (amenities_gdf['category'] == category) &
                (amenities_gdf.geometry.within(buffer))
            ].shape[0]
            weighted_score = count * weight
            temp_scores[category] = weighted_score
            total_score += weighted_score
        
        # append individual category scores
        for category in ranking:
            category_scores[category].append(temp_scores[category])

        # add total score
        results.at[hotel.name, 'total_score'] = total_score
    
    # attach individual category scores to results
    for category in ranking:
        results[f'score_{category.replace(" ", "_")}'] = category_scores[category]

    # normalize total score to 0–100
    max_total_score = results['total_score'].max()
    results['total_score'] = results['total_score'] / max_total_score * 100 if max_total_score > 0 else 0
    results['total_score'] = results['total_score'].round(2)

    # normalize individual category scores
    for category in ranking:
        col = f'score_{category.replace(" ", "_")}'
        max_cat_score = results[col].max()
        results[f'{col}_normalized'] = results[col] / max_cat_score * 100 if max_cat_score > 0 else 0

    # convert back to original CRS
    results = results.to_crs(epsg=4326)

    return results