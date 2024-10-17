# -*- coding: utf-8 -*-
"""
Created on Tue Oct  8 06:00:21 2024

@author: kevin
"""

import json

# Load the JSON data from the file
with open('restaurants.json', 'r') as f:
    data = json.load(f)

bulk_data = []

for restaurant in data['restaurants']:
    # Extract RestaurantID and Cuisine
    restaurant_id = restaurant['id']
    cuisine = restaurant.get('cuisine', restaurant['categories'][0]['title'])  # Use cuisine or first category

    # Prepare the bulk upload format
    bulk_data.append({
        "index": {
            "_index": "restaurants",
            "_id": restaurant_id
        }
    })
    bulk_data.append({
        "RestaurantID": restaurant_id,
        "Cuisine": cuisine
    })

# Save the bulk data to a new file
with open('bulk_restaurants.json', 'w') as f:
    for entry in bulk_data:
        f.write(json.dumps(entry) + '\n')
