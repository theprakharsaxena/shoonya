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
API_HASH = base64.b64encode(f"{DYTE_ORG_ID}:{DYTE_API_KEY}".encode("utf-8")).decode(
    "utf-8"
)

aws_access_key_id = "DO00B6BEQU3R9ZCCLVDM"
aws_secret_access_key = "krgNenN7zhGmMr0kH+dmSrTRH4AOtp8GGAej7D2rqYg"
region_name = "us-east-1"
endpoint_url = "https://shoonya-data.nyc3.digitaloceanspaces.com"


def convert_model_to_dict(model_list):
    result = []
    for model in model_list:
        program_dict = model.__dict__.copy()
        for key in program_dict.keys():
            if key.startswith("_"):
                del program_dict[key]
                break
        program_dict["id"] = model.id
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


# boto3.setup_default_session(
#         aws_access_key_id='your_access_key_id',
#         aws_secret_access_key='your_secret_access_key',
#     )


def generate_presigned_url_upload(bucket_name, object_name, expiration=3600):
    s3_client = boto3.client(
        "s3",
        region_name=region_name,
        endpoint_url=endpoint_url,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
    )
    try:
        response = s3_client.generate_presigned_url(
            "put_object",
            Params={"Bucket": bucket_name, "Key": object_name, "ACL": "public-read"},
            ExpiresIn=expiration,
        )
    except (NoCredentialsError, PartialCredentialsError):
        print("Credentials not available.")
        return ""
    return response


def generate_presigned_url_download(bucket_name, object_name, expiration=3600):
    s3_client = boto3.client(
        "s3",
        region_name=region_name,
        endpoint_url=endpoint_url,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
    )
    try:
        response = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket_name, "Key": object_name},
            ExpiresIn=expiration,
        )
    except (NoCredentialsError, PartialCredentialsError):
        print("Credentials not available.")
        return ""
    return response


def create_meeting_dyte(title):
    meeting_id = None
    url = "https://api.dyte.io/v2/meetings"
    headers = {"Authorization": "Basic " + str(API_HASH)}
    data = {"title": title}
    try:
        response = requests.post(url, json=data, headers=headers)
        meeting_data = response.json()
        print("Meeting has been created Successfully")
        meeting_id = meeting_data["data"]["id"]
        print("meeting id - ", meeting_id)
        return {"meeting_id": meeting_id, "status": True}
    except Exception as e:
        return {"meeting_id": str(e), "status": True}


def add_participant(participant_email, participant_name, meeting_id, permission):
    url = f"https://api.dyte.io/v2/meetings/{meeting_id}/participants"
    print("Adding participants by url : ", url)
    headers = {"Authorization": "Basic " + str(API_HASH)}
    data = {
        "name": participant_name,
        "preset_name": permission,
        "custom_participant_id": participant_email,
    }
    response = requests.post(url=url, json=data, headers=headers)
    response = response.json()
    print(response)
    if response.get("success"):
        return {"auth_token": response["data"]["token"], "uuid": response["data"]["id"]}
    else:
        return {"auth_token": "", "uuid": ""}


def remove_participant(participant_uuid, meeting_id):
    url = (
        f"https://api.dyte.io/v2/meetings/{meeting_id}/participants/{participant_uuid}"
    )
    headers = {"Authorization": "Basic " + str(API_HASH)}
    response = requests.delete(url, headers=headers)
    response = response.json()
    print(response, "-----------------")
    return response["success"]


from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from sqlalchemy.orm import joinedload


def get_program_details(program_id):
    program = Programme.query.filter(Programme.id == program_id).first()

    if not program:
        return None

    program_data = {
        "id": program.id,
        "name": program.name,
        "instructor_id": program.instructor_id,
        "issues": program.issues,
        "description": program.description,
        "start_date": program.start_date.isoformat(),
        "end_date": program.end_date.isoformat(),
        "published": program.published,
        "price": program.price,
        "discount_percent": program.discount_percent,
        "currency": program.currency,
        "program_time": program.program_time.isoformat(),
        "highlighted_priority": program.highlighted_priority,
        "signature": program.signature,
        "modules": [],
        "benefits": [],
    }

    modules = Module.query.filter(Module.programme_id == program.id).all()

    benefits = ProgramBenefit.query.filter_by(program_id=program_id).all()
    benefits = convert_model_to_dict(benefits)
    program_data["benefits"] = benefits

    for module in modules:
        module_data = {
            "id": module.id,
            "name": module.name,
            "description": module.description,
            "start_date": module.start_date.isoformat() if module.start_date else None,
            "end_date": module.end_date.isoformat() if module.end_date else None,
            "sessions": [],
        }

        sessions = Module_Session.query.filter(
            Module_Session.module_id == module.id
        ).all()

        for session in sessions:
            session_data = {
                "id": session.id,
                "session_date": session.session_date.isoformat(),
                "meeting_id": session.meeting_id,
                "completed": session.completed,
            }
            module_data["sessions"].append(session_data)

        program_data["modules"].append(module_data)
    return program_data


def get_programmes_by_instructor(instructor_id):
    current_date = date.today()
    programmes = Programme.query.filter_by(instructor_id=instructor_id).all()
    print(programmes)
    print(programmes[0].start_date, type(programmes[0].start_date), current_date)
    ongoing_programmes = [
        get_program_details(programme.id)
        for programme in programmes
        if programme.end_date >= current_date
    ]
    done_programmes = [
        get_program_details(programme.id)
        for programme in programmes
        if programme.end_date < current_date
    ]
    return ongoing_programmes, done_programmes
