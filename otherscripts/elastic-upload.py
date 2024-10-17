# -*- coding: utf-8 -*-
"""
Created on Tue Oct  8 07:47:12 2024

@author: kevin
"""

import boto3
import requests
from requests_aws4auth import AWS4Auth

# Initialize AWS session and credentials
session = boto3.Session()
credentials = session.get_credentials()
region = 'us-east-1'  # Replace with your AWS region

# AWS4Auth for signing the request with IAM credentials
auth = AWS4Auth(credentials.access_key, credentials.secret_key, region, 'es', session_token=credentials.token)

# OpenSearch Bulk API endpoint
url = 'https://search-restaurants-t2in7xlj52ss6btfgkupyyouze.us-east-1.es.amazonaws.com/_bulk'

# Load the bulk JSON file (update the path to your file)
with open('bulk_restaurants.json', 'r') as file:
    bulk_data = file.read()

# Send the POST request to OpenSearch
headers = {"Content-Type": "application/json"}
response = requests.post(url, headers=headers, data=bulk_data, auth=auth)

# Check the response
if response.status_code == 200:
    print("Bulk data uploaded successfully!")
else:
    print(f"Error: {response.status_code}")
    print(response.text)
