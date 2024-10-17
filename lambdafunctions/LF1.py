# -*- coding: utf-8 -*-
"""
Created on Fri Oct 18 01:49:13 2024

@author: kevin
"""

#Import libraries
import json
import boto3

sqs = boto3.client('sqs')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('usst')
ses = boto3.client('ses')

QUEUE_URL = 'https://sqs.us-east-1.amazonaws.com/135808918511/custInfo'

#-------------------------------------------------------------------------------
#Additional functions

def close(sessionAttributes, name, fulfillment_state, message):
    return {
        "sessionState": {
            "sessionAttributes": sessionAttributes,
            "dialogAction": {
                "type": "Close"
            },
            "intent": {
                "name": name,
                "state": fulfillment_state
            }
        },
        "messages": [
            {
                "contentType": message['contentType'],
                "content": message['content']
            }
        ]
    }

def send_to_sqs(location, cuisine, time, people, email, sessionID):
    message_body = {
        'location': location,
        'cuisine': cuisine,
        'time': time,
        'people': people,
        'email': email,
        'sessionID': sessionID
    }

    response = sqs.send_message(
        QueueUrl=QUEUE_URL,
        MessageBody=json.dumps(message_body)
    )
    return response
    
def get_previous_search(session_id):
    try:
        response = table.get_item(Key={'SessionID': session_id})
        return response.get('Item')
    except:
        return None



#-------------------------------------------------------------------------------
#Main Intents

def Greeting(intent_request, sessionAttributes):
    userInput = intent_request['inputTranscript'].lower()
    firstUtterances = ['hi', 'hello', 'i need help', 'can you help me?']
    greeted = sessionAttributes.get('greeted', 'false')
    
    if any(response in userInput for response in firstUtterances):
        sessionAttributes['greeted'] = 'true'
        
        return {
            "sessionState": {
                "sessionAttributes": sessionAttributes,
                "dialogAction": {
                    "type": "ElicitIntent"
                }
            },
            "messages": [
                {
                    "contentType": "PlainText",
                    "content": "Hi! I'm BB, a Dining Concierge bot. Would you like help finding a restaurant?"
                }
            ]
        }
        
    
    utterances = ['yes', 'sure', 'ok', 'yep', 'definitely']
    if any(response in userInput for response in utterances) and greeted == 'true':
        return DiningSuggestions(intent_request, sessionAttributes)
    

        
        
def DiningSuggestions(intent_request, sessionAttributes):
    phase = sessionAttributes.get('phase', 'location')
    Id = intent_request['sessionId']

    slots = intent_request['sessionState']['intent']['slots']
    
    location = slots.get('Location', {}).get('value', {}).get('interpretedValue') if slots.get('Location') and slots.get('Location').get('value') else None
    cuisine = slots.get('Cuisine', {}).get('value', {}).get('interpretedValue') if slots.get('Cuisine') and slots.get('Cuisine').get('value') else None
    time = slots.get('Time', {}).get('value', {}).get('interpretedValue') if slots.get('Time') and slots.get('Time').get('value') else None
    people = slots.get('People', {}).get('value', {}).get('interpretedValue') if slots.get('People') and slots.get('People').get('value') else None
    email = slots.get('Email', {}).get('value', {}).get('interpretedValue') if slots.get('Email') and slots.get('Email').get('value') else None
    
    if phase == 'location':
        if location:
            return elicit_cuisine(intent_request, sessionAttributes, location)
        else:
            return elicit_location(intent_request, sessionAttributes)

    elif phase == 'cuisine':
        if cuisine:
            return elicit_time(intent_request, sessionAttributes, location, cuisine)
        else:
            return elicit_cuisine(intent_request, sessionAttributes, location)
    
    elif phase == 'time':
        if time:
            return elicit_people(intent_request, sessionAttributes, location, cuisine, time)
        else:
            return elicit_time(intent_request, sessionAttributes, location, cuisine)
    elif phase == 'people':
        if people:
            return elicit_email(intent_request, sessionAttributes, location, cuisine, time, people)
        else:
            return elicit_people(intent_request, sessionAttributes, location, cuisine, time)
    elif phase == 'email':
        if email:
            
            send_to_sqs(location, cuisine, time, people, email, Id)
            
            return {
                "sessionState": {
                    "sessionAttributes": sessionAttributes,
                    "dialogAction": {
                        "type": "Close"
                    },
                    "intent": {
                        "name": "DiningSuggestionsIntent",
                        "state": "Fulfilled"
                    }
                },
                "messages": [
                    {
                        "contentType": "PlainText",
                        "content": f"Thanks! We will find {cuisine} restaurants with a reservation available for {people} at {time} in {location} for you. I will email that list to you at {email}."
                    }
                ]
            }
        else:
            if location == None:
                return elicit_location(intent_request, sessionAttributes)
            return elicit_email(intent_request, sessionAttributes, location, cuisine, time, people)

def ThankYou(intent_request, sessionAttributes):
    return close(
            sessionAttributes,
            "ThankYouIntent",
            "Fulfilled",
            {
                "contentType": "PlainText",
                "content": "You are welcome!"
            }
        )

#---------------------------------------------------------------------------------------------------------
#Eliciting Functions

def elicit_location(intent_request, sessionAttributes):
    sessionAttributes['phase'] = 'location'
    return {
        "sessionState": {
            "sessionAttributes": sessionAttributes,
            "dialogAction": {
                "type": "ElicitSlot",
                "slotToElicit": "Location"
            },
            "intent": {
                "name": "DiningSuggestionsIntent",
                "slots": {
                    "Location": None,
                    "Cuisine": None,
                    "Time": None,
                    "People": None,
                    "Email": None
                }
            }
        },
        "messages": [
            {
                "contentType": "PlainText",
                "content": "Which location would you prefer? We have Manhattan, Brooklyn, and Queens."
            }
        ]
    }

    
def elicit_cuisine(intent_request, sessionAttributes, location):
    sessionAttributes['phase'] = 'cuisine'
    return {
        "sessionState": {
            "sessionAttributes": sessionAttributes,
            "dialogAction": {
                "type": "ElicitSlot",
                "slotToElicit": "Cuisine"
            },
            "intent": {
                "name": "DiningSuggestionsIntent",
                "slots": {
                    "Location": {
                        "value": {
                            "interpretedValue": location
                        }
                    },
                    "Cuisine": None,
                    "Time": None,
                    "People": None,
                    "Email": None
                }
            }
        },
        "messages": [
            {
                "contentType": "PlainText",
                "content": "What type of cuisine would you prefer? We have American, Chinese, Indian, Japanese, Mexican, Thai, Italian."
            }
        ]
    }
    

def elicit_time(intent_request, sessionAttributes, location, cuisine):
    sessionAttributes['phase'] = 'time'
    return {
        "sessionState": {
            "sessionAttributes": sessionAttributes,
            "dialogAction": {
                "type": "ElicitSlot",
                "slotToElicit": "Time"
            },
            "intent": {
                "name": "DiningSuggestionsIntent",
                "slots": {
                    "Location": {
                        "value": {
                            "interpretedValue": location
                        }
                    },
                    "Cuisine": {
                        "value": {
                            "interpretedValue": cuisine
                        }
                    },
                    "Time": None,
                    "People": None,
                    "Email": None
                }
            }
        },
        "messages": [
            {
                "contentType": "PlainText",
                "content": "What time would you like to make the reservation?"
            }
        ]
    }
    

def elicit_people(intent_request, sessionAttributes, location, cuisine, time):
    sessionAttributes['phase'] = 'people'
    return {
        "sessionState": {
            "sessionAttributes": sessionAttributes,
            "dialogAction": {
                "type": "ElicitSlot",
                "slotToElicit": "People"
            },
            "intent": {
                "name": "DiningSuggestionsIntent",
                "slots": {
                    "Location": {
                        "value": {
                            "interpretedValue": location
                        }
                    },
                    "Cuisine": {
                        "value": {
                            "interpretedValue": cuisine
                        }
                    },
                    "Time": {
                        "value": {
                            "interpretedValue": time
                        }
                    },
                    "People": None,
                    "Email": None
                }
            }
        },
        "messages": [
            {
                "contentType": "PlainText",
                "content": "This table needs to be for how many people?"
            }
        ]
    }


def elicit_email(intent_request, sessionAttributes, location, cuisine, time, people):
    sessionAttributes['phase'] = 'email'
    return {
        "sessionState": {
            "sessionAttributes": sessionAttributes,
            "dialogAction": {
                "type": "ElicitSlot",
                "slotToElicit": "Email"
            },
            "intent": {
                "name": "DiningSuggestionsIntent",
                "slots": {
                    "Location": {
                        "value": {
                            "interpretedValue": location
                        }
                    },
                    "Cuisine": {
                        "value": {
                            "interpretedValue": cuisine
                        }
                    },
                    "Time": {
                        "value": {
                            "interpretedValue": time
                        }
                    },
                    "People": {
                        "value": {
                            "interpretedValue": people
                        }
                    },
                    "Email": None
                }
            }
        },
        "messages": [
            {
                "contentType": "PlainText",
                "content": "Please provide me with an email address and I will send over the list of restaurants."
            }
        ]
    }


    

#---------------------------------------------------------------------------------------------------
#Main Functions
    
def dispatch(intent_request):
    intent_name = intent_request['sessionState']['intent']['name']
    sessionAttributes = intent_request['sessionState'].get('sessionAttributes', {})
    #print(intent_name)
    
    response = None
    if intent_name == 'GreetingIntent':
        return Greeting(intent_request, sessionAttributes)
    elif intent_name == 'DiningSuggestionsIntent':
        return DiningSuggestions(intent_request, sessionAttributes)
    elif intent_name == 'ThankYouIntent':
        return ThankYou(intent_request, sessionAttributes)
    else:
        #print(intent_request['sessionId'])
        previous_search = get_previous_search(intent_request['sessionId'])
        if previous_search != None:
            # Give recommendations
            recommendation = f"Okay, based on your last search for {previous_search['LastCuisine']} restaurants in {previous_search['LastLocation']}, here are the recommendations: \n"
            for i, restaurant in enumerate(previous_search['Recommendations'], start=1):
                recommendation += f"{i}. {restaurant['Name']}, located at {restaurant['Address']}\n"
        
            ses.send_email(
                Source='kevinvaishnav15@gmail.com',
                Destination={'ToAddresses': [previous_search['Email']]},
                Message={
                    'Subject': {'Data': 'Old Recommendations'},
                    'Body': {'Text': {'Data': recommendation}}
                }
            )
        
            return close(
                sessionAttributes,
                "FallbackIntent",
                "Fulfilled",
                {
                    "contentType": "PlainText",
                    "content": f"{recommendation}"
                }
            )
            
        else:
            return close(
                sessionAttributes,
                "FallbackIntent",
                "Fulfilled",
                {
                    "contentType": "PlainText",
                    "content": "Okay, feel free to ask if you need to find a restaurant later."
                }
            )


def lambda_handler(event, context):
    response = dispatch(event)
    
    return {
        'sessionState': response.get('sessionState', {}),
        'messages': response.get('messages', []),
        'sessionId': event['sessionId']
    }