"""
Test script to measure baseline query counts before optimization
Run this to establish baseline metrics for Phase 1.2
"""
from app import create_app, db
import logging

# Enable SQLAlchemy query logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# Track queries
query_count = 0

def count_queries():
    """Decorator to count queries for a function"""
    import functools
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            global query_count
            
            # Create custom handler to count queries
            query_handler = logging.Handler()
            query_handler.setLevel(logging.INFO)
            
            queries = []
            def handle_log(record):
                if 'SELECT' in record.getMessage() or 'INSERT' in record.getMessage() or 'UPDATE' in record.getMessage():
                    queries.append(record.getMessage())
            
            query_handler.emit = handle_log
            
            logger = logging.getLogger('sqlalchemy.engine')
            logger.addHandler(query_handler)
            
            result = func(*args, **kwargs)
            
            logger.removeHandler(query_handler)
            return result, len(queries)
        
        return wrapper
    return decorator

if __name__ == '__main__':
    app = create_app()
    
    with app.app_context():
        from app.models import User, ScheduledDay
        from datetime import date
        
        # Get a test user
        user = User.query.first()
        if not user:
            print("No users found in database. Please create a user first.")
            exit(1)
        
        print(f"Testing with user: {user.username}")
        print(f"{'='*60}")
        print("Counting queries with SQLAlchemy logging...")
        print(f"{'='*60}\n")
        
        # Manual query counting by enabling logging
        import io
        import sys
        
        # Test each route's query logic
        from datetime import timedelta
        
        print("Dashboard Queries:")
        print("-" * 60)
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        week_end = week_start + timedelta(days=6)
        
        # Query 1: Today's workout
        todays_workout = ScheduledDay.query.filter_by(
            user_id=user.id,
            calendar_date=today
        ).first()
        
        # Query 2: Recent workout
        recent_workout = ScheduledDay.query.filter_by(
            user_id=user.id,
            is_completed=True
        ).order_by(ScheduledDay.calendar_date.desc()).first()
        
        # Query 3: Upcoming workouts
        upcoming_workouts = ScheduledDay.query.filter(
            ScheduledDay.user_id == user.id,
            ScheduledDay.calendar_date > today,
            ScheduledDay.calendar_date <= today + timedelta(days=7)
        ).order_by(ScheduledDay.calendar_date).limit(5).all()
        
        # Query 4: Workouts this week count
        workouts_this_week = ScheduledDay.query.filter(
            ScheduledDay.user_id == user.id,
            ScheduledDay.calendar_date >= week_start,
            ScheduledDay.calendar_date <= week_end,
            ScheduledDay.is_completed == True
        ).count()
        
        # Query 5: Total workouts count
        total_workouts = ScheduledDay.query.filter_by(
            user_id=user.id,
            is_completed=True
        ).count()
        
        # Query 6: Active programs count
        from app.models import ProgramInstance
        active_programs = ProgramInstance.query.filter_by(
            user_id=user.id
        ).count()
        
        print("\nSee SQL queries logged above")
        print(f"{'='*60}")
