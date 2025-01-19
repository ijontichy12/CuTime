# app/routes/worktime.py
from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from app.forms import AddWorkTimeForm, EditWorkTimeForm
from app.models import Employee, WorkTime, Team, team_employee
from app import db

worktime_bp = Blueprint('worktime', __name__)

@worktime_bp.route('/add_worktime/<int:employee_id>', methods=['GET', 'POST'])
@login_required
def add_worktime(employee_id):
    employee = Employee.query.join(team_employee, Employee.id == team_employee.c.employee_id) \
                             .join(Team, team_employee.c.team_id == Team.id) \
                             .filter(Employee.id == employee_id, Team.manager_id == current_user.id) \
                             .first_or_404()
    
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
        flash('Arbeitszeit erfolgreich hinzugefügt')
        return redirect(url_for('dashboard.dashboard'))
    return render_template('worktime/add_worktime.html', form=form, employee=employee)

@worktime_bp.route('/edit_worktime/<int:worktime_id>', methods=['GET', 'POST'])
@login_required
def edit_worktime(worktime_id):
    worktime = WorkTime.query.join(Employee, WorkTime.employee_id == Employee.id) \
                             .join(team_employee, Employee.id == team_employee.c.employee_id) \
                             .join(Team, team_employee.c.team_id == Team.id) \
                             .filter(WorkTime.id == worktime_id, Team.manager_id == current_user.id) \
                             .first_or_404()
    
    form = EditWorkTimeForm(obj=worktime)
    
    if form.validate_on_submit():
        # Update the worktime object with form data
        worktime.date = form.date.data
        worktime.start_time = form.start_time.data
        worktime.end_time = form.end_time.data
        worktime.status = form.status.data
        worktime.comment = form.comment.data
        
        # Commit changes to the database
        db.session.commit()
        flash('Arbeitszeit erfolgreich bearbeitet')
        return redirect(url_for('dashboard.dashboard'))
    
    # Pre-fill the form with the worktime data
    form.date.data = worktime.date
    form.start_time.data = worktime.start_time
    form.end_time.data = worktime.end_time
    form.status.data = worktime.status
    form.comment.data = worktime.comment
    
    return render_template('worktime/edit_worktime.html', form=form, worktime=worktime)

@worktime_bp.route('/delete_worktime/<int:worktime_id>', methods=['POST'])
@login_required
def delete_worktime(worktime_id):
    worktime = WorkTime.query.join(Employee, WorkTime.employee_id == Employee.id) \
                             .join(team_employee, Employee.id == team_employee.c.employee_id) \
                             .join(Team, team_employee.c.team_id == Team.id) \
                             .filter(WorkTime.id == worktime_id, Team.manager_id == current_user.id) \
                             .first_or_404()
    
    db.session.delete(worktime)
    db.session.commit()
    flash('Arbeitszeit erfolgreich gelöscht')
    return redirect(url_for('dashboard.dashboard'))
