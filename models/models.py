from flask_sqlalchemy import SQLAlchemy
from flask_security import UserMixin, RoleMixin
import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy import func, ForeignKey, CheckConstraint


db = SQLAlchemy()


class Role(db.Model, RoleMixin):
    __tablename__ = 'role'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))
    permissions = db.Column(JSON, default={})  # Store permissions as JSON
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())


class User(db.Model, UserMixin):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(225) , nullable = False )
    address  = db.Column(db.String(225))
    pincode = db.Column(db.String(15))
    password = db.Column(db.String(225), nullable=False)
    active = db.Column(db.Boolean, default=True)
    fs_uniquifier = db.Column(db.String(64), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    roles = db.relationship('Role', secondary='user_roles')
    reservations = db.relationship('ReservedSpots', backref='user', lazy=True)


class UserRoles(db.Model):
    __tablename__ = 'user_roles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))


class ParkingLots(db.Model):
    __tablename__ = 'parking_lots'

    id = db.Column(db.Integer , primary_key = True)
    primename = db.Column(db.String(225) , nullable = False)
    price =  db.Column(db.Numeric(10, 2))
    address = db.Column(db.String(225) , nullable = False)
    pincode = db.Column(db.String(15) , nullable =False)
    maxspots = db.Column(db.Integer , nullable = False)
    spots = db.relationship('ParkingSpot', backref='lot', lazy=True)


class ParkingSpot(db.Model):
    __tablename__ = 'parking_spot'

    id = db.Column(db.Integer , primary_key = True)
    lot_id = db.Column(db.Integer , ForeignKey('parking_lots.id') , index = True)
    spot_no = db.Column(db.Integer , nullable = False)
    status = db.Column(db.String(1), nullable=False)
    reservations = db.relationship('ReservedSpots', backref='spot', lazy=True)

    __table_args__ = (
        CheckConstraint("status IN ('A', 'O')", name="check_status_valid"),
    )


class ReservedSpots(db.Model):
    __tablename__ = 'reserved_spots'

    id = db.Column(db.Integer , primary_key = True)
    spot_id = db.Column(db.Integer , ForeignKey('parking_spot.id') , nullable = True , index = True)
    user_id = db.Column(db.Integer , ForeignKey('user.id') , nullable = True , index = True)
    location_at_booking = db.Column(db.String(225), nullable = False)
    primename_at_booking = db.Column(db.String(225) , nullable = False)
    vehicle_number = db.Column(db.String(15) , nullable = False )
    parking_time = db.Column(db.DateTime(timezone=True) , nullable = False , server_default=func.now())
    leaving_time = db.Column(db.DateTime(timezone=True) )
    rate_at_booking = db.Column(db.Numeric(10,2), nullable=False)
    total_cost = db.Column(db.Numeric(10,2))
