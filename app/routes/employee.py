# app/routes/employee.py
from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app.forms import AddEmployeeForm
from app.models import Employee, Team
from app import db

employee_bp = Blueprint('employee', __name__)

@employee_bp.route('/add_employee', methods=['GET', 'POST'])
@login_required
def add_employee():
    form = AddEmployeeForm()
    if form.validate_on_submit():
        name = form.name.data
        new_employee = Employee(name=name)
        new_employee.teams.append(current_user.team)
        db.session.add(new_employee)
        db.session.commit()
        flash('Mitarbeiter erfolgreich hinzugefügt')
        
        # Ensure the user is authenticated before redirecting
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        
        # Redirect to the dashboard
        return redirect(url_for('dashboard.dashboard'))
    
    return render_template('employee/add_employee.html', form=form)
