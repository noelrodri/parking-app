import os , uuid
from flask import Flask, redirect, flash, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_security import Security, SQLAlchemyUserDatastore, auth_required, roles_required, current_user
from flask_security.utils import hash_password
from flask import request, jsonify, render_template
from models.models import db, User, Role, ParkingLots, ParkingSpot, ReservedSpots
from wtforms import StringField, TextAreaField , PasswordField 
from wtforms.validators import DataRequired, Email, Length, InputRequired 
from sqlalchemy.exc import SQLAlchemyError
from forms.forms import ParkingLotForm , ExtendedForm, DeleteForm , ReleaseSpotForm , BookSpotFrom, ViewSpotForm, LotSearchForm
from datetime import datetime 
from pytz import timezone, UTC
from flask import Blueprint
from decimal import Decimal
from sqlalchemy import func, case


ist = timezone('Asia/Kolkata')
admin_bp = Blueprint('admin', __name__, url_prefix='/admin' , template_folder='templates/admin'  )



@admin_bp.route('/dashboard' , methods = ['Get' , 'POST'])
@roles_required('admin')
def dashboard():
    lots_query = (
        db.session.query(
            ParkingLots,
            func.count(
                case((ParkingSpot.status == 'O', 1))
            ).label('occupied')
        )
        .join(ParkingSpot, ParkingLots.id == ParkingSpot.lot_id)
        .filter(ParkingLots.active == True)   # only active lots
        .filter(ParkingSpot.active == True)   # only active spots for count
        .group_by(ParkingLots.id)
        .all()
    )




    filtered_spots = {}
    lots = []

    for lot_obj, occupied in lots_query:
        lot_obj.occupied = occupied
        filtered_spots[lot_obj] = [s for s in lot_obj.spots if s.active]
        lots.append(lot_obj)



    return render_template('admin_dash.html' , parking_lots = lots , spots = filtered_spots)



@admin_bp.route('/spot/view<int:spot_id>', methods = ['GET' , 'POST'] )
@roles_required('admin')
def spot_view(spot_id):
    spot = ParkingSpot.query.filter_by(id= spot_id, active=True).first_or_404()
    form  = DeleteForm(obj = spot)


    if form.validate_on_submit():
        if spot.status == 'A':
            try:
                lot = ParkingLots.query.get(spot.lot_id)
                db.session.delete(spot)

                if lot and lot.maxspots > 0:
                    lot.maxspots -= 1

                db.session.commit()
                flash("Spot Deleted", 'success')
                return redirect(url_for('admin.dashboard'))

            except SQLAlchemyError as e:
                db.session.rollback()
                flash("Did not delete Spot", 'danger')
                return render_template ('view_spot.html' , form = form, spot = spot )

        else:
            flash("Cannot Delete Occupied Spot", 'danger')
            return redirect(url_for('admin.dashboard'))

    else:
        return render_template('view_spot.html', form = form , spot = spot )



@admin_bp.route('/spot/details<int:spot_id>' , methods = [ 'GET'])
@roles_required('admin')
def spot_details(spot_id):

    spot = ParkingSpot.query.filter_by(id=spot_id, active=True).first_or_404()
    reservation = ReservedSpots.query.filter_by(spot_id=spot.id).first()

    reservation = (ReservedSpots.query.filter(ReservedSpots.spot_id == spot_id,ReservedSpots.spot.has(active=True))
    .first_or_404())

    now_utc = UTC.localize(datetime.utcnow())

    if reservation.parking_time.tzinfo is None:
        parking_time_utc = UTC.localize(reservation.parking_time)
    else:
        parking_time_utc = reservation.parking_time


    ist_parked = parking_time_utc.astimezone(ist)
    #ist_parked = reservation.parking_time.astimezone(ist)
    now_ist = now_utc.astimezone(ist)
    elapsed_time = now_ist - ist_parked
    cost = (Decimal(elapsed_time.total_seconds()) / Decimal(3600)) * reservation.rate_at_booking
    form = ViewSpotForm(obj=reservation)
    form.parking_time.data = ist_parked  
    form.spot_no.data = spot.spot_no

    form.cost.data = cost                 

    return render_template('spot_details.html', form=form, spot=spot)


@admin_bp.route('/user-list' , methods = [ 'GET'])
@roles_required('admin')
def user_list():
    users = User.query.filter(~User.roles.any(Role.name == 'admin')).all()
    return render_template ('registered_users.html' , users = users )


@admin_bp.route('/parking-lot/delete/<int:lot_id>' , methods = [ 'GET'])
@roles_required('admin')
def lot_delete(lot_id = None):
    
    occupied_spot = ParkingSpot.query.filter_by(lot_id=lot_id, status='O', active=True).first_or_404()
    lot = ParkingLots.query.get(lot_id)

    if occupied_spot:
        flash("Cannot delete lot with occupied spots.", "danger")
        return redirect(url_for('admin.dashboard'))

    try:
        for spot in ParkingSpot.query.filter_by(lot_id = lot_id.id , active = True).all():
            spot.avtive = False 

        lot.active = False 
        db.session.commit()
        flash("Parking lot deleted successfully.", "success")

    except SQLAlchemyError as e:
        print(e)
        db.session.rollback()
        flash("An error occurred while deleting the parking lot.", "danger")

    return redirect(url_for('admin.dashboard'))
    

@admin_bp.route('/lot-search' , methods = ['GET', 'POST'])
@roles_required('admin')
def lot_search():
    form = LotSearchForm()

    data = {}
    lots = []

    if form.validate_on_submit():

        selected_option = form.search_by.data
        query_data = form.query.data.strip()

        if selected_option ==  'user_id':
            lots = db.session.query(ParkingLots).join(ParkingSpot).join(ReservedSpots).filter(ReservedSpots.user_id == query_data)\
            .distinct().all()
            data['header'] = "Parking Lots Used By User-"

        elif selected_option == 'address':
            lots = ParkingLots.query.filter(ParkingLots.address.ilike(f"%{query_data}%")).all()
            data['header'] = "Parking Lot At Following Address-"

        elif selected_option == 'pincode':
            data['header'] = "Parking Lots With Pincode-"
            lots = ParkingLots.query.filter(ParkingLots.pincode == query_data ).all()

        for lot in lots:
            lot.occupied = sum(1 for spot in lot.spots if spot.status == 'O')


    return render_template('admin_search.html' , form = form , lots = lots , data = data )




@admin_bp.route('/parking-lot' , methods = ['POST', 'GET'])
@admin_bp.route('/parking-lot/<int:lot_id>', methods=['GET', 'POST'])
@roles_required('admin')
def edit_lot(lot_id = None):

    if lot_id:
        lot = ParkingSpot.query.filter_by(id= lot_id, active=True).first_or_404()
        _data = {"title":"Edit Parking Lot", "type": "Edit" }

        form = ParkingLotForm(obj = lot)

        if form.validate_on_submit():
            occupied_count = ParkingSpot.query.filter_by(lot_id=lot.id, status='O', active = True).count()
            new_max_spots = form.maxspots.data

            if new_max_spots < occupied_count:
                flash("Cannot set max spots below number of occupied spots.", "danger")
                return render_template('edit_lot.html', form=form, data = _data )


            lot.primename = form.primename.data.strip()
            lot.address = form.address.data.strip()
            lot.pincode = form.pincode.data.strip()
            lot.price = round(form.price.data,2)

            try:
                if new_max_spots < lot.maxspots:
                    excess_spots = (ParkingSpot.query.filter_by(lot_id=lot.id, status='A', active = True) .order_by(ParkingSpot.spot_no.desc())
                    .limit(lot.maxspots - new_max_spots).all())

                    for spot in excess_spots:
                        spot.active = False


                elif new_max_spots > lot.maxspots:  # check for adition
                    last_spot = ParkingSpot.query.filter_by(lot_id=lot_id).order_by(ParkingSpot.spot_no.desc()).first() #all spots required active and deactivated
                    deactivated_spots = ParkingSpot.query.filter_by(lot_id=lot_id , active = False).order_by(ParkingSpot.spot_no.desc()).all()
                    total_spots = ParkingSpot.query.filter_by(lot_id=lot_id , active = True).count()
                    spots_to_add = new_max_spots - total_spots

                    for deac_spot in deactivated_spots:  #consume deactivated spots first
                        if spots_to_add <= 0:
                            break 
                        deac_spot.active = True 
                        spots_to_add -= 1 

                    if spots_to_add > 0:
                        start_no = last_spot.spot_no + 1 if last_spot else 1
                        for spot_no in range(start_no, start_no + spots_to_add):
                            new_spot = ParkingSpot(lot_id=lot_id, spot_no=spot_no, status='A', active=True)
                            db.session.add(new_spot)



                lot.maxspots = new_max_spots
                db.session.commit()
                flash('Parking lot Updated', 'success')
                return redirect(url_for('admin.dashboard'))

            except SQLAlchemyError as e:
                db.session.rollback()
                print(e)
                flash('An error occurred while updating the lot', 'danger')



        return render_template('edit_lot.html' ,form = form , data = _data , lot = lot)

    _data = {"title":"New Parking Lot", "type": "Add" }
    form = ParkingLotForm()
    if form.validate_on_submit():     
        address = form.address.data.strip()

        if ParkingLots.query.filter_by(address= address).first():
            
            flash ("A parking Lot at this addres already exits", "danger")
            return render_template('edit_lot.html' , form = form , data = _data)

        else:
            new_lot = ParkingLots(
                primename = form.primename.data.strip(),
                price = round(form.price.data ,2),
                address = address,
                pincode = form.pincode.data.strip(),
                maxspots = form.maxspots.data
                )

            try:
                db.session.add(new_lot)
                db.session.flush()

                for i in range(1 , new_lot.maxspots+1):
                    spot = ParkingSpot(
                        lot_id = new_lot.id,
                        spot_no = i,
                        status = 'A'
                    ) 
                    db.session.add(spot)

                db.session.commit()
                flash(f"Created new lot and Spots", "success")
                return redirect(url_for('admin.dashboard'))

            except SQLAlchemyError as e:
                db.session.rollback()
                flash(f"Did not create new lot", "danger")
                return render_template("edit_lot.html", form=form , data = _data)

            return redirect(url_for('admin.dashboard'))

    return render_template('edit_lot.html', form = form, data = _data)

