import pandas as pd
import geopandas as gpd
import numpy as np
from sklearn.cluster import DBSCAN
from shapely.geometry import Point
import streamlit as st

@st.cache_data(show_spinner="Clustering amenities...")
def get_clusters():
    """
    Load amenities data, perform DBSCAN clustering, and return clustered dataframes for each category.
    
    Returns:
    - clustered_dfs: A dictionary of clustered dataframes for each category.
    """
    # load amenities data
    amenities = pd.read_csv('data/vancouver_amenities.csv')

    # create geometry column
    amenities['geometry'] = amenities.apply(lambda row: Point(row['lon'], row['lat']), axis=1)

    # create a geodataframe with epsg: 4326 for Vancouver
    amenities_gdf = gpd.GeoDataFrame(amenities, geometry='geometry', crs='EPSG:4326')

    # convert to epsg 26910 for DBSCAN
    amenities_gdf = amenities_gdf.to_crs(epsg=26910)

    # DBSCAN clustering for each category:
    # - 'food & drink'
    # - 'transportation'
    # - 'entertainments & culture'
    # - 'health & emergency'
    # - 'shop & services'
    # DBSCAN parameters tuned per category
    dbscan_params = {
        'food & drink': {'eps': 200, 'min_samples': 15},  # high density
        'transportation': {'eps': 250, 'min_samples': 10},  # medium density
        'entertainments & culture': {'eps': 300, 'min_samples': 8},  # sparse but localized
        'health & emergency': {'eps': 300, 'min_samples': 5},  # very sparse
        'shop & services': {'eps': 300, 'min_samples': 8}  # sparse but localized
    }

    clustered_dfs = {}
    categories = ['food & drink', 'transportation', 'entertainments & culture', 'health & emergency', 'shop & services']
    for category in categories:
        # create a subdataframe for each category
        category_df = amenities_gdf[amenities_gdf['category'] == category].copy()

        # get the coordinates in meters
        coords = np.vstack(category_df.geometry.apply(lambda geom: (geom.x, geom.y)))

        # DBSCAN clustering
        # eps: radius of neighborhood in meters
        # min_samples: minimum number of samples in a neighborhood to form a cluster
        params = dbscan_params.get(category, {'eps': 300, 'min_samples': 10})
        dbscan = DBSCAN(eps=params['eps'], min_samples=params['min_samples']).fit(coords)
        category_df['cluster'] = dbscan.labels_

        # filter out noise (-1)
        category_df = category_df[category_df['cluster'] != -1]
        
        # append to the list of clustered dataframes
        clustered_dfs[category] = category_df

    # convert back to epsg 4326
    for category in clustered_dfs:
        clustered_dfs[category] = clustered_dfs[category].to_crs(epsg=4326)
        clustered_dfs[category].reset_index(drop=True, inplace=True)
        clustered_dfs[category]['geometry'] = clustered_dfs[category].geometry.apply(lambda geom: Point(geom.x, geom.y))
        clustered_dfs[category]['lat'] = clustered_dfs[category].geometry.apply(lambda geom: geom.y)
        clustered_dfs[category]['lon'] = clustered_dfs[category].geometry.apply(lambda geom: geom.x)
    # drop geometry column
    for category in clustered_dfs:
        clustered_dfs[category].drop(columns=['geometry'], inplace=True)

    return clustered_dfs