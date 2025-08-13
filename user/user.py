import os , uuid
from flask import Flask, redirect, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_security import Security, SQLAlchemyUserDatastore, auth_required, roles_required, current_user
from flask_security.utils import hash_password
from flask import request, jsonify, render_template
from models.models import db, User, Role, ParkingLots, ParkingSpot, ReservedSpots
from sqlalchemy.exc import SQLAlchemyError
from forms.forms import ParkingLotForm , ExtendedForm, DeleteForm , ReleaseSpotForm , BookSpotFrom, ViewSpotForm, LotSearchForm
from datetime import datetime 
from pytz import timezone, UTC
from flask import Blueprint
import re 
from decimal import Decimal
from sqlalchemy import func

ist = timezone('Asia/Kolkata')
user_bp = Blueprint('user', __name__, url_prefix='/user' , template_folder = 'templates/user'  )

numberplte_pat = r'^(?:[A-Z]{2}\d{2}[A-Z]{1,2}\d{1,4}|\d{2}BH\d{4}[A-Z]{2})$'


@user_bp.route('/spot/release<int:rev_id>' , methods = ['GET' , 'POST'])  
@auth_required()
def spot_release(rev_id):
    reservation = ReservedSpots.query.get_or_404(rev_id)    

    form = ReleaseSpotForm(obj = reservation)
    form.leaving_time.data = datetime.now(UTC).astimezone(ist)  #convert to ist for display 
    form.parking_time.data =  UTC.localize(reservation.parking_time).astimezone(ist)
    form.spot_no.data = reservation.spot.spot_no    # not available in reservation table

    elapsed_time =  form.leaving_time.data - form.parking_time.data
    form.total_cost.data = (Decimal(elapsed_time.total_seconds()) /  Decimal(3600)) * reservation.rate_at_booking


    if form.validate_on_submit():
        reservation.leaving_time = datetime.now(UTC)
        elapsed_seconds = (reservation.leaving_time - UTC.localize(reservation.parking_time)).total_seconds()
        elapsed_hours = Decimal(elapsed_seconds) / Decimal(3600)
        reservation.total_cost = elapsed_hours * reservation.rate_at_booking  # re-caulculated twice to prevent error due to delayed submission
        spot = ParkingSpot.query.get(reservation.spot_id)
        spot.status = 'A'

        try:
            db.session.add(reservation)
            db.session.commit()


        except SQLAlchemyError as e: 
            db.session.rollback()
            print(e)
            flash('Error Spot not released' , 'danger')
            return redirect(url_for('user.spot_release'))

        return redirect(url_for('user.user_dashboard'))

    return render_template('release_spot.html' , form = form , reservation = reservation)



@user_bp.route('/spot/book<int:lot_id>' , methods = ['GET' , 'POST'])
@auth_required()
def book_spot(lot_id):
    lot = ParkingLots.query.get_or_404(lot_id)

    if request.method == 'GET':
        
        available_spots = [spot for spot in lot.spots if spot.status == 'A']
        if available_spots:
            first_spot = sorted(available_spots, key=lambda spot: spot.id)[0]
            first_spot.price = lot.price 
            first_spot.user_id = current_user.id 
            form = BookSpotFrom(obj = first_spot)

        else:
            flash('No available spots choose another Lot', 'danger')
            return redirect(url_for('user.user_dashboard'))

    else:
        form = BookSpotFrom()

        if form.validate_on_submit():
            spot = ParkingSpot.query.filter_by(id=form.id.data.strip(), active=True).first_or_404()

            if spot.status == 'A':
                _vehicle_number = form.vehicle_number.data.strip().upper()

                if not re.match(numberplte_pat, _vehicle_number):
                    flash("Invalid vehicle number format", "danger")
                    return render_template('book_spot.html' , form = form, lot = lot )

                #check for vehicle with same number parked 
                if ReservedSpots.query.filter(func.upper(ReservedSpots.vehicle_number) == _vehicle_number , 
                    ReservedSpots.leaving_time == None).first(): 
                    flash("Vehicle With the Same Number is Already Parked, Enter New Number", "danger")
                    return render_template('book_spot.html' , form = form, lot = lot )


                reserved_spot = ReservedSpots (
                    spot_id = spot.id,
                    user_id = current_user.id,
                    vehicle_number = _vehicle_number,
                    rate_at_booking = lot.price,
                    location_at_booking = lot.address,
                    primename_at_booking = lot.primename,
                    ) 

                try:
                    spot.status = 'O'
                    db.session.add(reserved_spot)
                    db.session.commit()
                    flash('Spot successfully reserved!', 'success')
                    return redirect(url_for('user.user_dashboard'))

                except SQLAlchemyError as e:
                    print(e)
                    db.session.rollback()
                    flash('Spot not Reserved Due to Error', 'danger')

            else:
                flash('Spot not available choose another Spot ', 'danger')
                return redirect(url_for('user.user_dashboard'))

            flash('Spot Scucessfully Booked' , 'success')
            return redirect(url_for('user.user_dashboard'))


    return render_template('book_spot.html' , form = form, lot = lot )



@user_bp.route('/dashboard' , methods = ['GET' , 'POST'])
@auth_required()
def user_dashboard():
    data = {}

    parking_lots = ParkingLots.query.all()

    for lot in parking_lots:
        lot.availability  = sum(1 for spot in lot.spots if spot.status == 'A')


    reservations = ReservedSpots.query.filter_by(user_id = current_user.id).all()

    for reservation in reservations:
        utc_time = UTC.localize(reservation.parking_time)
        reservation.parking_time = utc_time.astimezone(ist)
        reservation.location = reservation.location_at_booking

    return render_template('user_dash.html' ,  user = current_user , reservations = reservations)


@user_bp.route('/api/parking-search', methods = ['POST'])   # put /user when acessing 
@auth_required()
def parking_search():
    data = request.get_json()
    query = data.get('query', '').strip()

    if not query:
        results = ParkingLots.query.all()


    if query.isdigit():
        results = ParkingLots.query.filter(ParkingLots.pincode.ilike(f"%{query}%")).all()
    else:
        results = ParkingLots.query.filter(ParkingLots.address.ilike(f"%{query}%")).all()


    response = []
    for lot in results:
        available_spots = sum(1 for spot in lot.spots if spot.status == 'A' )
        response.append({'id': lot.id,  'address': lot.address,  'pincode': lot.pincode, 'availability':available_spots })


    return jsonify( {"parking_lots" : response } )
