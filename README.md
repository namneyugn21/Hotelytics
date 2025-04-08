# Hotelytics: Vancouver Hotel and Tour Generator

## Overview

This project uses OpenStreetMap (OSM) data to help users find the most suitable hotel in Vancouver based on surrounding amenities and walkability. It also generates a personalized walking tour from the selected hotel to nearby attractions using real street network data.

## Project Objectives

- Recommend hotels based on proximity to key amenities (e.g., food, transportation, culture).
- Allow users to assign weights to different amenity categories.
- Identify high-density zones of activity (hotspots) using clustering.
- Generate a walkable tour to nearby attractions once a hotel is selected.

## Data Sources

- **Hotels Dataset**: Extracted from OpenStreetMap (GeoJSON format), cleaned and standardized.
- **OSM Amenities**: `amenities-vancouver.json.gz`, categorized into tourism-relevant groups.
- **Curated Attractions List**: Custom list of high-quality Vancouver landmarks with coordinates and optional descriptions.

## Key Features

### 1. Hotel Scoring System

- Apply a 300-meter buffer around each hotel.
- Count the number of nearby amenities per category.
- Weight counts based on user preferences (e.g., food = 2, culture = 3).
- Optional enhancements:
  - Use DBSCAN clustering to detect and reward proximity to amenity hotspots.
  - Compute diversity scores based on category variety.

### 2. Walking Tour Generator

- Use Haversine distance to identify top nearby attractions from a selected hotel.
- Generate a realistic walking path using OpenStreetMap pedestrian data with `osmnx` and shortest path algorithms.
- Optionally enrich attractions with data from Wikidata or Wikipedia.

## Technologies and Tools

- **Data Processing**: `pandas`, `geopandas`, `shapely`
- **Spatial Analysis & Routing**: `osmnx`, `networkx`, `haversine`
- **Clustering**: `scikit-learn` (DBSCAN)
- **Visualization**: `folium`, `matplotlib`
- **Web Interface**: `streamlit`, `streamlit-folium`

## Deliverables

- Cleaned and categorized spatial datasets (GeoJSON and CSV)
- A fully functional Streamlit web application:
  - Hotel ranking based on user preferences
  - Interactive map of hotels and amenities
  - Tour path visualized on a dynamic map
- Visualizations:
  - Amenity distribution and density
  - Bar charts of hotel scores
  - Walking path maps
- Final report documenting:
  - Data pipeline
  - Scoring and routing logic
  - Application of data science concepts
  - Individual team member contributions


## Concepts Applied

This project applies multiple core data science concepts:

- **Graph Theory**: Street network modeled as a graph, used for shortest path routing.
- **Geospatial Analysis**: Coordinate projections, buffer zones, spatial joins, and clustering.
- **Feature Engineering**: Categorizing and weighting amenities for scoring models.
- **Clustering**: DBSCAN used to identify high-density zones of amenities.
- **Data Wrangling**: Cleaning and normalizing OpenStreetMap data and tags.
- **Decision Modeling**: Scoring logic reflects user-defined priorities and spatial context.

## How to Run

1. **Install Required Packages**  
   Make sure you have Python 3.8+ installed. Then install the required libraries by running the following commands:

   ```bash
   pip install streamlit
   pip install folium
   pip install streamlit-folium
   pip install pandas
   pip install geopandas
   pip install shapel

2. **Run with this commend line** 
  Navigate to the project directory in your terminal and run:

  ```bash
  streamlit run app.py


## Authors

This project was developed as part of a data science course at Simon Fraser University.  
Contributors: Nam Nguyen and Vi Phung
