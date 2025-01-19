# app/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField, DateField, TimeField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError, Optional

class LoginForm(FlaskForm):
    username = StringField('Benutzername', validators=[DataRequired(), Length(min=2, max=150)])
    password = PasswordField('Passwort', validators=[DataRequired()])
    submit = SubmitField('Anmelden')

class AddEmployeeForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=150)])
    submit = SubmitField('Mitarbeiter hinzufügen')

class AddWorkTimeForm(FlaskForm):
    date = DateField('Datum', validators=[DataRequired()])
    start_time = TimeField('Startzeit', validators=[Optional()])
    end_time = TimeField('Endzeit', validators=[Optional()])
    status = SelectField('Status', choices=[('Present', 'Anwesend'), ('Absent', 'Abwesend'), ('Holiday', 'Urlaub'), ('Ill', 'Krank')], validators=[DataRequired()])
    comment = TextAreaField('Kommentar', validators=[Length(max=200)])
    submit = SubmitField('Absenden')

class EditWorkTimeForm(AddWorkTimeForm):
    submit = SubmitField('Speichern')
