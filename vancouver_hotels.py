import pandas as pd
import geopandas as gpd 

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