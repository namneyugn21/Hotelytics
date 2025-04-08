import geopandas as gpd 

gdf = gpd.read_file("data/vancouver_hotels.geojson")

# filter relevant columns
hotels = gdf[[
  'id',
  'name',
  'addr:housenumber',
  'addr:unit',
  'addr:street',
  'addr:city',
  'addr:province',
  'addr:postcode',
  'geometry'
]]
hotels = hotels.rename(columns={
  'addr:housenumber': 'housenumber',
  'addr:unit': 'unit',
  'addr:street': 'street',
  'addr:city': 'city',
  'addr:province': 'province',
  'addr:postcode': 'postcode'
})

# filter out hotels that does not have a name
hotels = hotels[~hotels['name'].isna()]

# change the id to be 1-indexed
hotels['id'] = hotels.index + 1

# change the province and city to be BC and Vancouver and the missing postcodes to be N/A
hotels['province'] = hotels['province'].fillna('BC')
hotels['city'] = hotels['city'].fillna('Vancouver')
hotels['postcode'] = hotels['postcode'].fillna('N/A')

# extract representative point for each geometry (Point stays the same, Polygon becomes its centroid)
hotels_proj = hotels.to_crs(epsg=26910) # UTM zone 10N
hotels['centroid'] = hotels_proj.centroid
hotels['centroid'] = hotels.set_geometry('centroid').to_crs(epsg=4326)['centroid'] # conver back to WGS 84

hotels.to_csv('data/vancouver_hotels.csv', index=False)