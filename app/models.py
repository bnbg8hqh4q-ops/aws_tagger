
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

#Schema creation. By default SQLAlchemy will store this class in db.metadata
class Profile(db.Model):
    __tablename__ = 'profiles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False, unique=True)
    access_key_id = db.Column(db.String(128), nullable=False)
    secret_access_key = db.Column(db.String(256), nullable=False)
    default_region = db.Column(db.String(32), nullable=True)
    is_active = db.Column(db.Boolean, default=False)
