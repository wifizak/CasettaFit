#!/usr/bin/env python3
"""Seed initial admin user"""
import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User, UserProfile

def seed_admin():
    app = create_app()
    
    with app.app_context():
        # Check if admin already exists
        admin = User.query.filter_by(username='admin').first()
        
        if admin:
            print('Admin user already exists.')
            return
        
        # Create admin user
        admin = User(
            username='admin',
            is_admin=True,
            is_active=True
        )
        admin.set_password('adminpass')
        
        db.session.add(admin)
        db.session.flush()
        
        # Create admin profile
        profile = UserProfile(user_id=admin.id)
        db.session.add(profile)
        
        db.session.commit()
        
        print('Admin user created successfully!')
        print('Username: admin')
        print('Password: adminpass')
        print('Please change the password after first login.')


if __name__ == '__main__':
    seed_admin()
