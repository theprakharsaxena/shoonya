import flask_sqlalchemy  # type: ignore
from sqlalchemy.dialects.postgresql import ARRAY  # type: ignore
from sqlalchemy import CheckConstraint  # type: ignore

URI_DB = "postgresql://uaol3lj8vaiq1k:p6a004c6e31838b90af3a8ac07d101b0723f575030a1d79052d8d073ce8a740dc@cf9gid2f6uallg.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com:5432/d380mpjm611fqq"
#URI_DB = "postgres://u5eor41obppssp:pfa51a4e960c76cce6c31b7a614d9b5d641f7fe3df847157e7c6e96b16d05fbd9@c9uss87s9bdb8n.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com:5432/dcan8q4sj8ple7"

db = flask_sqlalchemy.SQLAlchemy()


class IntrestedEmail2(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.Text, nullable=True)
    email = db.Column(db.Text, nullable=True)
    purpose = db.Column(db.Text, nullable=True)


# This is the record Email Class
class IntrestedEmail(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.Text, nullable=True)
    purpose = db.Column(db.Text, nullable=True)


class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.Text, unique=True)
    password = db.Column(db.Text)
    email = db.Column(db.Text, unique=True)
    first_name = db.Column(db.Text)
    last_name = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True, server_default="false")
    active_programme = db.Column(db.Integer, db.ForeignKey("programme.id"))
    active_meeting_participant_id = db.Column(db.Text, nullable=True)
    active_meeting_auth_token = db.Column(db.Text, nullable=True)
    roles = db.Column(db.Text, default="Customer")
    current_session = db.Column(
        db.Integer, db.ForeignKey("module__session.id"), nullable=True
    )
    profile_picture_link = db.Column(db.Text, default="", nullable=False)

    @property
    def rolenames(self):
        try:
            return self.roles.split(",")
        except Exception:
            return []

    @classmethod
    def lookup(cls, username):
        return cls.query.filter_by(username=username).one_or_none()

    @classmethod
    def identify(cls, id):
        return cls.query.get(id)

    @property
    def identity(self):
        return self.id

    def is_valid(self):
        return self.is_active


class Instructor(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.Text, unique=True)
    password = db.Column(db.Text)
    gender = db.Column(db.Text, nullable=False, default="male")
    location = db.Column(db.Text, nullable=False)
    vetting_done = db.Column(db.Boolean, default=False)
    email = db.Column(db.Text, unique=True)
    first_name = db.Column(db.Text)
    last_name = db.Column(db.Text)
    experience_years = db.Column(db.Integer, nullable=False)
    is_active = db.Column(db.Boolean)
    affiliation = db.Column(
        db.Text, default="independent"
    )  # This for the case where the instructor is a part of a institute where
    active_meeting_participant_id = db.Column(db.Text, nullable=True)
    active_meeting_auth_token = db.Column(db.Text, nullable=True)
    current_session = db.Column(
        db.Integer, db.ForeignKey("module__session.id"), nullable=True
    )
    roles = db.Column(db.Text, default="Instructor")

    @property
    def rolenames(self):
        try:
            return self.roles.split(",")
        except Exception:
            return []

    @classmethod
    def lookup(cls, username):
        return cls.query.filter_by(username=username).one_or_none()

    @classmethod
    def identify(cls, id):
        return cls.query.get(id)

    @property
    def identity(self):
        return self.id

    def is_valid(self):
        return self.is_active


# This is the class for Program Content and Data Storage
class Programme(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.Text)
    instructor_id = db.Column(
        db.Integer, db.ForeignKey("instructor.id"), nullable=False
    )
    issues = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    language = db.Column(db.Text, nullable=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    published = db.Column(
        db.Boolean, default=False
    )  # Set this value to True when instructor sets it to publish in forntend
    price = db.Column(db.Float, nullable=False)
    discount_percent = db.Column(db.Float, nullable=False)
    currency = db.Column(db.Text, nullable=False)
    program_time = db.Column(db.Time, nullable=False)
    highlighted_priority = db.Column(db.Integer, nullable=False, default=0)
    signature = db.Column(db.Boolean, default=False)
    session_duration = db.Column(db.Integer, nullable=False)


class ProgramBenefit(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    program_id = db.Column(db.Integer, db.ForeignKey("programme.id"))
    heading = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text, nullable=True)


class Module(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.Text)
    programme_id = db.Column(db.Integer, db.ForeignKey("programme.id"))
    description = db.Column(db.Text)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)


class Module_Session(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    module_id = db.Column(db.Integer, db.ForeignKey("module.id"))
    session_date = db.Column(db.DateTime, nullable=False)
    lesson_name = db.Column(db.Text, nullable=True)
    meeting_id = db.Column(db.Text, nullable=True)
    completed = db.Column(db.Boolean, default=False)


class Programme_Data(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    program_id = db.Column(db.Integer, db.ForeignKey("programme.id"))
    resource_name = db.Column(db.Text, nullable=False)
    bucket_name = db.Column(db.Text, nullable=False)


class Enrollments(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    customer_id = db.Column(db.Integer, db.ForeignKey("customer.id"))
    program_id = db.Column(db.Integer, db.ForeignKey("programme.id"))
    payment_done = db.Column(db.Boolean, nullable=True, default=False)
    instructor_payout_done = db.Column(db.Boolean, nullable=True, default=False)


# This is the class for Resources.
class Resources(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    link = db.Column(db.Text, nullable=False)
    title = db.Column(db.Text, nullable=False)
