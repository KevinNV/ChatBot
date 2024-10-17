# -*- coding: utf-8 -*-
"""
Created on Sun Oct  6 20:56:00 2024

@author: kevin
"""

import requests
import json
import time
import os

API_KEY = 'AYAjq-JAXLhQ8Razc6k2qlR1TpDtE_GUO_7zFY5uY1WiCxIFiT3NqQrD0jK0Xocr5t_aTiKhx0yBAy3joAEVir9RUC9Yf5v3d9BT1vbaQdC2EKQjKemal6xb6dcBZ3Yx'

def get_existing_data(file_name):
    """Load existing data from the JSON file if it exists."""
    if os.path.exists(file_name):
        with open(file_name, "r") as file:
            return json.load(file).get('restaurants', [])
    return []

def save_data_to_file(data, file_name):
    """Save data to the JSON file."""
    with open(file_name, "w") as file:
        json.dump({'restaurants': data}, file, indent=4)
    print(f"Data saved to {file_name}")

def get_restaurants(existing_data, target_count=1000):
    headers = {'Authorization': f"Bearer {API_KEY}"}
    url = 'https://api.yelp.com/v3/businesses/search'
    cuisines = ['italian', 'chinese', 'indian', 'american', 'mexican', 'thai', 'japanese']
    max_requests = 200
    max_offset = 190
    api_request_count = 0

    # Track how many restaurants have been fetched for each cuisine
    cuisine_count = {cuisine: 0 for cuisine in cuisines}

    # Count existing restaurants by cuisine
    for business in existing_data:
        cuisine_count[business['cuisine']] += 1

    # Fetch restaurants
    for cuisine in cuisines:
        while cuisine_count[cuisine] < target_count:
            for offset in range(0, max_offset, 50):
                if api_request_count >= max_requests:
                    print(f"Reached daily API request limit of {max_requests}.")
                    return existing_data  # Return the data collected so far

                if cuisine_count[cuisine] >= target_count:
                    break

                params = {
                    'limit': 50,
                    'location': 'Manhattan',
                    'term': cuisine,
                    'offset': offset
                }

                response = requests.get(url, headers=headers, params=params)
                api_request_count += 1

                if response.status_code == 200:
                    res = response.json()
                    res['cuisine'] = cuisine

                    for business in res.get('businesses', []):
                        if cuisine_count[cuisine] < target_count:
                            business['cuisine'] = cuisine
                            existing_data.append(business)
                            cuisine_count[cuisine] += 1

                    time.sleep(1)  # To avoid hitting rate limits

                else:
                    print(f"Error: {response.status_code}, {response.text}")
                    break

    return existing_data

# File path for saving/loading data
file_name = "restaurants_v2.json"

# Load existing data from the file
existing_data = get_existing_data(file_name)

# Get restaurants and append to existing data
updated_data = get_restaurants(existing_data, target_count=1000)

# Save updated data back to the file
save_data_to_file(updated_data, file_name)
