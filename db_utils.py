from passlib.hash import bcrypt
from models import *
from datetime import date
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
import requests
import base64
from passlib.hash import bcrypt
DYTE_ORG_ID = "b1789fd1-17c6-41a6-9fdd-8f019ccb22f2"
DYTE_API_KEY = "f8719e53f63c936e9067"
API_HASH = base64.b64encode(f"{DYTE_ORG_ID}:{DYTE_API_KEY}".encode('utf-8')).decode('utf-8')

aws_access_key_id = 'DO00B6BEQU3R9ZCCLVDM'
aws_secret_access_key = 'krgNenN7zhGmMr0kH+dmSrTRH4AOtp8GGAej7D2rqYg'
region_name = 'us-east-1'
endpoint_url = 'https://shoonya-data.nyc3.digitaloceanspaces.com'

def convert_model_to_dict(model_list):
    result = []
    for model in model_list:
        program_dict = model.__dict__.copy()
        for key in program_dict.keys():
            if key.startswith('_'):
                del program_dict[key]
                break
        program_dict['id'] = model.id
        result.append(program_dict)
    return result

# def get_programmes_by_instructor(instructor_id):
#     current_date = date.today()
#     print("HERE!!!!!!")
#     programmes = Programme.query.filter_by(instructor_id=instructor_id).all()
#     print('-------------------------------',programmes[0].end_date, current_date)
#     ongoing_programmes = [programme for programme in programmes if programme.end_date >= current_date]
#     done_programmes = [programme for programme in programmes if programme.end_date < current_date]
#     return ongoing_programmes, done_programmes

def hash_password(password):
     return bcrypt.hash(password)