import pandas as pd

# load the amenities data: amenities-vancouver.json.gz
df = pd.read_json('data/amenities-vancouver.json.gz', compression='gzip', lines=True)

# filter out the neccessary amenities columns
amenity_categories = {
  "food & drink": [
    'cafe', 'fast_food', 'bbq', 'restaurant', 'pub', 'bar', 'food_court', 'ice_cream', 'bistro', 'juice_bar', 'internet_cafe', 'disused:restaurant', 'water_point', 'biergarten'
  ],
  "transportation": [
    'fuel', 'parking_entrance', 'bicycle_parking', 'parking', 'ferry_terminal', 'car_rental', 'car_sharing', 'bicycle_rental', 'seaplane terminal', 'charging_station', 'parking_space', 'taxi', 'bus_station', 'motorcycle_parking', 'boat_rental', 'EVSE', 'motorcycle_rental'
  ],
  "entertainments & culture": [
    'place_of_worship', 'cinema', 'theatre', 'library', 'arts_centre', 'fountain', 'photo_booth', 'nightclub', 'clock', 'stripclub', 'gambling', 'playground', 'meditation_centre', 'spa', 'lounge', 'gym', 'park', 'casino', 'leisure'
  ],
  "health & emergency": [
    'pharmacy', 'dentist', 'doctors', 'clinic', 'veterinary', 'hospital', 'first_aid', 'healthcare', 'chiropractor', 'Pharmacy', 
  ],
  "shop & services": [
    'post_office', 'atm', 'childcare', 'bank', 'car_wash', 'luggage_locker', 'bureau_de_change', 'marketplace', 'atm;bank', 'shop|clothes'
  ],
  "others": [
    'toilets', 'post_box', 'telephone', 'vending_machine', 'school', 'bench', 'community_centre', 'waste_basket', 'public_building', 'drinking_water', 'shelter', 'recycling', 'public_bookcase', 'university', 'dojo', 'bicycle_repair_station', 'waste_disposal', 'social_facility', 'college', 'construction', 'post_depot', 'nursery', 'kindergarten', 'conference_centre', 'shower', 'trolley_bay', 'fire_station', 'police', 'compressed_air', 'family_centre', 'townhall', 'music_school', 'scrapyard', 'language_school', 'courthouse', 'events_venue', 'prep_school', 'cram_school', 'science', 'ATLAS_clean_room', 'workshop', 'safety', 'lobby', 'animal_shelter', 'social_centre', 'vacuum_cleaner', 'smoking_area', 'studio', 'ranger_station', 'storage_rental', 'watering_place', 'trash', 'sanitary_dump_station', 'Observation Platform', 'housing co-op', 'driving_school', 'loading_dock', 'monastery', 'storage', 'payment_terminal', 'waste_transfer_station', 'office|financial', 'hunting_stand', 'money_transfer', 'letter_box', 'training', 'car_rep', 'research_institute'
  ],
}

# create the amenities dataframe
category_map = pd.Series({
  amenity: category
  for category, amenities in amenity_categories.items()
  for amenity in amenities
})

df['category'] = df['amenity'].map(category_map).fillna('others')
df = df.dropna(subset=['lon', 'lat']) # drop rows with missing lon/lat
 
# create a csv file from the dataframe
df.to_csv('data/vancouver_amenities.csv', index=False)