# -*- coding: utf-8 -*-
"""
Created on Fri Oct 18 01:48:55 2024

@author: kevin
"""

#Import libraries
import boto3
import json
import random
import requests
from requests_aws4auth import AWS4Auth
from opensearchpy import OpenSearch, RequestsHttpConnection
import time

#Connect to OpenSearch  
region = 'us-east-1'
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, 'es', session_token=credentials.token)

client = OpenSearch(
hosts=[{'host': 'search-restaurants-t2in7xlj52ss6btfgkupyyouze.us-east-1.es.amazonaws.com', 'port': 443}],
http_auth=awsauth,
use_ssl=True,
verify_certs=True,
ssl_assert_hostname = False,
ssl_show_warn = False,
connection_class=RequestsHttpConnection
)

# Initialize services
sqs = boto3.client('sqs')
dynamodb = boto3.resource('dynamodb')
ses = boto3.client('ses')

queue_url = 'https://sqs.us-east-1.amazonaws.com/135808918511/custInfo'

#-------------------------------------------------------------------------------
#SQS Functions. Pull message from SQS has been moved to the lambda_handler function for convenience
'''
def pull_message_from_sqs(event):
    queue_url = 'https://sqs.us-east-1.amazonaws.com/135808918511/custInfo'
    print(event)
    
    for record in event['Records']:
        body = record['body']
        receipt_handle = record['receiptHandle']
        
        message_body = json.loads(body)
        location = message_body.get('location')
        cuisine = message_body.get('cuisine')
        time = message_body.get('time')
        people = message_body.get('people')
        user_email = message_body.get('email')
        session_id = message_body.get('sessionID')
        
        delete_sqs_message(queue_url, receipt_handle)
        
        return cuisine, user_email, location, time, people, session_id
    
    return None, None, None, None, None, None
'''
        

def delete_sqs_message(queue_url, receipt_handle):
    try:
        sqs.delete_message(
            QueueUrl=queue_url,
            ReceiptHandle=receipt_handle
        )
        print("Message deleted successfully from SQS.")
    except Exception as e:
        print(f"Error deleting message from SQS: {e}")

#-------------------------------------------------------------------------------
#Get restaurant details from OpensSearch/ElasticSearch and also from DynamoDB. Also, get saved recommendations for users from the database.

def get_random_restaurant_from_es(cuisine, count=3):
    
    query = {
        "query": {
            "match": {
                "Cuisine": cuisine.lower()
            }
        }
    }
    
    try:
        response = client.search(
            body=query,
            index="restaurants",
            size=count
        )
        
        if response['hits']['hits']:
            return [hit['_source'] for hit in response['hits']['hits']]
    except Exception as e:
        print(f"Error querying OpenSearch: {e}")
    
    return None

def get_restaurant_details(restaurant_id):
    table = dynamodb.Table('yelp-restaurants')
    response = table.get_item(Key={'RestaurantID': restaurant_id})
    
    if 'Item' in response:
        return response['Item']
    return None
    
    
def store_recommendations_in_dynamodb(session_id, location, cuisine, recommendations, email):
    table = dynamodb.Table('usst')
    try:
        table.put_item(
            Item={
                'SessionID': session_id,           
                'LastLocation': location,          
                'LastCuisine': cuisine,            
                'Recommendations': recommendations, 
                'Timestamp': int(time.time()),
                'Email': email
            }
        )
        print(f"Stored recommendations for session {session_id} in DynamoDB.")
    except Exception as e:
        print(f"Error storing recommendations in DynamoDB: {e}")

#-------------------------------------------------------------------------------
#Send the emails

def send_email_to_user(user_email, restaurants, location, time, people, cuisine):
    email_subject = f"Restaurant Suggestions"
    email_body = f"Hello! Here are my {cuisine} restaurant suggestions for {people} people, for today at {time}:\n"
    
    for i, restaurant in enumerate(restaurants, start=1):
        email_body += f"{i}. {restaurant['Name']}, located at {restaurant['Address']}\n"
    print("Hiiiii")
    response = ses.send_email(
        Source='kevinvaishnav15@gmail.com',
        Destination={'ToAddresses': [user_email]},
        Message={
            'Subject': {'Data': email_subject},
            'Body': {'Text': {'Data': email_body}}
        }
    )
    
    return response
    
#-------------------------------------------------------------------------------
#Main handler

def lambda_handler(event, context):
    queue_url = 'https://sqs.us-east-1.amazonaws.com/135808918511/custInfo'
    
    response = sqs.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=10,
        WaitTimeSeconds=10
    )

    if 'Messages' in response:
        for message in response['Messages']:
            message_body = json.loads(message['Body'])
            receipt_handle = message['ReceiptHandle']

            location = message_body.get('location')
            cuisine = message_body.get('cuisine')
            time = message_body.get('time')
            people = message_body.get('people')
            user_email = message_body.get('email')
            session_id = message_body.get('sessionID')

            if location and cuisine and user_email:
                #print(f"Processing message: {message_body}")
                
                restaurants = get_random_restaurant_from_es(cuisine)
                if restaurants:
                    detailed_restaurants = []
                    for restaurant in restaurants:
                        restaurant_details = get_restaurant_details(restaurant['RestaurantID'])
                        if restaurant_details:
                            detailed_restaurants.append(restaurant_details)
                    if detailed_restaurants:
                        store_recommendations_in_dynamodb(session_id, location, cuisine, detailed_restaurants, user_email)
                        send_email_to_user(user_email, detailed_restaurants, location, time, people, cuisine)
            
            delete_sqs_message(queue_url, receipt_handle)
    else:
        print("No messages in the queue")
    
    return {
        'statusCode': 200,
        'body': json.dumps('Lambda executed successfully!')
    }