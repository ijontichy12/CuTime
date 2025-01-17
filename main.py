from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

# Use environment variables for database connection (assuming DATABASE_URL exists)
DATABASE_URL = os.environ.get("DATABASE_URL")

# Fix the SQLAlchemy postgres vs postgresql issue
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    print("Modified DATABASE_URL:", DATABASE_URL)

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
print("Final SQLALCHEMY_DATABASE_URI:", app.config['SQLALCHEMY_DATABASE_URI'])

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    __tablename__ = 'users'  
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    team = db.relationship('Team', backref='manager', uselist=False)

    def __repr__(self):
        return f'<User {self.username}>'

class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)
    manager_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    employees = db.relationship('Employee', secondary='team_employee', back_populates='teams')

class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    teams = db.relationship('Team', secondary='team_employee', back_populates='employees')
    work_times = db.relationship('WorkTime', backref='employee', lazy=True)

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

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Ungültige Anmeldeinformationen')
    return render_template('login.html')

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

    # Group work times by date
    work_times_by_date = {}
    for worktime in work_times:
        date_str = worktime.date.strftime('%d.%m.%Y')
        if date_str not in work_times_by_date:
            work_times_by_date[date_str] = []
        work_times_by_date[date_str].append(worktime)

    return render_template('dashboard.html', employees=employees, work_times_by_date=work_times_by_date)

@app.route('/add_employee', methods=['GET', 'POST'])
@login_required
def add_employee():
    if request.method == 'POST':
        name = request.form['name']
        new_employee = Employee(name=name)
        new_employee.teams.append(current_user.team)
        db.session.add(new_employee)
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('add_employee.html')

@app.route('/add_worktime/<int:employee_id>', methods=['GET', 'POST'])
@login_required
def add_worktime(employee_id):
    employee = Employee.query.join(team_employee, Employee.id == team_employee.c.employee_id).join(Team, team_employee.c.team_id == Team.id).filter(Employee.id == employee_id, Team.manager_id == current_user.id).first_or_404()
    if request.method == 'POST':
        date_str = request.form['date']
        start_time_str = request.form['start_time']
        end_time_str = request.form['end_time']
        status = request.form['status']
        comment = request.form['comment']

        # Convert date string to Python date object
        date = datetime.strptime(date_str, '%Y-%m-%d').date()

        # Convert time strings to Python time objects
        start_time = datetime.strptime(start_time_str, '%H:%M').time() if start_time_str else None
        end_time = datetime.strptime(end_time_str, '%H:%M').time() if end_time_str else None

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
        return redirect(url_for('dashboard'))
    return render_template('add_worktime.html', employee=employee)

@app.route('/edit_worktime/<int:worktime_id>', methods=['GET', 'POST'])
@login_required
def edit_worktime(worktime_id):
    worktime = WorkTime.query.join(Employee, WorkTime.employee_id == Employee.id).join(team_employee, Employee.id == team_employee.c.employee_id).join(Team, team_employee.c.team_id == Team.id).filter(WorkTime.id == worktime_id, Team.manager_id == current_user.id).first_or_404()
    if request.method == 'POST':
        date_str = request.form['date']
        start_time_str = request.form['start_time']
        end_time_str = request.form['end_time']
        status = request.form['status']
        comment = request.form['comment']

        # Convert date string to Python date object
        worktime.date = datetime.strptime(date_str, '%Y-%m-%d').date()

        # Convert time strings to Python time objects
        worktime.start_time = datetime.strptime(start_time_str, '%H:%M').time() if start_time_str else None
        worktime.end_time = datetime.strptime(end_time_str, '%H:%M').time() if end_time_str else None
        worktime.status = status
        worktime.comment = comment

        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('edit_worktime.html', worktime=worktime)

@app.route('/delete_worktime/<int:worktime_id>', methods=['POST'])
@login_required
def delete_worktime(worktime_id):
    worktime = WorkTime.query.join(Employee, WorkTime.employee_id == Employee.id).join(team_employee, Employee.id == team_employee.c.employee_id).join(Team, team_employee.c.team_id == Team.id).filter(WorkTime.id == worktime_id, Team.manager_id == current_user.id).first_or_404()
    db.session.delete(worktime)
    db.session.commit()
    return redirect(url_for('dashboard'))


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)
