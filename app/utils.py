# app/utils.py
from app import db
from app.models import User, Team
from werkzeug.security import generate_password_hash

def init_db():
    print("Starting database initialization...")
    try:
        # Create all tables
        db.create_all()
        
        # Check for existing admin user
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            print("Creating admin user...")
            test_user = User(username='admin', password=generate_password_hash('admin', method='pbkdf2:sha256'))
            db.session.add(test_user)
            
            # Create team1 if it doesn't exist
            team1 = Team.query.filter_by(name='team1').first()
            if not team1:
                team1 = Team(name='team1', manager=test_user)
                db.session.add(team1)
            
            # Create admin2 user
            test_user2 = User(username='admin2', password=generate_password_hash('admin', method='pbkdf2:sha256'))
            db.session.add(test_user2)
            
            # Create team2 if it doesn't exist
            team2 = Team.query.filter_by(name='team2').first()
            if not team2:
                team2 = Team(name='team2', manager=test_user2)
                db.session.add(team2)
            
            db.session.commit()
            print("Database initialized successfully!")
    except Exception as e:
        print(f"Error initializing database: {e}")
        db.session.rollback()
        raise e
