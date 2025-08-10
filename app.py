import os , uuid
from flask import Flask, redirect, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_security import Security, SQLAlchemyUserDatastore, auth_required, roles_required, current_user
from flask_migrate import Migrate
from flask_security.utils import hash_password
from flask import request, jsonify, render_template
from flask_security.forms import LoginForm 
from models.models import db, User, Role, ParkingLots, ParkingSpot, ReservedSpots
from sqlalchemy.exc import SQLAlchemyError
from user.user import user_bp
from admin.admin import admin_bp
from forms.forms import ExtendedForm, EditProfileForm
from collections import Counter
from sqlalchemy import func
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)


app.register_blueprint(user_bp)  
app.register_blueprint(admin_bp)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'fallback_secret')
app.config['SECURITY_PASSWORD_HASH'] = 'argon2'
app.config['SECURITY_PASSWORD_SALT'] = os.getenv('SECURITY_PASSWORD_SALT', 'fallback_salt')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI' , 'sqlite:///users.db')
app.config['SECURITY_REGISTERABLE'] = True
app.config['SECURITY_RECOVERABLE'] = True
app.config['SECURITY_REGISTER_FORM'] = ExtendedForm
app.config['SECURITY_SEND_REGISTER_EMAIL'] = False
app.config['SECURITY_LOGIN_URL'] = '/login'
app.config['SECURITY_LOGOUT_URL'] = '/logout'

debug_mode = os.getenv('FLASK_DEBUG', '1') == '1'


db.init_app(app)

migrate = Migrate(app, db)

user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)  


#create users 
with app.app_context():
    def create_users():
        db.create_all()  #create all tables 

        if not user_datastore.find_role("admin"):
            user_datastore.create_role(
                name="admin", 
                description="Administrator with full access", 
                permissions={"read": True, "write": True, "delete": True}
            )
        
        if not user_datastore.find_role("user"):
            user_datastore.create_role(
                name="user", 
                description="Regular user with limited access", 
                permissions={"read": True}
            )
        
        db.session.commit()
        
        # Create users with hashed passwords
        if not user_datastore.find_user(email="admin@example.com"):
            user_datastore.create_user(
                email="admin@example.com", 
                password= hash_password("password"),
                name = "admin",
                roles=[user_datastore.find_role("admin")],
                address = "admin example address",
                pincode = "400000"
            )
                
        db.session.commit() 
    
    create_users()



@app.route('/')
def home():
    if current_user.is_authenticated:
        if current_user.has_role('admin'):
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('user.user_dashboard'))

    return redirect(url_for('security.login'))


@app.route('/edit-profile' , methods = ['GET' , 'POST'])
@auth_required()
def edit_profile():
    form = EditProfileForm(obj = current_user)


    if form.validate_on_submit():
        new_email = form.email.data.strip()

        if new_email != current_user.email:
            existing_email= User.query.filter_by(email=new_email).first()

            if existing_email:
                flash("Email already in use.", "danger")
                return render_template('edit_profile.html', form=form)

        current_user.email = new_email
        current_user.pincode = form.pincode.data.strip()
        current_user.name =  form.name.data.strip()
        current_user.address = form.address.data.strip()

        try:
            db.session.commit()
            flash("Details Updaed Successfully" , 'success')

            if current_user.has_role('admin'):
                return redirect(url_for('admin.dashboard'))

            else:
                return redirect(url_for('user.user_dashboard'))

        except SQLAlchemyError as e:
            print(e)
            db.session.rollback()
            flash("Error Occured Please Try Again", 'danger')

    return render_template('edit_profile.html' , form = form)


@app.route('/summary', methods = ['GET'])
@auth_required()
def parking_summary():

    if current_user.has_role('admin'):
        spot_revenue = (
        db.session.query(ParkingSpot.id,func.sum(ReservedSpots.rate_at_booking).label('total_revenue')).
        join(ReservedSpots).group_by(ParkingSpot.id).all())

        revenue_labels = [f"Spot {spot_id}" for spot_id, _ in spot_revenue]
        revenue_values = [float(revenue or 0) for _, revenue in spot_revenue]

        lots = ParkingLots.query.all()
        lot_labels = []
        available_counts = []
        occupied_counts = []

        for lot in lots:
            lot_labels.append(lot.primename.split()[0])  # First word of lot name
            spots = lot.spots

            occupied = 0
            available = 0

            for spot in spots:
                active_reservations = ReservedSpots.query.filter_by(spot_id=spot.id, leaving_time= None).count()
                if active_reservations > 0:
                    occupied += 1
                else:
                    available += 1

            available_counts.append(available)
            occupied_counts.append(occupied)

        return render_template("summary.html",revenue_labels=revenue_labels,revenue_values=revenue_values,
                lot_labels=lot_labels,available_counts=available_counts,occupied_counts=occupied_counts,user=current_user)



    else:
        reservations = ReservedSpots.query.filter(ReservedSpots.user_id == current_user.id).all()

        spot_ids = [f"{r.primename_at_booking.split(' ')[0]}" for r in reservations]
        spot_usage = Counter(spot_ids)

        labels = list(spot_usage.keys())
        values = list(spot_usage.values())

        max_value = max(values) if values else 1 

        return render_template('summary.html' ,labels = labels , max_value = max_value  , values = values , user = current_user)


if __name__ == '__main__':
    app.run(debug=debug_mode)