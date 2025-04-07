import pandas as pd

# load the amenities data: amenities-vancouver.json.gz
df = pd.read_json('data/amenities-vancouver.json.gz', compression='gzip', lines=True)

df.to_csv('data/vancouver_amenities.csv', index=False)

# get the type of amenities
amenities = df['amenity'].unique()
print(amenities)

# Normalize for matching (e.g., 'Pharmacy' → 'pharmacy')
df['amenity'] = df['amenity'].str.lower()

# Category mapping from your image
category_map = {
    # Food & Drink
    'cafe': 'Food & Drink', 'fast_food': 'Food & Drink', 'restaurant': 'Food & Drink',
    'pub': 'Food & Drink', 'bar': 'Food & Drink', 'bistro': 'Food & Drink',
    'ice_cream': 'Food & Drink', 'juice_bar': 'Food & Drink', 'food_court': 'Food & Drink',
    'biergarten': 'Food & Drink', 'casino': 'Food & Drink',

    # Transportation
    'bus_station': 'Transportation', 'taxi': 'Transportation', 'ferry_terminal': 'Transportation',
    'car_rental': 'Transportation', 'bicycle_rental': 'Transportation', 'motorcycle_rental': 'Transportation',
    'parking': 'Transportation', 'parking_entrance': 'Transportation', 'parking_space': 'Transportation',
    'bicycle_parking': 'Transportation', 'motorcycle_parking': 'Transportation',
    'evse': 'Transportation', 'compressed_air': 'Transportation', 'car_sharing': 'Transportation',
    'car_rep': 'Transportation', 'car_wash': 'Transportation',

    # Leisure & Culture
    'cinema': 'Leisure & Culture', 'theatre': 'Leisure & Culture', 'library': 'Leisure & Culture',
    'arts_centre': 'Leisure & Culture', 'museum': 'Leisure & Culture', 'park': 'Leisure & Culture',
    'playground': 'Leisure & Culture', 'nightclub': 'Leisure & Culture', 'spa': 'Leisure & Culture',
    'studio': 'Leisure & Culture', 'observation platform': 'Leisure & Culture',
    'stripclub': 'Leisure & Culture', 'gambling': 'Leisure & Culture', 'seaplane terminal': 'Leisure & Culture',
    'events_venue': 'Leisure & Culture', 'leisure': 'Leisure & Culture',

    # Health & Emergency
    'pharmacy': 'Health & Emergency', 'hospital': 'Health & Emergency', 'doctors': 'Health & Emergency',
    'dentist': 'Health & Emergency', 'clinic': 'Health & Emergency', 'first_aid': 'Health & Emergency',
    'fire_station': 'Health & Emergency', 'police': 'Health & Emergency', 'healthcare': 'Health & Emergency',
    'chiropractor': 'Health & Emergency', 'veterinary': 'Health & Emergency',

    # Education
    'school': 'Education', 'college': 'Education', 'university': 'Education', 'kindergarten': 'Education',
    'prep_school': 'Education', 'cram_school': 'Education', 'dojo': 'Education', 'music_school': 'Education',
    'language_school': 'Education', 'science': 'Education', 'training': 'Education',

    # Shops & Services
    'atm': 'Shops & Services', 'bank': 'Shops & Services', 'post_office': 'Shops & Services',
    'marketplace': 'Shops & Services', 'charging_station': 'Shops & Services',
    'storage_rental': 'Shops & Services', 'photo_booth': 'Shops & Services',
    'payment_terminal': 'Shops & Services', 'money_transfer': 'Shops & Services',
    'post_box': 'Shops & Services', 'letter_box': 'Shops & Services', 'bureau_de_change': 'Shops & Services',
    'shop|clothes': 'Shops & Services', 'office|financial': 'Shops & Services', 'atm;bank': 'Shops & Services',

    # Childcare & Family
    'childcare': 'Childcare & Family', 'nursery': 'Childcare & Family', 'family_centre': 'Childcare & Family',

    # Public Services
    'townhall': 'Public Services', 'courthouse': 'Public Services', 'public_building': 'Public Services',
    'conference_centre': 'Public Services', 'ranger_station': 'Public Services',

    # Religion
    'place_of_worship': 'Religion', 'monastery': 'Religion', 'meditation_centre': 'Religion',

    # Utilities
    'recycling': 'Utilities', 'waste_basket': 'Utilities', 'waste_disposal': 'Utilities',
    'trash': 'Utilities', 'sanitary_dump_station': 'Utilities', 'water_point': 'Utilities',
    'fountain': 'Utilities', 'watering_place': 'Utilities', 'drinking_water': 'Utilities',
    'scrapyard': 'Utilities', 'waste_transfer_station': 'Utilities',

    # Miscellaneous Facilities
    'toilets': 'Facilities', 'shower': 'Facilities', 'shelter': 'Facilities', 'bench': 'Facilities',
    'clock': 'Facilities', 'loading_dock': 'Facilities', 'vacuum_cleaner': 'Facilities',
    'studio': 'Facilities', 'internet_cafe': 'Facilities', 'luggage_locker': 'Facilities',
    'social_centre': 'Facilities', 'social_facility': 'Facilities', 'animal_shelter': 'Facilities',
    'storage': 'Facilities', 'lobby': 'Facilities', 'workshop': 'Facilities',
    'driving_school': 'Facilities', 'safety': 'Facilities', 'construction': 'Facilities',
    'observation platform': 'Facilities', 'public_bookcase': 'Facilities', 'ATLAS_clean_room': 'Facilities',
    'disused:restaurant': 'Facilities', 'housing co-op': 'Facilities', 'fuel': 'Facilities',
    'telephone': 'Facilities', 'vending_machine': 'Facilities'
}

# Assign category to each amenity
df['category'] = df['amenity'].map(category_map).fillna('misc')

# Save categorized version
df.to_csv('data/type_amenities.csv', index=False)
print("\n✅ Category column added and saved to data/type_amenities.csv")