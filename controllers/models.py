
from controllers.database import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    passhash = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    is_admin = db.Column(db.Boolean,default=False)
    address = db.Column(db.String(200), nullable=False)
    pincode = db.Column(db.String(10), nullable=False)
class parking_lot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    location_name = db.Column(db.String(100), nullable=False)
    max_slots = db.Column(db.Integer,nullable=False)
    price = db.Column(db.Float,nullable=False)
    address = db.Column(db.String(200),nullable=False)
    pincode = db.Column(db.String(10),nullable=False)


class parking_spot(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    parking_lot_id = db.Column(db.Integer,db.ForeignKey('parking_lot.id'),nullable=False)
    status = db.Column(db.String(20),nullable=False)
    parking_lot = db.relationship('parking_lot')

class reserve_parking_spot(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    parking_spot_id = db.Column(db.Integer, db.ForeignKey('parking_spot.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    
    parking_spot = db.relationship('parking_spot')
    user = db.relationship('User')