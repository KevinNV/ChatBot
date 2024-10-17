# -*- coding: utf-8 -*-
"""
Created on Fri Oct 18 01:49:50 2024

@author: kevin
"""

#Import libraries
import json
import boto3

def lambda_handler(event, context):
    client = boto3.client('lexv2-runtime')
    #print(event)
    if event['httpMethod'] == 'GET':
        return {'statusCode': 200,
        'headers': {'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'},
        'body': json.dumps({'message': 'Welcome to the Chatbot API. Please use POST to send messages.'})}
    
    body = json.loads(event.get("body", "{}"))
    last_user_message = body.get("inputTranscript", "Hi")
    session_id = body.get("sessionId", "default-session")
    #print(session_id)
    
    if not last_user_message or len(last_user_message) < 1:
        botMessage = "Please try again."
        return {
            'statusCode': 200,
            'headers': {
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "*"
            },
            'body': json.dumps({"response": botMessage})
        }
     
    try:
        
        response = client.recognize_text(
            botId='92MRFL2QHD',
            botAliasId='EP90I7GF1K',
            localeId='en_US',
            sessionId=session_id,
            text=last_user_message
        )
        #print(response)
        lex_response = response.get('messages', [])
        
        if lex_response and len(lex_response) > 0:
            last_user_message = lex_response[0].get('content', 'Sorry, I did not understand that.')
        else:
            last_user_message = "System is Down!"
    
    except Exception as e:
        print(f"Error calling Lex bot: {str(e)}")
        last_user_message = "There was an error processing your request. Please try again later."
    
    return {
        "statusCode": 200,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
            'Content-Type': 'application/json'
        },
        "body": json.dumps({"response": last_user_message})
    }