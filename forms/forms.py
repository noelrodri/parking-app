from flask_wtf import FlaskForm
from wtforms import (StringField, IntegerField, DecimalField, SubmitField, TextAreaField , SelectField, SubmitField , DateField , 
DateTimeField, DateTimeField, EmailField)
from wtforms.validators import DataRequired, Length, NumberRange,Regexp , Email
from flask_security.forms import RegisterForm




class ParkingLotForm(FlaskForm):
    primename = StringField('Prime Location Name', validators=[DataRequired(), Length(min=2, max=100)])
    address = TextAreaField('Address', validators=[DataRequired()])
    pincode = StringField('Pin Code', validators=[DataRequired(), Length(min=6, max=6 , message = "Pin can only be six digits")])
    price = DecimalField('Price (per hour)' ,  places=2,rounding=None,
    validators=[DataRequired(message="Price is required"),NumberRange(min=0, max = 999,  message="Price must be a positive number")])
    
    maxspots = IntegerField('Maximum Spots', validators=[DataRequired(), NumberRange(min=1, message ="Enter a minimum of 1 Spot" )])
    submit = SubmitField('Submit')


class ExtendedForm(RegisterForm):
    address = TextAreaField('Address', validators=[DataRequired()])
    pincode = StringField('Pincode', validators=[DataRequired(), Length(min=6, max=6, message='Pincode must be 6 digits')])
    name = StringField('Name', validators=[DataRequired()])


class DeleteForm(FlaskForm):
    spot_no = StringField('Spot Id')
    status = StringField('Status')
    submit = SubmitField('Delete')


class ViewSpotForm(FlaskForm):
    spot_id = StringField('Spot Id')
    user_id = StringField("Customer Id")
    spot_no = StringField('Spot No')
    vehicle_number = StringField('Vechicle Number')
    parking_time = DateTimeField('Time Of Parking', format='%Y-%m-%d %H:%M:%S')
    cost = DecimalField('Est Parking Cost')


class ReleaseSpotForm(FlaskForm):
    spot_no = StringField('Parking Spot No')
    spot_id = StringField("Parking Lot ID")
    vehicle_number = StringField("Vechicle Number")
    parking_time = DateTimeField('Time Of Parking', format='%Y-%m-%d %H:%M:%S')
    leaving_time = DateTimeField('Time of Parking Release', format='%Y-%m-%d %H:%M:%S')
    total_cost = DecimalField('Parking Cost')   
    submit = SubmitField('Release')


class BookSpotFrom(FlaskForm):
    spot_no = StringField("Spot Number")
    id = StringField("Spot ID")
    user_id = StringField("User ID")
    price = DecimalField('Hourly Rate INR')
    vehicle_number = StringField('Vehicle Number',
    validators=[DataRequired(),Regexp(r'^(?:[A-Z]{2}\d{2}[A-Z]{1,2}\d{1,4}|\d{2}BH\d{4}[A-Z]{2})$',
        message='Enter a valid Indian Standard/BH Series Number (MH12AA7842 or 22BH1489AA)')])
    submit = SubmitField('Reserve')   


class LotSearchForm(FlaskForm):
    search_by = SelectField('Search by',
        choices=[('user_id', 'User ID'),('address', 'Address'),('pincode', 'Pincode')],validators=[DataRequired()])

    query = StringField('Search String', validators=[DataRequired()])
    submit = SubmitField('Search')



class EditProfileForm(FlaskForm):
    email = EmailField('Email', validators=[DataRequired(),Email(message="Enter a valid email address.")])
    address = TextAreaField('Address', validators=[DataRequired()])
    pincode = StringField('Pincode', validators=[DataRequired(), Length(min=6, max=6, message='Pincode must be 6 digits')])
    name = StringField('Name', validators=[DataRequired()])
    submit = SubmitField('Update')

