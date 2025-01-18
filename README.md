# Employee Work Time Tracker

A Flask-based web application for tracking employee work times. Designed for managers to add employees, log work times, and view summaries.
## Features

**User Authentication:** Secure login and logout functionality.

**Employee Management:** Add and manage employees.

**Work Time Tracking:** Log work times for employees, including start time, end time, status, and comments.

**Dashboard:** View a summary of work times grouped by date and employee.

**Responsive Design:** Built with Tailwind CSS for a responsive and modern UI.

## Technologies Used

**Backend:** Flask (Python)

**Frontend:** HTML, Tailwind CSS

**Database:** PostgreSQL

**Authentication:** Flask-Login

**Deployment:** Render (or your preferred hosting service)

## Setup Instructions

**Prerequisites**

Python 3.x

PostgreSQL

***Pipenv (optional, for virtual environment management)***

## Installation

**Clone the Repository:**

    git clone https://github.com/your-username/employee-work-time-tracker.git
    cd employee-work-time-tracker

**Set Up a Virtual Environment (optional but recommended):**
    
    python -m venv venv
    source venv/bin/activate

**Install Dependencies:**

    pip install -r requirements.txt

**Set Up Environment Variables:**
  
*Create a .env file in the root directory and add the following variables:*

    DATABASE_URL=postgresql://username:password@localhost:5432/employee_db
    SECRET_KEY=your_secret_key_here

**Run the Application:**

    python main.py

*The application will be available at http://localhost:5000.*

## Deployment

**To deploy the application on Render:**

    Create a Render Account: Sign up at Render.

    Create a New Web Service: Connect your GitHub repository and configure the build settings.

    Set Environment Variables: Add DATABASE_URL and SECRET_KEY in the Render dashboard.

    Deploy: Trigger the deployment process.

### Database Schema

**Tables**

Users: *Stores user information (managers).*

    id, username, password, team (relationship with Team table).

Teams: *Stores team information.*

    id, name, manager_id (foreign key to Users table).

Employees: *Stores employee information.*

    id, name, teams (many-to-many relationship with Teams table).

WorkTimes: *Stores work time entries.*

    id, employee_id, date, start_time, end_time, status, comment.

**Relationships**

    A User (manager) can manage one Team.

    A Team can have multiple Employees.

    An Employee can belong to multiple Teams.

    Each Employee can have multiple WorkTime entries.

### Environment Variables

    DATABASE_URL: The connection URL for the PostgreSQL database.

    SECRET_KEY: A secret key for Flask session management.

# Notes

***The application uses Flask-Login for authentication and Tailwind CSS for styling.

***The database is initialized with a default admin user (admin/admin) and two teams (team1, team2).***
