import pandas as pd

# load the amenities data: amenities-vancouver.json.gz
df = pd.read_json('data/amenities-vancouver.json.gz', compression='gzip', lines=True)

df.to_csv('data/vancouver_amenities.csv', index=False)

# get the type of amenities
amenities = df['amenity'].unique()
print(amenities)