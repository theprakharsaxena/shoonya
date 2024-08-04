from passlib.hash import bcrypt
from models import *
from datetime import date
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
import requests
import base64
from passlib.hash import bcrypt
# DYTE_ORG_ID = "b1789fd1-17c6-41a6-9fdd-8f019ccb22f2"
# DYTE_API_KEY = "f8719e53f63c936e9067"
DYTE_ORG_ID = "e036961b-979c-4d9b-a287-9eedd30ec5dc"
DYTE_API_KEY = "49afdbf6230583a469ac"
API_HASH = base64.b64encode(f"{DYTE_ORG_ID}:{DYTE_API_KEY}".encode('utf-8')).decode('utf-8')

def add_participant(participant_email, participant_name, meeting_id, permission):
     url  = f"https://api.dyte.io/v2/meetings/{meeting_id}/participants"
     print('Adding participants by url : ', url)
     headers = {
          "Authorization":"Basic "+str(API_HASH)
     }
     data = {
          "name":participant_name,
          "preset_name":permission,
          "custom_participant_id":participant_email
     }
     response = requests.post(url=url, json=data, headers=headers)
     response = response.json()
     print(response)
     if response.get('success'):
          return {'auth_token':response['data']['token'],'uuid':response['data']['id']}
     else:
          return {'auth_token':None,'uuid':None}

def remove_participant(participant_uuid, meeting_id):
     url = f"https://api.dyte.io/v2/meetings/{meeting_id}/participants/{participant_uuid}"
     headers = {
          "Authorization":"Basic "+str(API_HASH)
     }
     response = requests.delete(url, headers=headers)
     response = response.json()
     print(response,'-----------------')
     return response['success']

def create_meeting_dyte(title):
     meeting_id = None
     url = "https://api.dyte.io/v2/meetings"
     headers = {
          "Authorization": "Basic "+str(API_HASH)
     }
     data = {
          "title":title
     }
     try:
          response = requests.post(url, json=data, headers=headers)
          meeting_data = response.json()
          print('Meeting has been created Successfully')
          meeting_id = meeting_data['data']['id']
          print('meeting id - ',meeting_id)
          return {'meeting_id':meeting_id, 'status':True}
     except Exception as e:
          return {'meeting_id':str(e), 'status':True}
