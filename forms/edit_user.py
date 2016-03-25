from flask_wtf import Form
from wtforms import StringField, DateTimeField, SelectField
from wtforms.validators import DataRequired, Length

class EditUserForm(Form):
    name = StringField('Name', validators=[DataRequired()])
    phone_number = StringField('Phone number', validators=[Length(min=6)])
    image_link = StringField('Link to profile picture', validators=[Length(min=6)])