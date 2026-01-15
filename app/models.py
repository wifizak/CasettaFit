from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login_manager


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    profile = db.relationship('UserProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    body_metrics = db.relationship('BodyMetricHistory', backref='user', cascade='all, delete-orphan')
    goal = db.relationship('UserGoal', backref='user', uselist=False, cascade='all, delete-orphan')
    gyms = db.relationship('UserGym', backref='user', foreign_keys='UserGym.user_id', cascade='all, delete-orphan')
    program_instances = db.relationship('ProgramInstance', backref='user', cascade='all, delete-orphan')
    workout_sessions = db.relationship('WorkoutSession', backref='user', cascade='all, delete-orphan')
    scheduled_days = db.relationship('ScheduledDay', backref='user', cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password against hash"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'


class UserProfile(db.Model):
    __tablename__ = 'user_profiles'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    
    # Preferences
    weight_unit = db.Column(db.String(10), default='lbs', nullable=False)
    
    # Profile picture
    profile_picture = db.Column(db.String(255))
    
    # Current body metrics
    current_weight = db.Column(db.Float)
    current_body_fat = db.Column(db.Float)
    
    # Measurements (in inches or cm based on preference)
    chest = db.Column(db.Float)
    waist = db.Column(db.Float)
    hips = db.Column(db.Float)
    left_arm = db.Column(db.Float)
    right_arm = db.Column(db.Float)
    left_thigh = db.Column(db.Float)
    right_thigh = db.Column(db.Float)
    left_calf = db.Column(db.Float)
    right_calf = db.Column(db.Float)
    
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<UserProfile user_id={self.user_id}>'


class BodyMetricHistory(db.Model):
    __tablename__ = 'body_metric_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    weight = db.Column(db.Float)
    body_fat = db.Column(db.Float)
    chest = db.Column(db.Float)
    waist = db.Column(db.Float)
    hips = db.Column(db.Float)
    left_arm = db.Column(db.Float)
    right_arm = db.Column(db.Float)
    left_thigh = db.Column(db.Float)
    right_thigh = db.Column(db.Float)
    left_calf = db.Column(db.Float)
    right_calf = db.Column(db.Float)
    notes = db.Column(db.Text)
    
    # Indexes for query optimization
    __table_args__ = (
        db.Index('idx_user_recorded', 'user_id', 'recorded_at'),
    )
    
    # Relationship handled by User.body_metrics with cascade
    
    def __repr__(self):
        return f'<BodyMetricHistory user_id={self.user_id} date={self.recorded_at}>'


class UserGoal(db.Model):
    __tablename__ = 'user_goals'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    
    # Weight goals
    target_weight = db.Column(db.Float)
    target_body_fat = db.Column(db.Float)
    
    # Target date
    target_date = db.Column(db.Date)
    
    # Measurement goals
    target_chest = db.Column(db.Float)
    target_waist = db.Column(db.Float)
    target_hips = db.Column(db.Float)
    target_left_arm = db.Column(db.Float)
    target_right_arm = db.Column(db.Float)
    target_left_thigh = db.Column(db.Float)
    target_right_thigh = db.Column(db.Float)
    target_left_calf = db.Column(db.Float)
    target_right_calf = db.Column(db.Float)
    
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship handled by User.goal with cascade
    
    def __repr__(self):
        return f'<UserGoal user_id={self.user_id}>'


# ============================================================================
# PHASE 2: Exercise & Gym Management Models
# ============================================================================

class MasterExercise(db.Model):
    __tablename__ = 'master_exercises'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, index=True)
    description = db.Column(db.Text)
    video_url = db.Column(db.String(255))  # YouTube or video URL
    
    # Muscle groupings (simplified)
    primary_muscle = db.Column(db.String(50))  # "Chest", "Back", "Legs", etc.
    secondary_muscles = db.Column(db.String(255))  # JSON array of secondary muscles
    
    # Category: Strength, Cardio, Stretch, Resistance, Bodyweight
    category = db.Column(db.String(20))  # Single category instead of many-to-many
    difficulty_level = db.Column(db.String(20))  # beginner, intermediate, advanced
    
    # Ownership tracking
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Equipment (many-to-many with variation settings)
    equipment = db.relationship('MasterEquipment', secondary='exercise_equipment_mapping', backref='exercises')
    
    # Relationships
    creator = db.relationship('User', backref=db.backref('created_exercises', cascade='all, delete-orphan'), foreign_keys=[created_by])
    
    def __repr__(self):
        return f'<MasterExercise {self.name}>'


class ExerciseEquipmentMapping(db.Model):
    """Many-to-many relationship between exercises and equipment"""
    __tablename__ = 'exercise_equipment_mapping'
    
    id = db.Column(db.Integer, primary_key=True)
    exercise_id = db.Column(db.Integer, db.ForeignKey('master_exercises.id'), nullable=False)
    equipment_id = db.Column(db.Integer, db.ForeignKey('master_equipment.id'), nullable=False)


class ExerciseEquipmentVariation(db.Model):
    """Stores variation settings for specific exercise-equipment combinations"""
    __tablename__ = 'exercise_equipment_variations'
    
    id = db.Column(db.Integer, primary_key=True)
    exercise_id = db.Column(db.Integer, db.ForeignKey('master_exercises.id'), nullable=False)
    equipment_id = db.Column(db.Integer, db.ForeignKey('master_equipment.id'), nullable=False)
    variation_id = db.Column(db.Integer, db.ForeignKey('equipment_variations.id'), nullable=False)
    selected_option = db.Column(db.String(50))  # The chosen variation option
    
    # Relationships
    exercise = db.relationship('MasterExercise', backref='equipment_variations')
    equipment = db.relationship('MasterEquipment')
    variation = db.relationship('EquipmentVariation')
    
    def __repr__(self):
        return f'<ExerciseEquipmentVariation exercise={self.exercise_id} equipment={self.equipment_id}>'


class UserExercisePreference(db.Model):
    """Per-user ratings and preferences for exercises"""
    __tablename__ = 'user_exercise_preferences'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    exercise_id = db.Column(db.Integer, db.ForeignKey('master_exercises.id'), nullable=False)
    rating = db.Column(db.Integer)  # 1-5 star rating (like/dislike)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='exercise_preferences')
    exercise = db.relationship('MasterExercise', backref='user_preferences')
    
    def __repr__(self):
        return f'<UserExercisePreference user_id={self.user_id} exercise_id={self.exercise_id}>'


class UserExerciseTier(db.Model):
    """Per-user tier rankings for exercises (S, A, B, C, D, F)"""
    __tablename__ = 'user_exercise_tiers'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    exercise_id = db.Column(db.Integer, db.ForeignKey('master_exercises.id'), nullable=False)
    tier = db.Column(db.String(1), nullable=False)  # 'S', 'A', 'B', 'C', 'D', 'F'
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint - one tier per user per exercise
    __table_args__ = (
        db.UniqueConstraint('user_id', 'exercise_id', name='unique_user_exercise_tier'),
    )
    
    # Relationships
    user = db.relationship('User', backref='exercise_tiers')
    exercise = db.relationship('MasterExercise', backref='user_tiers')
    
    def __repr__(self):
        return f'<UserExerciseTier user_id={self.user_id} exercise_id={self.exercise_id} tier={self.tier}>'


class UserGym(db.Model):
    __tablename__ = 'user_gyms'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    address = db.Column(db.String(255))  # Optional gym address
    picture_url = db.Column(db.String(255))  # Optional gym picture
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Who created this gym
    is_shared = db.Column(db.Boolean, default=False, nullable=False)  # Can other users access this gym?
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships handled by User.gyms with cascade
    creator = db.relationship('User', backref='created_gyms', foreign_keys=[created_by])
    equipment = db.relationship('GymEquipment', backref='gym', cascade='all, delete-orphan')
    exercises = db.relationship('GymExercise', backref='gym', cascade='all, delete-orphan')
    
    # Computed properties for tracking
    @property
    def user_count(self):
        """Count unique users who have workouts in this gym"""
        # Will be implemented when WorkoutSession model exists
        return 0
    
    @property
    def workout_count(self):
        """Count total workouts completed in this gym"""
        # Will be implemented when WorkoutSession model exists
        return 0
    
    def __repr__(self):
        return f'<UserGym {self.name}>'


class GymMembership(db.Model):
    """Many-to-many relationship between Users and Gyms for gym memberships"""
    __tablename__ = 'gym_memberships'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    gym_id = db.Column(db.Integer, db.ForeignKey('user_gyms.id'), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Unique constraint: a user can only join a gym once
    __table_args__ = (db.UniqueConstraint('user_id', 'gym_id', name='unique_user_gym_membership'),)
    
    # Relationships
    user = db.relationship('User', backref='gym_memberships')
    gym = db.relationship('UserGym', backref='members')
    
    def __repr__(self):
        return f'<GymMembership user_id={self.user_id} gym_id={self.gym_id}>'


# Association table for MasterEquipment and UserGym many-to-many relationship
equipment_gym_association = db.Table('equipment_gym_association',
    db.Column('equipment_id', db.Integer, db.ForeignKey('master_equipment.id'), primary_key=True),
    db.Column('gym_id', db.Integer, db.ForeignKey('user_gyms.id'), primary_key=True),
    db.Column('created_at', db.DateTime, default=datetime.utcnow, nullable=False)
)


class MasterEquipment(db.Model):
    """Global equipment database similar to MasterExercise"""
    __tablename__ = 'master_equipment'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, index=True)
    description = db.Column(db.Text)
    equipment_type = db.Column(db.String(20), nullable=False)  # Strength, Cardio, Body, Resistance
    manufacturer = db.Column(db.String(100))  # Equipment manufacturer
    model = db.Column(db.String(100))  # Equipment model number/name
    
    # Ownership tracking
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    creator = db.relationship('User', backref='created_equipment', foreign_keys=[created_by])
    variations = db.relationship('EquipmentVariation', backref='equipment', cascade='all, delete-orphan')
    gyms = db.relationship('UserGym', secondary=equipment_gym_association, backref='available_equipment')
    
    def __repr__(self):
        return f'<MasterEquipment {self.name}>'


class EquipmentVariation(db.Model):
    """Equipment variations (rack position, handle orientation, etc.)"""
    __tablename__ = 'equipment_variations'
    
    id = db.Column(db.Integer, primary_key=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey('master_equipment.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)  # "Rack Position", "Handle Orientation", etc.
    options = db.Column(db.Text)  # JSON array of possible values
    
    def __repr__(self):
        return f'<EquipmentVariation {self.name}>'


class GymEquipment(db.Model):
    """Equipment assigned to a specific gym with gym-specific settings"""
    __tablename__ = 'gym_equipment'
    
    id = db.Column(db.Integer, primary_key=True)
    gym_id = db.Column(db.Integer, db.ForeignKey('user_gyms.id'), nullable=False)
    equipment_id = db.Column(db.Integer, db.ForeignKey('master_equipment.id'), nullable=False)
    
    # Gym-specific overrides
    quantity = db.Column(db.Integer, default=1, nullable=False)  # How many of this equipment
    
    # Progressive overload configuration for this gym
    progression_type = db.Column(db.String(20), nullable=False)  # Plates, Stack, Increments, Percentage, Time, Reps
    
    # For specific progression types
    weight_value = db.Column(db.Float)  # For fixed weights (dumbbells, kettlebells)
    plate_sizes = db.Column(db.Text)  # JSON array of available plate sizes
    stack_increment = db.Column(db.Float)  # For weight stack machines
    
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    equipment = db.relationship('MasterEquipment', backref='gym_assignments')
    
    def __repr__(self):
        return f'<GymEquipment gym_id={self.gym_id} equipment_id={self.equipment_id}>'


class GymExercise(db.Model):
    """Exercises available in a specific gym (progression moved to equipment level)"""
    __tablename__ = 'gym_exercises'
    
    id = db.Column(db.Integer, primary_key=True)
    gym_id = db.Column(db.Integer, db.ForeignKey('user_gyms.id'), nullable=False)
    exercise_id = db.Column(db.Integer, db.ForeignKey('master_exercises.id'), nullable=False)
    
    # Custom settings per gym exercise
    notes = db.Column(db.Text)
    is_favorite = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    exercise = db.relationship('MasterExercise', backref='gym_assignments')
    
    def __repr__(self):
        return f'<GymExercise gym_id={self.gym_id} exercise_id={self.exercise_id}>'


# ============================================================================
# PHASE 3: Program Builder Models
# ============================================================================

class BodyPattern(db.Model):
    __tablename__ = 'body_patterns'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # NULL = system/shared pattern
    pattern_json = db.Column(db.Text, nullable=False)  # JSON array of day labels e.g., ["Push", "Pull", "Legs", "Rest"]
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = db.relationship('User', backref='body_patterns')
    
    def __repr__(self):
        return f'<BodyPattern {self.name}>'


class Program(db.Model):
    __tablename__ = 'programs'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    
    # Ownership and sharing
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_template = db.Column(db.Boolean, default=False, nullable=False)  # Admin shared template
    is_active = db.Column(db.Boolean, default=False, nullable=False)  # Is this the user's active program?
    
    # Program metadata
    duration_weeks = db.Column(db.Integer)  # Total program length in weeks
    days_per_week = db.Column(db.Integer, default=7)  # How many training days per week (default 7 for full week)
    notes = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    creator = db.relationship('User', backref='created_programs', foreign_keys=[created_by])
    weeks = db.relationship('ProgramWeek', backref='program', cascade='all, delete-orphan', order_by='ProgramWeek.week_number')
    shared_with = db.relationship('ProgramShare', backref='program', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Program {self.name}>'


class ProgramShare(db.Model):
    __tablename__ = 'program_shares'
    
    id = db.Column(db.Integer, primary_key=True)
    program_id = db.Column(db.Integer, db.ForeignKey('programs.id'), nullable=False)
    shared_with_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    can_edit = db.Column(db.Boolean, default=False, nullable=False)  # Always False for now (read-only)
    shared_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = db.relationship('User', backref='shared_programs')
    
    def __repr__(self):
        return f'<ProgramShare program_id={self.program_id} user_id={self.shared_with_user_id}>'


class ProgramWeek(db.Model):
    __tablename__ = 'program_weeks'
    
    id = db.Column(db.Integer, primary_key=True)
    program_id = db.Column(db.Integer, db.ForeignKey('programs.id'), nullable=False)
    week_number = db.Column(db.Integer, nullable=False)  # 1, 2, 3, etc.
    week_name = db.Column(db.String(50))  # Optional: "Hypertrophy Week", "Deload", etc.
    is_deload = db.Column(db.Boolean, default=False, nullable=False)
    notes = db.Column(db.Text)
    
    # Relationships
    days = db.relationship('ProgramDay', backref='week', cascade='all, delete-orphan', order_by='ProgramDay.day_number')
    
    # Indexes for query optimization
    __table_args__ = (
        db.Index('idx_program', 'program_id'),
    )
    
    def __repr__(self):
        return f'<ProgramWeek program_id={self.program_id} week={self.week_number}>'


class ProgramDay(db.Model):
    __tablename__ = 'program_days'
    
    id = db.Column(db.Integer, primary_key=True)
    week_id = db.Column(db.Integer, db.ForeignKey('program_weeks.id'), nullable=False)
    day_number = db.Column(db.Integer, nullable=False)  # 1-7 for days of week
    day_name = db.Column(db.String(50))  # "Push", "Pull", "Legs", "Rest", etc.
    is_rest_day = db.Column(db.Boolean, default=False, nullable=False)
    has_superset = db.Column(db.Boolean, default=False, nullable=False)  # Enable superset column in UI
    notes = db.Column(db.Text)
    
    # Relationships
    series = db.relationship('ProgramSeries', backref='day', cascade='all, delete-orphan', order_by='ProgramSeries.order_index')
    
    # Indexes for query optimization
    __table_args__ = (
        db.Index('idx_week', 'week_id'),
    )
    
    def __repr__(self):
        return f'<ProgramDay week_id={self.week_id} day={self.day_number}>'


class ProgramSeries(db.Model):
    """A series within a program day - can be single exercise or superset"""
    __tablename__ = 'program_series'
    
    id = db.Column(db.Integer, primary_key=True)
    day_id = db.Column(db.Integer, db.ForeignKey('program_days.id'), nullable=False)
    order_index = db.Column(db.Integer, nullable=False, default=0)  # Order within the day
    series_type = db.Column(db.String(20), nullable=False, default='single')  # 'single' or 'superset'
    time_seconds = db.Column(db.Integer)  # For supersets - time to complete the superset
    notes = db.Column(db.Text)
    
    # Relationships
    exercises = db.relationship('ProgramExercise', backref='series', cascade='all, delete-orphan', order_by='ProgramExercise.superset_position')
    
    def __repr__(self):
        return f'<ProgramSeries day_id={self.day_id} type={self.series_type}>'


class ProgramExercise(db.Model):
    __tablename__ = 'program_exercises'
    
    id = db.Column(db.Integer, primary_key=True)
    series_id = db.Column(db.Integer, db.ForeignKey('program_series.id'), nullable=False)
    exercise_id = db.Column(db.Integer, db.ForeignKey('master_exercises.id'), nullable=False)
    superset_position = db.Column(db.Integer, nullable=False, default=1)  # 1 for single/first exercise, 2 for second in superset
    
    # Sets and reps configuration
    sets = db.Column(db.Integer, nullable=False)
    reps = db.Column(db.String(20))  # Can be "10", "8-12", "AMRAP", etc.
    
    # Timing
    lift_time_seconds = db.Column(db.Integer)  # Time per rep/set
    rest_time_seconds = db.Column(db.Integer)  # Rest between sets
    
    # Optional fields
    starting_weights = db.Column(db.Text)  # JSON array of weights per set, e.g., "[135, 185, 225]"
    target_rpe = db.Column(db.Float)  # Target RPE (Rate of Perceived Exertion)
    notes = db.Column(db.Text)
    
    # Relationships
    exercise = db.relationship('MasterExercise', backref='program_assignments')
    
    # Indexes for query optimization
    __table_args__ = (
        db.Index('idx_series', 'series_id'),
    )
    
    def __repr__(self):
        return f'<ProgramExercise series_id={self.series_id} exercise_id={self.exercise_id}>'


# ============================================================================
# Utility Functions
# ============================================================================

def sync_exercise_gym_associations(exercise_id):
    """
    Automatically associate an exercise with gyms that have all required equipment.
    Called when:
    - An exercise is created/updated with equipment
    - Equipment is added to a gym
    """
    exercise = MasterExercise.query.get(exercise_id)
    if not exercise:
        return
    
    # Get all equipment IDs required for this exercise
    required_equipment_ids = set([eq.id for eq in exercise.equipment])
    
    # If no equipment required, associate with all gyms
    if not required_equipment_ids:
        all_gyms = UserGym.query.all()
        for gym in all_gyms:
            existing = GymExercise.query.filter_by(gym_id=gym.id, exercise_id=exercise.id).first()
            if not existing:
                gym_exercise = GymExercise(gym_id=gym.id, exercise_id=exercise.id)
                db.session.add(gym_exercise)
        return
    
    # Find all gyms
    all_gyms = UserGym.query.all()
    
    for gym in all_gyms:
        # Get equipment IDs available at this gym
        gym_equipment_ids = set([eq.id for eq in gym.available_equipment])
        
        # Check if gym has all required equipment
        if required_equipment_ids.issubset(gym_equipment_ids):
            # Gym has all required equipment - ensure association exists
            existing = GymExercise.query.filter_by(gym_id=gym.id, exercise_id=exercise.id).first()
            if not existing:
                gym_exercise = GymExercise(gym_id=gym.id, exercise_id=exercise.id)
                db.session.add(gym_exercise)
        else:
            # Gym doesn't have all required equipment - remove association if it exists
            existing = GymExercise.query.filter_by(gym_id=gym.id, exercise_id=exercise.id).first()
            if existing:
                db.session.delete(existing)


def sync_gym_exercise_associations(gym_id):
    """
    Update exercise associations for a gym based on available equipment.
    Called when equipment is added/removed from a gym.
    """
    gym = UserGym.query.get(gym_id)
    if not gym:
        return
    
    # Get equipment IDs available at this gym
    gym_equipment_ids = set([eq.id for eq in gym.available_equipment])
    
    # Get all exercises
    all_exercises = MasterExercise.query.all()
    
    for exercise in all_exercises:
        # Get equipment required for this exercise
        required_equipment_ids = set([eq.id for eq in exercise.equipment])
        
        # If no equipment required or gym has all required equipment
        if not required_equipment_ids or required_equipment_ids.issubset(gym_equipment_ids):
            # Ensure association exists
            existing = GymExercise.query.filter_by(gym_id=gym.id, exercise_id=exercise.id).first()
            if not existing:
                gym_exercise = GymExercise(gym_id=gym.id, exercise_id=exercise.id)
                db.session.add(gym_exercise)
        else:
            # Gym doesn't have all required equipment - remove association if it exists
            existing = GymExercise.query.filter_by(gym_id=gym.id, exercise_id=exercise.id).first()
            if existing:
                db.session.delete(existing)


class ProgramInstance(db.Model):
    """A specific scheduling of a program - tracks when a program was scheduled"""
    __tablename__ = 'program_instances'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    program_id = db.Column(db.Integer, db.ForeignKey('programs.id'), nullable=False)
    gym_id = db.Column(db.Integer, db.ForeignKey('user_gyms.id', ondelete='SET NULL'), nullable=True)
    scheduled_date = db.Column(db.Date, nullable=False)  # Date the instance was created
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships handled by User.program_instances with cascade
    program = db.relationship('Program', backref='instances')
    gym = db.relationship('UserGym', backref='program_instances')
    scheduled_days = db.relationship('ScheduledDay', backref='instance', cascade='all, delete-orphan')
    custom_weights = db.relationship('InstanceExerciseWeight', backref='instance', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<ProgramInstance {self.program.name} on {self.scheduled_date}>'


class InstanceExerciseWeight(db.Model):
    """User-specific weight overrides for a program instance"""
    __tablename__ = 'instance_exercise_weights'
    
    id = db.Column(db.Integer, primary_key=True)
    instance_id = db.Column(db.Integer, db.ForeignKey('program_instances.id'), nullable=False)
    program_exercise_id = db.Column(db.Integer, db.ForeignKey('program_exercises.id'), nullable=False)
    custom_weights = db.Column(db.Text)  # JSON array of custom weights per set
    notes = db.Column(db.Text)  # User notes for this specific exercise in this instance
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    program_exercise = db.relationship('ProgramExercise', backref='instance_overrides')
    
    def __repr__(self):
        return f'<InstanceExerciseWeight instance={self.instance_id} exercise={self.program_exercise_id}>'


class WorkoutSession(db.Model):
    """Represents an actual workout session - can be tied to a scheduled day or standalone"""
    __tablename__ = 'workout_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    scheduled_day_id = db.Column(db.Integer, db.ForeignKey('scheduled_days.id'), nullable=True)  # Nullable for standalone workouts
    gym_id = db.Column(db.Integer, db.ForeignKey('user_gyms.id', ondelete='SET NULL'), nullable=True)
    started_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    is_completed = db.Column(db.Boolean, default=False, nullable=False)
    duration_seconds = db.Column(db.Integer, default=0, nullable=False)  # Actual workout time in seconds
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships handled by User.workout_sessions with cascade
    scheduled_day = db.relationship('ScheduledDay', backref='workout_sessions')
    gym = db.relationship('UserGym', backref='workout_sessions')
    sets = db.relationship('WorkoutSet', back_populates='workout_session', cascade='all, delete-orphan', lazy='dynamic')
    
    # Indexes
    __table_args__ = (
        db.Index('idx_user_started', 'user_id', 'started_at'),
        db.Index('idx_scheduled_day', 'scheduled_day_id'),
    )
    
    def __repr__(self):
        return f'<WorkoutSession {self.id} user={self.user_id} started={self.started_at}>'


class WorkoutSet(db.Model):
    """Individual set performed during a workout - tracks actual weights/reps"""
    __tablename__ = 'workout_sets'
    
    id = db.Column(db.Integer, primary_key=True)
    workout_session_id = db.Column(db.Integer, db.ForeignKey('workout_sessions.id'), nullable=False)
    exercise_id = db.Column(db.Integer, db.ForeignKey('master_exercises.id'), nullable=False)
    set_number = db.Column(db.Integer, nullable=False)  # 1, 2, 3, etc.
    reps = db.Column(db.Integer, nullable=True)  # Actual reps performed
    weight = db.Column(db.Float, nullable=True)  # Actual weight used
    rpe = db.Column(db.String(1), nullable=True)  # Per-set RPE: '-' (too heavy), '=' (good), '+' (could do more)
    overall_rpe = db.Column(db.String(1), nullable=True)  # Overall exercise completion RPE (required after all sets)
    notes = db.Column(db.Text)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    workout_session = db.relationship('WorkoutSession', back_populates='sets')
    exercise = db.relationship('MasterExercise', backref='workout_sets')
    
    # Indexes for efficient history queries
    __table_args__ = (
        db.Index('idx_session_exercise', 'workout_session_id', 'exercise_id'),
        db.Index('idx_exercise_completed', 'exercise_id', 'completed_at'),
    )
    
    def __repr__(self):
        return f'<WorkoutSet {self.exercise.name if self.exercise else "Unknown"} set={self.set_number} {self.weight}x{self.reps}>'


class ScheduledDay(db.Model):
    """Individual scheduled workout day - can be moved independently"""
    __tablename__ = 'scheduled_days'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    program_id = db.Column(db.Integer, db.ForeignKey('programs.id'), nullable=False)
    program_day_id = db.Column(db.Integer, db.ForeignKey('program_days.id'), nullable=False)
    instance_id = db.Column(db.Integer, db.ForeignKey('program_instances.id'), nullable=True)
    gym_id = db.Column(db.Integer, db.ForeignKey('user_gyms.id', ondelete='SET NULL'), nullable=True)
    calendar_date = db.Column(db.Date, nullable=False)
    is_completed = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships handled by User.scheduled_days with cascade
    program = db.relationship('Program', backref='scheduled_days')
    program_day = db.relationship('ProgramDay', backref='scheduled_instances')
    gym = db.relationship('UserGym', backref='scheduled_workouts')
    
    # Indexes for efficient queries
    __table_args__ = (
        db.Index('idx_user_date', 'user_id', 'calendar_date'),
        db.Index('idx_user_program_date', 'user_id', 'program_id', 'calendar_date'),
    )
    
    def __repr__(self):
        return f'<ScheduledDay {self.program_day.name} on {self.calendar_date}>'


class SkippedExercise(db.Model):
    __tablename__ = 'skipped_exercise'
    
    id = db.Column(db.Integer, primary_key=True)
    workout_session_id = db.Column(db.Integer, db.ForeignKey('workout_sessions.id', ondelete='CASCADE'), nullable=False)
    exercise_id = db.Column(db.Integer, db.ForeignKey('master_exercises.id'), nullable=False)
    reason = db.Column(db.String(200), nullable=True)
    skipped_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    workout_session = db.relationship('WorkoutSession', backref='skipped_exercises')
    exercise = db.relationship('MasterExercise', backref='skipped_in_sessions')
    
    # Composite unique constraint - can't skip same exercise twice in same session
    __table_args__ = (
        db.UniqueConstraint('workout_session_id', 'exercise_id', name='unique_session_exercise_skip'),
    )
    
    def __repr__(self):
        return f'<SkippedExercise session={self.workout_session_id} exercise={self.exercise_id}>'
