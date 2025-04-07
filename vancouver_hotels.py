import pandas as pd
import geopandas as gpd 
import folium

gdf = gpd.read_file("data/vancouver_hotels.geojson")
df = pd.DataFrame(gdf.drop(columns='geometry'))

# we will filter out the neccessary columns from the dataframe
hotels = df[[
  'id',
  'name',
  'addr:housenumber',
  'addr:unit',
  'addr:street',
  'addr:city',
  'addr:province',
  'addr:postcode',
]]

hotels = hotels.rename(columns={
  'addr:housenumber': 'housenumber',
  'addr:unit': 'unit',
  'addr:street': 'street',
  'addr:city': 'city',
  'addr:province': 'province',
  'addr:postcode': 'postcode'
})

# channge the id to indexing numbers
hotels['id'] = hotels.index + 1

# since the some rows have missing province and city, we will fill them with 'BC' and 'Vancouver'
# and missing postcode with 'N/A'
hotels['province'] = hotels['province'].fillna('BC')
hotels['city'] = hotels['city'].fillna('Vancouver')
hotels['postcode'] = hotels['postcode'].fillna('N/A')

# create a csv file from the dataframe
hotels.to_csv('data/vancouver_hotels.csv', index=False)

# 🎯 Create and save a map using Folium
hotel_map = folium.Map(location=[49.2827, -123.1207], zoom_start=12)  # Centered on Vancouver

for _, row in gdf.iterrows():
    geom = row.geometry
    if geom is not None:
        # Get a Point location (use centroid if it's a polygon)
        if geom.geom_type == 'Point':
            lat = geom.y
            lon = geom.x
        else:
            centroid = geom.centroid
            lat = centroid.y
            lon = centroid.x

        popup = row.get("name", "Unnamed Hotel")
        folium.Marker(location=[lat, lon], popup=popup).add_to(hotel_map)

# Save the map to HTML file
hotel_map.save("data/vancouver_hotels_map.html")
print("Succesfully! Hotel data saved and map generated at: data/vancouver_hotels_map.html")