from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models import Employee, WorkTime, Team
from datetime import datetime

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    team = current_user.team
    employees = Employee.query.join(Team.employees).filter(Team.manager_id == current_user.id).all()
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
    
    return render_template('dashboard/dashboard.html', employees=employees, work_times_by_date=work_times_by_date)
