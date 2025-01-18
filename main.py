from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy import MetaData
import os
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField, DateField, TimeField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError, Optional
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Use environment variables for database connection (assuming DATABASE_URL exists)
DATABASE_URL = os.environ.get("DATABASE_URL")
# Fix the SQLAlchemy postgres vs postgresql issue
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    print("Modified DATABASE_URL:", DATABASE_URL)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
print("Final SQLALCHEMY_DATABASE_URI:", app.config['SQLALCHEMY_DATABASE_URI'])
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'your_secret_key_here'
print("SECRET_KEY:", app.config['SECRET_KEY'])

# Initialize CSRF protection
csrf = CSRFProtect(app)

# Initialize Flask-Limiter
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["5 per minute"]  # Default rate limit for all routes
)

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User model
class User(UserMixin, db.Model):
    __tablename__ = 'users'  
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    team = db.relationship('Team', backref='manager', uselist=False)

    def __repr__(self):
        return f'User({self.username})'

# Team model
class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)
    manager_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    employees = db.relationship('Employee', secondary='team_employee', back_populates='teams')

# Employee model
class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    teams = db.relationship('Team', secondary='team_employee', back_populates='employees')
    work_times = db.relationship('WorkTime', backref='employee', lazy=True)

# WorkTime model
class WorkTime(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, db.ForeignKey('employee.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=True)
    end_time = db.Column(db.Time, nullable=True)
    status = db.Column(db.String(50), nullable=True)
    comment = db.Column(db.String(200), nullable=True)

# Association table for many-to-many relationship between Team and Employee
team_employee = db.Table('team_employee',
    db.Column('team_id', db.Integer, db.ForeignKey('team.id'), primary_key=True),
    db.Column('employee_id', db.Integer, db.ForeignKey('employee.id'), primary_key=True)
)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# WTForms Forms
class LoginForm(FlaskForm):
    username = StringField('Benutzername', validators=[DataRequired(), Length(min=2, max=150)])
    password = PasswordField('Passwort', validators=[DataRequired()])
    submit = SubmitField('Anmelden')

class AddEmployeeForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=150)])
    submit = SubmitField('Mitarbeiter hinzufgen')

class AddWorkTimeForm(FlaskForm):
    date = DateField('Datum', validators=[DataRequired()])
    start_time = TimeField('Startzeit', validators=[Optional()])
    end_time = TimeField('Endzeit', validators=[Optional()])
    status = SelectField('Status', choices=[('Present', 'Anwesend'), ('Absent', 'Abwesend'), ('Holiday', 'Urlaub'), ('Ill', 'Krank')], validators=[DataRequired()])
    comment = TextAreaField('Kommentar', validators=[Length(max=200)])
    submit = SubmitField('Absenden')

    def validate(self, extra_validators=None):
        rv = super(AddWorkTimeForm, self).validate()
        if self.status.data in ['Present', 'Present']:
            if not self.start_time.data or not self.end_time.data:
                self.start_time.errors.append('Start- und Endzeit sind erforderlich.')
                self.end_time.errors.append('Start- und Endzeit sind erforderlich.')
                rv = False
        return rv

class EditWorkTimeForm(AddWorkTimeForm):
    submit = SubmitField('Speichern')

# Initialize database
def init_db():
    print("Starting database initialization...")
    try:
        with app.app_context():
            # Get list of existing tables
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            print(f"Existing tables: {existing_tables}")
            print("Creating all database tables...")
            db.create_all()
            # Check tables again
            inspector = db.inspect(db.engine)
            tables_after = inspector.get_table_names()
            print(f"Tables after creation: {tables_after}")
            print("Checking for existing admin user...")
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                print("Creating admin user...")
                test_user = User(username='admin', 
                                 password=generate_password_hash('admin', method='pbkdf2:sha256'))
                db.session.add(test_user)
                # Check if team1 already exists
                team1 = Team.query.filter_by(name='team1').first()
                if not team1:
                    team1 = Team(name='team1', manager=test_user)
                    db.session.add(team1)
                print("Creating admin2 user...")
                test_user2 = User(username='admin2', 
                                  password=generate_password_hash('admin', method='pbkdf2:sha256'))
                db.session.add(test_user2)
                # Check if team2 already exists
                team2 = Team.query.filter_by(name='team2').first()
                if not team2:
                    team2 = Team(name='team2', manager=test_user2)
                    db.session.add(team2)
                print("Committing changes to database...")
                db.session.commit()
                print("Database initialized successfully!")
    except Exception as e:
        print(f"Error initializing database: {e}")
        print(f"Error type: {type(e)}")
        db.session.rollback()
        raise e

def drop_all_tables():
    print("Dropping all tables...")
    try:
        with app.app_context():
            # Reflect the current state of the database into a new metadata object
            meta = MetaData()
            meta.reflect(bind=db.engine)
            
            # Log the tables before dropping
            print("Tables before dropping:", meta.tables.keys())
            
            # Drop all tables using the reflected metadata
            db.drop_all()
            
            # Verify that tables have been dropped
            inspector = db.inspect(db.engine)
            remaining_tables = inspector.get_table_names()
            print("Remaining tables after dropping:", remaining_tables)
            
            if not remaining_tables:
                print("All tables dropped successfully.")
            else:
                print("Some tables were not dropped:", remaining_tables)
    except Exception as e:
        print(f"Error dropping tables: {e}")
        db.session.rollback()
        raise e

def parse_time(time_str):
    if time_str:
        try:
            return datetime.strptime(time_str, '%H:%M:%S').time()
        except ValueError:
            return datetime.strptime(time_str, '%H:%M').time()
    return None

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")  # Apply rate limiting to the login route
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Ungltige Anmeldeinformationen')
    return render_template('login.html', form=form)

@app.errorhandler(429)
def ratelimit_handler(e):
    return render_template('429.html'), 429

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    team = current_user.team
    employees = Employee.query.join(team_employee, Employee.id == team_employee.c.employee_id).join(Team, team_employee.c.team_id == Team.id).filter(Team.manager_id == current_user.id).all()
    work_times = []
    for employee in employees:
        work_times.extend(WorkTime.query.filter_by(employee_id=employee.id).all())
    
    # Group work times by date and sort by date
    work_times_by_date = {}
    for worktime in work_times:
        date_str = worktime.date.strftime('%d.%m.%Y')
        if date_str not in work_times_by_date:
            work_times_by_date[date_str] = []
        work_times_by_date[date_str].append(worktime)
    
    # Sort the dictionary by date (ascending order)
    work_times_by_date = dict(sorted(work_times_by_date.items(), key=lambda item: datetime.strptime(item[0], '%d.%m.%Y')))
    
    return render_template('dashboard.html', employees=employees, work_times_by_date=work_times_by_date)

@app.route('/add_employee', methods=['GET', 'POST'])
@login_required
def add_employee():
    form = AddEmployeeForm()
    if form.validate_on_submit():
        name = form.name.data
        new_employee = Employee(name=name)
        new_employee.teams.append(current_user.team)
        db.session.add(new_employee)
        db.session.commit()
        flash('Mitarbeiter erfolgreich hinzugefgt')
        return redirect(url_for('dashboard'))
    return render_template('add_employee.html', form=form)

@app.route('/add_worktime/<int:employee_id>', methods=['GET', 'POST'])
@login_required
def add_worktime(employee_id):
    employee = Employee.query.join(team_employee, Employee.id == team_employee.c.employee_id).join(Team, team_employee.c.team_id == Team.id).filter(Employee.id == employee_id, Team.manager_id == current_user.id).first_or_404()
    form = AddWorkTimeForm()
    if form.validate_on_submit():
        date = form.date.data
        start_time = form.start_time.data
        end_time = form.end_time.data
        status = form.status.data
        comment = form.comment.data
        new_worktime = WorkTime(
            employee_id=employee.id,
            date=date,
            start_time=start_time,
            end_time=end_time,
            status=status,
            comment=comment
        )
        db.session.add(new_worktime)
        db.session.commit()
        flash('Arbeitszeit erfolgreich hinzugefgt')
        return redirect(url_for('dashboard'))
    return render_template('add_worktime.html', form=form, employee=employee)

@app.route('/edit_worktime/<int:worktime_id>', methods=['GET', 'POST'])
@login_required
def edit_worktime(worktime_id):
    worktime = WorkTime.query.join(Employee, WorkTime.employee_id == Employee.id).join(team_employee, Employee.id == team_employee.c.employee_id).join(Team, team_employee.c.team_id == Team.id).filter(WorkTime.id == worktime_id, Team.manager_id == current_user.id).first_or_404()
    form = EditWorkTimeForm(obj=worktime)
    if form.validate_on_submit():
        worktime.date = form.date.data
        worktime.start_time = form.start_time.data
        worktime.end_time = form.end_time.data
        worktime.status = form.status.data
        worktime.comment = form.comment.data
        db.session.commit()
        flash('Arbeitszeit erfolgreich bearbeitet')
        return redirect(url_for('dashboard'))
    return render_template('edit_worktime.html', form=form, worktime=worktime)

@app.route('/delete_worktime/<int:worktime_id>', methods=['POST'])
@login_required
def delete_worktime(worktime_id):
    worktime = WorkTime.query.join(Employee, WorkTime.employee_id == Employee.id).join(team_employee, Employee.id == team_employee.c.employee_id).join(Team, team_employee.c.team_id == Team.id).filter(WorkTime.id == worktime_id, Team.manager_id == current_user.id).first_or_404()
    db.session.delete(worktime)
    db.session.commit()
    flash('Arbeitszeit erfolgreich geloscht')
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    # Uncomment the next line only if you want to initialize the database upon startup
    init_db()
   
    # Uncomment the next lines only if you want to drop tables for testing purposes
    # with app.app_context():
    #     drop_all_tables()
    
    app.run(host='0.0.0.0', port=5000, debug=True)
else:
    # Call init_db() when running in a production environment (e.g., with gunicorn)
    with app.app_context():
        init_db()
