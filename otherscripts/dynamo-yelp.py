# -*- coding: utf-8 -*-
"""
Created on Mon Oct  7 23:57:21 2024

@author: kevin
"""

import json
import boto3
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

# Function to safely convert float to Decimal
def safe_decimal(value, precision=6):
    """
    Convert a float value to Decimal, rounding to avoid precision errors.
    """
    if value is None:
        return Decimal(0)
    return Decimal(value).quantize(Decimal(f'1.{"0" * precision}'), rounding=ROUND_HALF_UP)

# Initialize DynamoDB resource
dynamodb = boto3.resource('dynamodb')

# Define the DynamoDB table
table_name = 'yelp-restaurants'
table = dynamodb.Table(table_name)

# Load the JSON file containing the restaurant data
with open('restaurants.json', 'r') as file:
    data = json.load(file, parse_float=Decimal)  # Converts floats to Decimal

# Extract the list of restaurants
restaurants = data.get('restaurants', [])

# Function to insert a restaurant record into DynamoDB
def insert_restaurant(restaurant):
    try:
        # Extract the necessary fields from the restaurant data
        business_id = restaurant.get('id')
        name = restaurant.get('name')
        address = ', '.join(restaurant.get('location', {}).get('display_address', []))
        coordinates = restaurant.get('coordinates', {})
        num_reviews = safe_decimal(restaurant.get('review_count', 0))  # Safely convert to Decimal
        rating = safe_decimal(restaurant.get('rating', 0))  # Safely convert to Decimal
        zip_code = restaurant.get('location', {}).get('zip_code', '')

        # Get the current timestamp
        inserted_at = datetime.now().isoformat()

        # Construct the item to insert into DynamoDB
        item = {
            'RestaurantID': business_id,
            'Name': name,
            'Address': address,
            'Coordinates': {
                'Latitude': safe_decimal(coordinates.get('latitude', 0)),  # Safely convert to Decimal
                'Longitude': safe_decimal(coordinates.get('longitude', 0))  # Safely convert to Decimal
            },
            'NumberOfReviews': num_reviews,
            'Rating': rating,
            'ZipCode': zip_code,
            'insertedAtTimestamp': inserted_at
        }

        # Insert the item into DynamoDB
        table.put_item(Item=item)
        print(f"Inserted {name} successfully.")

    except Exception as e:
        print(f"Error inserting {restaurant.get('name')}: {e}")

# Iterate over the list of restaurants and insert them into DynamoDB
for restaurant in restaurants:
    insert_restaurant(restaurant)

print("All restaurant data has been processed.")
