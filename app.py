from flask import Flask, jsonify, render_template, send_file, request
from sqlalchemy import and_, func, asc, desc
import flask_praetorian
from models import *
import datetime
import db_utils
import os
from datetime import datetime
from flask_cors import CORS
import dyte_meeting

# BELOW ARE THE PRODUCTION MODE PAYMENT CREDENTIALS
endpoint_secret = "whsec_9xa8AnUfWnx0fcCK2aYRQeCK4RpqshrX"

app = Flask(__name__, static_folder="/static_files")
app.config["SQLALCHEMY_DATABASE_URI"] = URI_DB
db.init_app(app)
CORS(app)

customer_guard = flask_praetorian.Praetorian()
instructor_guard = flask_praetorian.Praetorian()
app.config["JWT_ACCESS_LIFESPAN"] = {"hours": 24}
app.config["JWT_REFRESH_LIFESPAN"] = {"days": 2}
app.config["SECRET_KEY"] = "SHOONYA_SECRET_KEY"
INSTRUCTOR_PERMISSION = "group_call_host"
CUSTOMER_PERMISSION = "group_call_participant"

customer_guard.init_app(app, Customer)
instructor_guard.init_app(app, Instructor)

with app.app_context():
    db.create_all()
    db.session.commit()
    print("The Database has been created successfully")


# @app.route("/")
# def serve_frontend():
#     return render_template("index.html")


@app.route("/assets/<path:path>")
def server_static(path):
    print("path", path, os.path.join("static_files", "assets", path))
    return send_file(os.path.join("static_files", "assets", path))


# -------------------------- PROPER BACKEND ROUTES BEGIN HERE ----------------------

@app.route("/", methods=["GET"])
def check_status():
    return {
        "status": True,
        "message": "Server is running"
    }, 200

@app.route("/api/check_status", methods=["GET"])
def check_status():
    return {
        "status": True,
        "message": "Server is live"
    }, 200

@app.route("/api/send_resources", methods=["POST"])
def send_resources():
    resources = []
    # Logic to load the resources.
    resources = Resources.query.all()
    resources = db_utils.convert_model_to_dict(resources)
    return {
        "status": True,
        "resources": resources,
        "message": "Resources send successfully",
    }, 200


@app.route("/api/send_standalone_programs", methods=["POST"])
def send_programs():
    all_programs = Programme.query.filter_by(signature=False).all()
    all_programs = db_utils.convert_model_to_dict(all_programs)
    for i in range(len(all_programs)):
        if all_programs[i]["start_date"]:
            all_programs[i]["start_date"] = all_programs[i]["start_date"].strftime(
                "%Y-%m-%d"
            )
        if all_programs[i]["end_date"]:
            all_programs[i]["end_date"] = all_programs[i]["end_date"].strftime(
                "%Y-%m-%d"
            )
        if all_programs[i]["program_time"]:
            all_programs[i]["program_time"] = all_programs[i]["program_time"].strftime(
                "%H:%M:%S"
            )

    print(all_programs, "--------------")
    return {
        "status": True,
        "standalone_programs": all_programs,
        "message": "Programs attached successfully",
    }


@app.route("/api/send_signature_programs", methods=["POST"])
def send_signature_programs():
    extracted_programs = Programme.query.filter_by(signature=True).all()
    extracted_programs = db_utils.convert_model_to_dict(extracted_programs)
    print(extracted_programs)

    # Adding only those programs that have not started yet.
    all_programs = list()
    for prg in extracted_programs:
        if datetime.now().date() < prg["start_date"]:
            all_programs.append(prg)

    for i in range(len(all_programs)):
        if all_programs[i]["start_date"]:
            all_programs[i]["start_date"] = all_programs[i]["start_date"].strftime(
                "%Y-%m-%d"
            )
        else:
            all_programs[i]["start_date"] = None
        if all_programs[i]["end_date"]:
            all_programs[i]["end_date"] = all_programs[i]["end_date"].strftime(
                "%Y-%m-%d"
            )
        else:
            all_programs[i]["end_date"] = None
        if all_programs[i]["program_time"]:
            print(all_programs[i]["program_time"])
            all_programs[i]["program_time"] = all_programs[i]["program_time"].strftime(
                "%H:%M:%S"
            )
        else:
            all_programs[i]["program_time"] = None

        all_programs[i]["benefits"] = list()
        benefits_prg = ProgramBenefit.query.filter_by(
            program_id=all_programs[i]["id"]
        ).all()
        for benefit in benefits_prg:
            dt = {"mainHeading": benefit.heading, "subHeading": benefit.description}
            all_programs[i]["benefits"].append(dt)
        all_programs[i]["original_price"] = 39.99

    # Creating the module and lecture count
    for i in range(len(extracted_programs)):
        programme_id = extracted_programs[i]["id"]
        modules = Module.query.filter_by(programme_id=programme_id).all()
        module_count = len(modules)
        lecture_count = 0
        for mod in modules:
            lectures = Module_Session.query.filter_by(module_id=mod.id).all()
            lecture_count = lecture_count + len(lectures)
        extracted_programs[i]["sections"] = module_count
        extracted_programs[i]["lectures"] = lecture_count

    return {
        "status": True,
        "signature_programs": all_programs,
        "message": "Programs attached successfully",
    }


@app.route("/api/send_filter_standalone_programs", methods=["POST"])
def send_filter_standalone_programs():
    return None


@app.route("/api/add_email", methods=["POST"])
def add_email():
    data = request.json
    try:
        name = data.get("name")
        email = data.get("email")
        purpose = data.get("purpose")
    except Exception as e:
        return {"status": "False", "message": "Email Key not found"}, 400
    # intemail = IntrestedEmail.query.filter_by(email=email, purpose=purpose).first()

    # if intemail is not None:
    #     return {"status": False, "message": "Duplicate email"}
    try:
        new_email = IntrestedEmail2(name=name, email=email, purpose=purpose)
        db.session.add(new_email)
        db.session.commit()
    except Exception as e:
        print(e)
        return {"status": "False", "message": "Database Error"}, 400
    return {"status": True, "message": "Email Added"}, 200


@app.route("/api/get_highlighted_programs", methods=["POST"])
def get_highlighted_programmes():
    programmes = Programme.query.filter(Programme.highlight_priority > 1).all()
    highlighted_programmes = {}
    for programme in programmes:
        if str(programme.highlight_priority) not in highlighted_programmes:
            highlighted_programmes[str(programme.highlight_priority)] = [programme]
        else:
            highlighted_programmes[str(programme.highlight_priority)].append(programme)
    return highlighted_programmes


@app.route("/api/get_programme", methods=["POST"])
def get_single_programme_seperate():
    data = request.json
    programme_id = data.get("programme_id")
    programme = Programme.query.filter_by(id=programme_id).all()
    if len(programme) <= 0:
        return {"status": False, "message": "Programme does not exist", "data": None}
    else:
        return {
            "status": True,
            "data": db_utils.convert_model_to_dict(programme),
            "message": "data sent successfully",
        }


# -------------------------------------------- Routes where login is required -------------------------------------------


@app.route("/api/customer/login", methods=["POST"])
def customer_login():
    data = request.json
    email = data.get("email")
    password = data.get("password")
    customer_id = -1
    customer = Customer.query.filter_by(email=email).first()
    if not customer:
        return {
            "status": False,
            "message": "Wrong email address/Password",
            "customer_id": -1,
        }
    username = customer.username
    customer_data = customer_guard.authenticate(username=username, password=password)
    status_code = 500
    status = False
    token = ""
    if customer_data:
        customer_data.is_active = True
        customer_id = customer_data.id
        status = True
        status_code = 200
        db.session.commit()
        token = customer_guard.encode_jwt_token(customer_data)
    return {"status": status, "customer_id": customer_id, "token": token}, status_code


@app.route("/api/customer/register", methods=["POST"])
def register_customer():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    confirm_password = data.get("confirm_password")
    print(password, confirm_password)
    if password != confirm_password:
        return {"status": False, "customer_id": -1, "message": "Password mismatch"}
    password = db_utils.hash_password(password)
    email = data.get("email")
    first_name = data.get("first_name")
    last_name = data.get("last_name")
    is_active = False
    active_programme = None

    customer_temp = Customer.query.filter_by(email=email).first()
    if customer_temp is not None:
        return {
            "status": False,
            "customer_id": -1,
            "message": "Username Email already exists",
        }
    customer_temp = Customer.query.filter_by(username=username).first()
    if customer_temp is not None:
        return {"status": False, "customer_id": -1, "message": "Email already exists"}
    customer_new = Customer(
        username=username,
        password=password,
        email=email,
        first_name=first_name,
        last_name=last_name,
        is_active=is_active,
        active_programme=active_programme,
    )
    db.session.add(customer_new)
    db.session.commit()
    new_customer = Customer.query.filter_by(username=username).first()
    customer_id = new_customer.id

    return {
        "status": True,
        "customer_id": customer_id,
        "message": "Customer has been successfully Registered.",
    }


@app.route("/api/customer/join_session", methods=["POST"])
@flask_praetorian.auth_required
def customer_join_session():
    # return {
    #     "status": True,
    #     "message": "This is a temp token",
    #     "auth_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJvcmdJZCI6ImIxNzg5ZmQxLTE3YzYtNDFhNi05ZmRkLThmMDE5Y2NiMjJmMiIsIm1lZXRpbmdJZCI6ImJiYjI3ZDdmLWE4MTktNDQ3MC1iMjFlLWIwN2ViOGM2NmQ4MSIsInBhcnRpY2lwYW50SWQiOiJhYWEwOWYwOC1iZDcyLTQ5NWQtOWQ2NC00MGI4YTM2MjkyZTUiLCJwcmVzZXRJZCI6ImI5MTZjMTk1LTYwYzAtNDY2Ni1hOGE3LTU4MjkxYzZjYmI1MiIsImlhdCI6MTcxODE5OTk2NCwiZXhwIjoxNzI2ODM5OTY0fQ.aEgFrysWt0kztGIx4S_AYBb7ACIMQGk8MPlbix3PoagZLZQ77aT3NFuAvI5iGC8SV3lpEs1vvfXWs38HKWb3dm82Df6j4IvAVq4Bn0Wxlgj-KlYXA3Gh9qJyMYWQ6yy9oc5CwLD_jsRTSIHBDtvONGFfuFjy4XuTL7p9pzZp0mg2PfiN_MK5GD5ifOsdZuXvHydeoffrGjFJW430jF6Qbk8al6wyys920fImo4CkTT0_TX5MMSNFGT_ExQwiKKH765ifE1MY0Pb98DdL0F53tTwsaSSmTeCSu7UFItChaDEdEVuHTQINVS_f1PQUmDD6JH4nzFkiZ_-vvTLhS__lrQ",
    # }
    data = request.json
    customer_id = data.get("customer_id")
    programme_id = data.get("programme_id")
    # Checking if the required parameters are present or not
    if customer_id is None:
        return {"status": False, "message": "No customer ID received", "auth_token": ""}
    if programme_id is None:
        return {
            "status": False,
            "message": "No programme ID received",
            "auth_token": "",
        }
    # Checking if the customer is actually enrolled in the program and has made the payment.
    enroll = Enrollments.query.filter_by(
        program_id=programme_id, customer_id=customer_id
    ).first()
    if enroll is None:
        return {
            "status": False,
            "message": "Customer has not enrolled for this program",
            "auth_token": "",
        }
    if not enroll.payment_done:
        return {
            "status": False,
            "message": "Customer has not made payment for this program",
            "auth_token": "",
        }
    # Checking if the customer and programme is actually present in database or not.
    customer = Customer.query.filter_by(id=customer_id).first()
    if customer is None:
        return {"status": False, "message": "Wrong customer ID", "auth_token": ""}
    programme = Programme.query.filter_by(id=programme_id).first()
    if not programme:
        return {"status": False, "message": "Wrong programme ID", "auth_token": ""}

    today = datetime.now().date()
    if programme.end_date < today:
        return {
            "status": False,
            "message": "Programme has already ended",
            "auth_token": "",
        }
    if customer.active_meeting_auth_token is not None:
        return {
            "status": True,
            "message": "Auth token has been sent",
            "auth_token": customer.active_meeting_auth_token,
        }

    # Checking if the instructor has joined the programme session or not.
    instructor = Instructor.query.filter_by(id=programme.instructor_id).first()
    if instructor is None:
        return {
            "status": False,
            "message": "No matching instructor ID found",
            "auth_token": "",
        }
    if instructor.current_session is None:
        print("returning here")
        return {
            "status": False,
            "message": "The Session has not yet started.",
            "auth_token": "",
        }
    # If instructor has joined the session then use the meeting id from instructor and then join that session.
    current_session = Module_Session.query.filter_by(
        id=instructor.current_session
    ).first()
    meeting_id = current_session.meeting_id
    print(meeting_id, "Meeting id is ************************************")

    data = dyte_meeting.add_participant(
        participant_email=customer.email,
        participant_name=customer.first_name,
        meeting_id=meeting_id,
        permission=CUSTOMER_PERMISSION,
    )

    customer.active_meeting_participant_id = data["uuid"]
    customer.active_meeting_auth_token = data["auth_token"]
    customer.current_session = instructor.current_session
    db.session.commit()

    return {
        "status": True,
        "auth_token": data["auth_token"],
        "message": "Auth token has been created successfully",
    }


@app.route("/api/customer/leave_session", methods=["POST"])
@flask_praetorian.auth_required
def customer_leave_session():
    data = request.json
    customer_id = data["customer_id"]
    programme_id = data["programme_id"]
    if customer_id is None:
        return {"status": False, "message": "No customer ID", "auth_token": ""}
    if programme_id is None:
        return {"status": False, "message": "No programme ID", "auth_token": ""}

    customer = Customer.query.filter_by(id=customer_id).first()
    current_session = Module_Session.query.filter_by(
        id=customer.current_session
    ).first()
    meeting_id = current_session.meeting_id
    dyte_meeting.remove_participant(
        participant_uuid=customer.active_meeting_participant_id, meeting_id=meeting_id
    )
    customer.current_session = None
    customer.active_meeting_participant_id = None
    customer.active_meeting_auth_token = None
    db.session.commit()

    return {"status": True, "message": "Customer has left the meeting successfully."}


@app.route("/api/customer/fetch_data/<customer_id>", methods=["GET"])
@flask_praetorian.auth_required
def get_customer_data(customer_id):
    customer_data = Customer.query.filter_by(id=customer_id).first()

    # CHECKING IF THE ACTIVE PROGRAMME HAS ENDED IF IT HAS THEN REMOVE IT THEN COMMMIT TO DB ONLT THEN PERFORM FURTHER ACTIVITY
    if customer_data.active_programme is not None:
        today = datetime.now().date()
        curr_prg = Programme.query.filter_by(id=customer_data.active_programme).first()
        curr_end_date = curr_prg.end_date
        if curr_end_date < today:
            customer_data.active_programme = None
        db.session.commit()
    
    if customer_data.current_session is not None:
        sess = Module_Session.query.filter_by(id=customer_data.current_session).first()
        if sess.completed==False:
            dt = dyte_meeting.remove_participant(participant_uuid=customer_data.active_meeting_participant_id,
                                                 meeting_id=sess.meeting_id)
            customer_data.current_session = None
            customer_data.active_meeting_participant_id = None
            customer_data.active_meeting_auth_token = None
    enrollments = Enrollments.query.filter_by(customer_id=customer_id, payment_done=True).all()
    previous_programs = list()
    current_program = Programme.query.filter_by(
        id=customer_data.active_programme
    ).first()

    current_program_id = -1
    current_activity = ""
    if current_program is not None:
        current_program_id = current_program.id
        current_session = (
            Module_Session.query.join(Module)
            .filter(
                and_(
                    Module.programme_id == current_program_id,
                    Module_Session.session_date >= datetime.now(),
                    Module_Session.completed == False,
                )
            )
            .order_by(asc(Module_Session.session_date))
            .first()
        )
        current_activity = None
        if current_session is not None:
            date = current_session.session_date
            date = date.strftime("%d-%m-%Y")
            current_activity = date  # ATTACH DATE HERE.

    for enrollment in enrollments:
        program_id = enrollment.program_id
        if program_id == customer_data.active_programme:
            continue
        program_data = Programme.query.filter_by(id=program_id).first()
        program_name = program_data.name
        program_status = "Completed"
        activity = "Buy Again"
        data = {
            "program_name": program_name,
            "program_status": program_status,
            "activity": activity,
            "programme_id": program_data.id,
        }
        previous_programs.append(data)
    if current_program is None:
        current_data = {
            "program_name": "",
            "program_status": "",
            "activity": "",
            "programme_id": -1,
        }
    else:
        current_data = {
            "program_name": current_program.name,
            "program_status": "Ongoing",
            "activity": current_activity,
            "programme_id": current_program.id,
        }
    return {
        "status": True,
        "username": customer_data.username,
        "customer_id": customer_id,
        "first_name": customer_data.first_name,
        "last_name": customer_data.last_name,
        "email": customer_data.email,
        "profile_picture_link": "",
        "current_programs": current_data,
        "previous_programs": previous_programs,
    }


@app.route("/api/customer/programme_data", methods=["POST"])
@flask_praetorian.auth_required
def get_programme_data():
    data = request.json
    programme_id = data.get("programme_id")
    customer_id = data.get("customer_id")

    if not customer_id:
        return {"status": False, "message": "Customer ID Required"}

    if not programme_id:
        return {"message": "programme_id is required", "data": {}, "status": False}, 400

    programme = Programme.query.filter_by(id=programme_id).first()

    if not programme:
        return {"data": {}, "status": False, "message": "Programme not found"}, 404

    customer = Customer.query.filter_by(id=customer_id).first()
    if not customer:
        return {"data": {}, "status": False, "message": "Customer not found"}

    enrollment = Enrollments.query.filter_by(
        customer_id=customer_id, program_id=programme_id
    ).first()
    if (enrollment is None) or (enrollment.payment_done == False):
        return {"status": False, "message": "Program enrollment not found", "data": {}}

    current_session = (
        Module_Session.query.join(Module)
        .filter(
            and_(
                Module.programme_id == programme_id,
                Module_Session.session_date >= datetime.now(),
                Module_Session.completed == False,
            )
        )
        .order_by(asc(Module_Session.session_date))
        .first()
    )
    current_session_id = -1
    if current_session is not None:
        current_session_id = current_session.id
    programme_data = {
        "id": programme.id,
        "name": programme.name,
        "instructor_id": programme.instructor_id,
        "issues": programme.issues,
        "description": programme.description,
        "language": programme.language,
        "start_date": programme.start_date.strftime("%Y-%m-%d"),
        "end_date": programme.end_date.strftime("%Y-%m-%d"),
        "published": programme.published,
        "price": programme.price,
        "discount_percent": programme.discount_percent,
        "currency": programme.currency,
        "program_time": programme.program_time.strftime("%H:%M:%S"),
        "highlighted_priority": programme.highlighted_priority,
        "signature": programme.signature,
        "session_duration": programme.session_duration,
        "modules": [],
    }
    programme_modules = (
        Module.query.filter_by(programme_id=programme_id)
        .order_by(asc(Module.start_date))
        .all()
    )
    for module in programme_modules:
        module_data = {
            "id": module.id,
            "name": module.name,
            "programme_id": module.programme_id,
            "description": module.description,
            "start_date": module.start_date.strftime("%Y-%m-%d"),
            "end_date": module.end_date.strftime("%Y-%m-%d"),
            "sessions": [],
        }
        module_sessions = (
            Module_Session.query.filter_by(module_id=module_data.get("id"))
            .order_by(asc(Module_Session.session_date))
            .all()
        )
        for session in module_sessions:
            session_data = {
                "current_session": False,
                "id": session.id,
                "module_id": session.module_id,
                "session_date": session.session_date.strftime("%Y-%m-%d"),
                "lesson_name": session.lesson_name,
                "meeting_id": session.meeting_id,
                "completed": session.completed,
            }
            if session_data["id"] == current_session_id:
                session_data["current_session"] = True
            module_data["sessions"].append(session_data)

        programme_data["modules"].append(module_data)

    print(programme_data)

    return {
        "status": True,
        "message": "Programme data has been fetched",
        "data": programme_data,
    }


@app.route("/api/customer/start_payment", methods=["POST"])
@flask_praetorian.auth_required
def customer_start_payment():
    data = request.json
    customer_id = data.get("customer_id")
    programme_id = data.get("programme_id")

    customer = Customer.query.filter_by(id=customer_id).first()
    programme = Programme.query.filter_by(id=programme_id).first()

    if customer is None:
        return {"status": False, "message": "Customer not found", "payment_url": ""}
    if programme is None:
        return {"status": False, "message": "Programme not found", "payment_url": ""}
    if customer.active_programme is not None:
        return {
            "status": False,
            "payment_url": "",
            "message": "Another program is currently active. Try after completion of that program",
        }

    # Checking if the customer can enroll in the program or not. Based on start date.
    current_date = datetime.now().date()
    programme_start_date = programme.start_date
    if (programme_start_date - current_date).days < 1:
        return {
            "status": False,
            "message": "Programme Enrollment has now closed",
            "payment_url": "",
        }

    # This is only for aarambh program.
    print(
        programme_id,
        "*********************************************************************8",
    )
    if programme_id == "100":
        enroll = Enrollments.query.filter_by(
            customer_id=customer_id, program_id=programme_id
        ).first()
        if not enroll:
            enrollment = Enrollments(
                customer_id=customer_id, program_id=programme_id, payment_done=True
            )
            db.session.add(enrollment)
            db.session.commit()
        enroll = Enrollments.query.filter_by(
            customer_id=customer_id, program_id=programme_id
        ).first()
        enroll.payment_done = True
        customer = Customer.query.filter_by(id=customer_id).first()
        customer.active_programme = 100
        db.session.commit()
        # print("working till here ************************************************")
        return {
            "status": True,
            "payment_link": "aarambh_registration",
            "message": "aarambh_registration",
        }

    en1 = Enrollments.query.filter_by(
        program_id=programme_id, customer_id=customer_id
    ).first()
    if en1 is None:
        enroll = Enrollments(customer_id=customer.id, program_id=programme.id)
        db.session.add(enroll)
        db.session.commit()
    elif (en1 is not None) and (en1.payment_done == True):
        return {"status": False, "message": "Payment done already", "payment_link": ""}

    payment_payload = dict()
    payment_payload["Programme Name"] = programme.name
    payment_payload["programme_id"] = programme.id
    payment_payload["start_date"] = programme.start_date
    payment_payload["price"] = programme.price

    payment_link_frontend = ""

    try:
        print(
            programme.currency.lower(),
            "This is the currency",
            "This is the unit amount",
            programme.price * 100,
        )
        print("HERE !!!")
        print(programme.name)
        print(programme.description)
    except Exception as e:
        print(e)
        return {
            "status": False,
            "message": "Payment Error",
            "payment_link": payment_link_frontend,
        }
    return {
        "status": True,
        "message": "Payment link Generated",
        "payment_link": payment_link_frontend,
    }

@app.route("/api/instructor/login", methods=["POST"])
def instructor_login():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    instructor_data = instructor_guard.authenticate(
        username=username, password=password
    )
    print(instructor_data, username, password)
    if instructor_data:
        status = True
        token = instructor_guard.encode_jwt_token(instructor_data)
        instructor_id = instructor_data.id
    else:
        status = False
        token = ""
        instructor_id = -1

    return {"status": status, "token": token, "instructor_id": instructor_id}


@app.route("/api/instructor/join_session", methods=["POST"])
@flask_praetorian.auth_required
def param_yoga_instructor_join():
    data = request.json
    instructor_id = data.get("instructor_id")
    programme_id = data.get("programme_id")

    instructor = Instructor.query.filter_by(id=instructor_id).first()
    programme = Programme.query.filter_by(id=programme_id).first()

    if instructor is None:
        return {"status": False, "auth_token": "", "message": "Instructor ID is wrong"}
    if programme is None:
        return {"status": False, "auth_token": "", "message": "Instructor ID is wrong"}
    today = datetime.today()
    module_session_current = (
        Module_Session.query.join(Module)
        .join(Programme)
        .filter(
            and_(
                Programme.id == programme_id,
                Module_Session.completed == False,
                func.date(Module_Session.session_date) >= today,
            )
        )
        .order_by(asc(Module_Session.session_date))
        .first()
    )

    module = Module.query.filter_by(id=module_session_current.module_id).first()
    instructor_email = instructor.email
    if module_session_current.meeting_id is None:
        meeting_data = dyte_meeting.create_meeting_dyte(title=module.name)
        if meeting_data.get("status") == False:
            return {
                "status": False,
                "auth_token": "",
                "message": "Error in creating meeting",
            }
        module_session_current.meeting_id = meeting_data.get("meeting_id")
        db.session.commit()
    meeting_detail = dyte_meeting.add_participant(
        participant_email=instructor_email,
        participant_name=instructor.first_name,
        meeting_id=module_session_current.meeting_id,
        permission=INSTRUCTOR_PERMISSION,
    )
    instructor_auth_token = meeting_detail.get("auth_token")
    instructor_uuid = meeting_detail.get("uuid")
    if (instructor_uuid is None) or (instructor_auth_token is None):
        return {
            "status": False,
            "message": "Could not add to meeting, try again",
            "auth_token": "",
        }
    instructor.current_session = module_session_current.id
    instructor.active_meeting_participant_id = instructor_uuid
    instructor.active_meeting_auth_token = instructor_auth_token
    db.session.commit()

    return {
        "status": True,
        "auth_token": instructor.active_meeting_auth_token,
        "message": "User added to Meeting",
    }


@app.route("/api/instructor/leave_session", methods=["POST"])
@flask_praetorian.auth_required
def instructor_leave_session():
    data = request.json
    instructor_id = data.get("instructor_id")
    programme_id = data.get("programme_id")
    if instructor_id is None:
        return {"status": False, "message": "Instructor ID is required"}
    if programme_id is None:
        return {"status": False, "message": "Programme ID is required"}
    instructor = Instructor.query.filter_by(id=instructor_id).first()
    if instructor is None:
        return {"status": False, "message": "Instructor ID is wrong"}
    programme = Programme.query.filter_by(id=programme_id).first()
    if programme is None:
        return {"status": False, "message": "Programme ID is wrong"}

    # Removing the instructor from the session.
    current_session = Module_Session.query.filter_by(
        id=instructor.current_session
    ).first()
    meeting_id = current_session.meeting_id
    data = dyte_meeting.remove_participant(
        participant_uuid=instructor.active_meeting_participant_id,
        meeting_id=meeting_id,
    )

    # Removing all participants from the session, removing only if the customers are in the current session.
    enrollments = Enrollments.query.filter_by(program_id=programme_id).all()
    customers = Customer.query.filter_by(active_programme=programme_id).all()
    for customer in customers:
        if customer.current_session is not None:
            part_id = customer.active_meeting_participant_id
            data = dyte_meeting.remove_participant(
                participant_uuid=part_id, meeting_id=meeting_id
            )
            customer.active_meeting_participant_id = None
            customer.active_meeting_auth_token = None
            customer.current_session = None
            db.session.commit()

    # Removing active programmes from all the participants if today was the last session of this programme.
    module_session = (
        Module_Session.query.join(Module)
        .join(Programme)
        .filter(Programme.id == programme_id)
        .order_by(desc(Module_Session.session_date))
        .first()
    )
    today = datetime.today()
    if module_session.session_date == today:
        enrollments = Enrollments.query.filter_by(program_id=programme_id).all()
        for enrollment in enrollments:
            customer_curr = Customer.query.filter_by(id=enrollment.customer_id).first()
            customer_curr.active_programme = None
            db.session.commit()

    # Storing the information.
    current_session = Module_Session.query.filter_by(
        id=instructor.current_session
    ).first()
    current_session.completed = True
    instructor.current_session = None
    instructor.active_meeting_participant_id = None
    instructor.active_meeting_auth_token = None
    db.session.commit()

    return {"status": True, "message": "Instructor has been removed from meeeting"}


# --------------------------------------------
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def catch_all(path):
    if path.startswith("api/") or path.startswith("static/"):
        return jsonify(error="Not Found"), 404
    else:
        return render_template("index.html")



