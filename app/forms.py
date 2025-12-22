from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectField, FloatField, IntegerField, SelectMultipleField, DateField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError, Optional
from app.models import User


class LoginForm(FlaskForm):
    """User login form"""
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class CreateUserForm(FlaskForm):
    """Admin form to create new user"""
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=3, max=50, message='Username must be between 3 and 50 characters')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=6, message='Password must be at least 6 characters')
    ])
    password2 = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    profile_picture = FileField('Profile Picture', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')
    ])
    is_admin = BooleanField('Administrator')
    submit = SubmitField('Create User')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Username already exists. Please choose a different one.')


class EditUserForm(FlaskForm):
    """Admin form to edit existing user"""
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=3, max=50, message='Username must be between 3 and 50 characters')
    ])
    password = PasswordField('New Password (leave blank to keep current)', validators=[
        Length(min=6, message='Password must be at least 6 characters')
    ])
    password2 = PasswordField('Confirm New Password', validators=[
        EqualTo('password', message='Passwords must match')
    ])
    profile_picture = FileField('Profile Picture', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')
    ])
    is_admin = BooleanField('Administrator')
    is_active = BooleanField('Active')
    submit = SubmitField('Update User')
    
    def __init__(self, original_user, *args, **kwargs):
        super(EditUserForm, self).__init__(*args, **kwargs)
        self.original_user = original_user
    
    def validate_username(self, username):
        if username.data != self.original_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user is not None:
                raise ValidationError('Username already exists. Please choose a different one.')


# ============================================================================
# PHASE 2: Exercise & Gym Management Forms
# ============================================================================

class MasterExerciseForm(FlaskForm):
    """Form for creating/editing exercises"""
    name = StringField('Exercise Name', validators=[
        DataRequired(),
        Length(max=50, message='Exercise name must be 50 characters or less')
    ])
    description = TextAreaField('Description', validators=[Optional()])
    video_url = StringField('Video URL', validators=[
        Optional(),
        Length(max=255, message='Video URL must be 255 characters or less')
    ], render_kw={"placeholder": "YouTube or instructional video URL"})
    
    # Category - Fixed dropdown
    category = SelectField('Category', choices=[
        ('', 'Select Category'),
        ('Strength', 'Strength'),
        ('Cardio', 'Cardio'),
        ('Stretch', 'Stretch'),
        ('Resistance', 'Resistance'),
        ('Bodyweight', 'Bodyweight')
    ], validators=[DataRequired()])
    
    primary_muscle = SelectField('Primary Muscle', 
                                 choices=[('', 'Select...'), ('Chest', 'Chest'), ('Back', 'Back'), 
                                         ('Shoulders', 'Shoulders'), ('Arms', 'Arms'), ('Legs', 'Legs'),
                                         ('Core', 'Core'), ('Full Body', 'Full Body'), ('Cardio', 'Cardio')],
                                 validators=[Optional()])
    secondary_muscles = StringField('Secondary Muscles', validators=[Optional()],
                                   render_kw={"placeholder": "e.g., Triceps, Front Delts"})
    difficulty_level = SelectField('Difficulty Level', 
                                   choices=[('', 'Not specified'), ('beginner', 'Beginner'), 
                                           ('intermediate', 'Intermediate'), ('advanced', 'Advanced')],
                                   validators=[Optional()])
    submit = SubmitField('Save Exercise')


class UserGymForm(FlaskForm):
    """Form for creating/editing user gyms"""
    name = StringField('Gym Name', validators=[
        DataRequired(),
        Length(max=50, message='Gym name must be 50 characters or less')
    ])
    address = StringField('Address (optional)', validators=[
        Optional(),
        Length(max=255, message='Address must be 255 characters or less')
    ])
    picture = FileField('Upload Picture (optional)', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')
    ])
    is_shared = BooleanField('Share with other users')
    submit = SubmitField('Save Gym')


class MasterEquipmentForm(FlaskForm):
    """Form for creating/editing master equipment"""
    name = StringField('Equipment Name', validators=[
        DataRequired(),
        Length(max=50, message='Equipment name must be 50 characters or less')
    ])
    description = TextAreaField('Description', validators=[Optional()])
    manufacturer = StringField('Manufacturer (optional)', validators=[
        Optional(),
        Length(max=100, message='Manufacturer must be 100 characters or less')
    ])
    model = StringField('Model (optional)', validators=[
        Optional(),
        Length(max=100, message='Model must be 100 characters or less')
    ])
    equipment_type = SelectField('Equipment Type',
                                 choices=[
                                     ('Strength', 'Strength'),
                                     ('Cardio', 'Cardio'),
                                     ('Body', 'Body Weight'),
                                     ('Resistance', 'Resistance Bands/Cables')
                                 ],
                                 validators=[DataRequired()])
    # Gyms will be handled via checkboxes in template
    submit = SubmitField('Save Equipment')


class EquipmentVariationForm(FlaskForm):
    """Form for adding variations to equipment"""
    name = StringField('Variation Name', validators=[
        DataRequired(),
        Length(max=50, message='Variation name must be 50 characters or less')
    ], render_kw={"placeholder": "e.g., Rack Position, Handle Orientation"})
    options = TextAreaField('Options (one per line)', validators=[DataRequired()],
                           render_kw={"placeholder": "High\\nMid\\nLow", "rows": 4})
    submit = SubmitField('Add Variation')


class GymEquipmentForm(FlaskForm):
    """Form for assigning equipment to a gym with gym-specific settings"""
    equipment_id = SelectField('Equipment', coerce=int, validators=[DataRequired()])
    quantity = IntegerField('Quantity', validators=[DataRequired()], default=1,
                           render_kw={"placeholder": "How many of this equipment"})
    progression_type = SelectField('Progression Type',
                                   choices=[
                                       ('Plates', 'Plates (barbell with plates)'),
                                       ('Stack', 'Stack (weight stack machine)'),
                                       ('Increments', 'Increments (dumbbells, fixed weights)'),
                                       ('Percentage', 'Percentage-based'),
                                       ('Time', 'Time-based'),
                                       ('Reps', 'Reps-based')
                                   ],
                                   validators=[DataRequired()])
    weight_value = FloatField('Weight Value (lbs)', validators=[Optional()],
                             render_kw={"placeholder": "For fixed weight items"})
    plate_sizes = StringField('Available Plate Sizes (comma-separated)', validators=[Optional()],
                             render_kw={"placeholder": "e.g., 45,35,25,10,5,2.5"})
    stack_increment = FloatField('Stack Increment (lbs)', validators=[Optional()],
                                render_kw={"placeholder": "Weight per plate on stack"})
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Add to Gym')


class GymExerciseForm(FlaskForm):
    """Form for assigning exercises to a gym"""
    exercise_id = SelectField('Exercise', coerce=int, validators=[DataRequired()])
    notes = TextAreaField('Notes', validators=[Optional()])
    is_favorite = BooleanField('Mark as Favorite')
    submit = SubmitField('Add to Gym')


class UserExercisePreferenceForm(FlaskForm):
    """Form for users to rate/prefer exercises"""
    rating = SelectField('Rating', 
                        choices=[('', 'Not Rated'), ('1', '1 - Dislike'), ('2', '2'), 
                                ('3', '3 - Neutral'), ('4', '4'), ('5', '5 - Love It')],
                        coerce=int, validators=[Optional()])
    notes = TextAreaField('Personal Notes', validators=[Optional()])
    submit = SubmitField('Save Preference')


# ============================================================================
# PHASE 3: Program Builder Forms
# ============================================================================

class ProgramForm(FlaskForm):
    """Form for creating/editing programs"""
    name = StringField('Program Name', validators=[
        DataRequired(),
        Length(max=50, message='Program name must be 50 characters or less')
    ])
    description = TextAreaField('Description', validators=[Optional()])
    duration_weeks = IntegerField('Duration (weeks)', validators=[DataRequired()], default=4)
    days_per_week = IntegerField('Days per Week', validators=[DataRequired()], default=7,
                                 render_kw={"placeholder": "7 for full week, or custom"})
    notes = TextAreaField('Notes', validators=[Optional()])
    is_template = BooleanField('Share as Template (Admin only)')
    submit = SubmitField('Save Program')


class ProgramWeekForm(FlaskForm):
    """Form for creating/editing program weeks"""
    week_name = StringField('Week Name (optional)', validators=[
        Optional(),
        Length(max=50, message='Week name must be 50 characters or less')
    ], render_kw={"placeholder": "e.g., Hypertrophy Week, Deload"})
    is_deload = BooleanField('Deload Week')
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Save Week')


class ProgramDayForm(FlaskForm):
    """Form for creating/editing program days"""
    day_name = StringField('Day Name', validators=[
        Optional(),
        Length(max=50, message='Day name must be 50 characters or less')
    ], render_kw={"placeholder": "e.g., Push, Pull, Legs, Upper, Lower"})
    is_rest_day = BooleanField('Rest Day')
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Save Day')


class ProgramExerciseForm(FlaskForm):
    """Form for adding exercises to program days"""
    exercise_id = SelectField('Exercise', coerce=int, validators=[DataRequired()])
    sets = IntegerField('Sets', validators=[DataRequired()], default=3)
    reps = StringField('Reps', validators=[DataRequired()], 
                       render_kw={"placeholder": "e.g., 10, 8-12, AMRAP"})
    lift_time_seconds = IntegerField('Lift Time (seconds)', validators=[Optional()],
                                     render_kw={"placeholder": "Time per rep/set"})
    rest_time_seconds = IntegerField('Rest Time (seconds)', validators=[Optional()], default=90,
                                     render_kw={"placeholder": "Rest between sets"})
    starting_weight = FloatField('Starting Weight (lbs)', validators=[Optional()],
                                render_kw={"placeholder": "Recommended starting weight"})
    target_rpe = FloatField('Target RPE (1-10)', validators=[Optional()])
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Add Exercise')


class ProgramSeriesForm(FlaskForm):
    """Form for adding a series (single or superset) to a program day"""
    series_type = SelectField('Series Type', 
                             choices=[('single', 'Single Exercise'), ('superset', 'Superset (2 exercises)')],
                             validators=[DataRequired()])
    time_seconds = IntegerField('Time Limit (seconds)', validators=[Optional()],
                               render_kw={"placeholder": "Optional time limit for superset"})
    
    # Exercise 1 fields
    exercise1_id = SelectField('Exercise 1', coerce=int, validators=[DataRequired()])
    sets = IntegerField('Sets', validators=[DataRequired()], default=3)
    reps1 = StringField('Reps (Ex 1)', validators=[DataRequired()], 
                       render_kw={"placeholder": "e.g., 10, 8-12, AMRAP"})
    rest1_time_seconds = IntegerField('Rest (Ex 1, seconds)', validators=[Optional()], default=90)
    starting_weights1 = StringField('Starting Weights (Ex 1)', validators=[Optional()],
                                   render_kw={"placeholder": "e.g., 135, 185, 225 (one per set)"})
    target_rpe1 = FloatField('Target RPE (Ex 1)', validators=[Optional()])
    
    # Exercise 2 fields (for superset)
    exercise2_id = SelectField('Exercise 2', coerce=int, validators=[Optional()])
    reps2 = StringField('Reps (Ex 2)', validators=[Optional()],
                       render_kw={"placeholder": "e.g., 10, 8-12, AMRAP"})
    rest2_time_seconds = IntegerField('Rest (Ex 2, seconds)', validators=[Optional()], default=90)
    starting_weights2 = StringField('Starting Weights (Ex 2)', validators=[Optional()],
                                   render_kw={"placeholder": "e.g., 135, 185, 225 (one per set)"})
    target_rpe2 = FloatField('Target RPE (Ex 2)', validators=[Optional()])
    
    notes = TextAreaField('Notes', validators=[Optional()])
    submit = SubmitField('Save Series')


class BodyPatternForm(FlaskForm):
    """Form for creating/editing body patterns"""
    name = StringField('Pattern Name', validators=[
        DataRequired(),
        Length(max=50, message='Pattern name must be 50 characters or less')
    ])
    pattern_days = TextAreaField('Day Labels (one per line)', validators=[DataRequired()],
                                 render_kw={"placeholder": "Push\nPull\nLegs\nRest", "rows": 7})
    submit = SubmitField('Save Pattern')


class ProgramShareForm(FlaskForm):
    """Form for sharing programs with other users"""
    user_id = SelectField('Share with User', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Share Program')


class UserGoalForm(FlaskForm):
    """Form for creating/editing user goals"""
    target_weight = FloatField('Target Weight', validators=[Optional()],
                              render_kw={"placeholder": "e.g., 180"})
    target_body_fat = FloatField('Target Body Fat %', validators=[Optional()],
                                render_kw={"placeholder": "e.g., 15.0"})
    target_date = DateField('Target Date', validators=[Optional()], format='%Y-%m-%d')
    
    # Measurement goals
    target_chest = FloatField('Target Chest', validators=[Optional()])
    target_waist = FloatField('Target Waist', validators=[Optional()])
    target_hips = FloatField('Target Hips', validators=[Optional()])
    target_left_arm = FloatField('Target Left Arm', validators=[Optional()])
    target_right_arm = FloatField('Target Right Arm', validators=[Optional()])
    target_left_thigh = FloatField('Target Left Thigh', validators=[Optional()])
    target_right_thigh = FloatField('Target Right Thigh', validators=[Optional()])
    target_left_calf = FloatField('Target Left Calf', validators=[Optional()])
    target_right_calf = FloatField('Target Right Calf', validators=[Optional()])
    
    notes = TextAreaField('Notes', validators=[Optional()],
                         render_kw={"placeholder": "Your fitness goals and motivation..."})
    submit = SubmitField('Save Goals')


class BodyMetricForm(FlaskForm):
    """Form for logging body metrics"""
    weight = FloatField('Weight', validators=[Optional()],
                       render_kw={"placeholder": "e.g., 180.5"})
    body_fat = FloatField('Body Fat %', validators=[Optional()],
                         render_kw={"placeholder": "e.g., 15.2"})
    
    # Measurements
    chest = FloatField('Chest', validators=[Optional()])
    waist = FloatField('Waist', validators=[Optional()])
    hips = FloatField('Hips', validators=[Optional()])
    left_arm = FloatField('Left Arm', validators=[Optional()])
    right_arm = FloatField('Right Arm', validators=[Optional()])
    left_thigh = FloatField('Left Thigh', validators=[Optional()])
    right_thigh = FloatField('Right Thigh', validators=[Optional()])
    left_calf = FloatField('Left Calf', validators=[Optional()])
    right_calf = FloatField('Right Calf', validators=[Optional()])
    
    notes = TextAreaField('Notes', validators=[Optional()],
                         render_kw={"placeholder": "How you're feeling, diet changes, etc."})
    submit = SubmitField('Log Metrics')


class UserProfileForm(FlaskForm):
    """Form for editing user profile"""
    profile_picture = FileField('Profile Picture', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')
    ])
    weight_unit = SelectField('Weight Unit', choices=[
        ('lbs', 'Pounds (lbs)'),
        ('kg', 'Kilograms (kg)')
    ], validators=[DataRequired()])
    submit = SubmitField('Save Profile')
