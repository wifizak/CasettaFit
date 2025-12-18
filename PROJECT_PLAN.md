# CasettaFit - Home Gym Weight Lifting Tracking Application
## Project Plan

**Created:** December 18, 2025  
**Status:** Planning Phase

---

## 1. Project Overview

### 1.1 Vision
A comprehensive, mobile-friendly home gym weight lifting tracking application that helps users plan, execute, and analyze their training programs with multi-user support and flexible gym configurations.

### 1.2 Technology Stack
- **Backend:** Python 3.x with Flask
- **WSGI Server:** Gunicorn
- **Reverse Proxy:** NGINX
- **Database:** SQLite
- **Frontend:** CoreUI Free / Bootstrap 5
- **Focus:** Very Mobile Friendly (Responsive Design)

---

## 2. Core Components

### 2.1 Database Architecture

#### Planned Database Tables:
1. **Master Lifts/Activities Database**
   - Universal database of all possible exercises
   - Categories, muscle groups, equipment needed
   
2. **User Gym Equipment Database**
   - User-specific or shared gym configurations
   - Available equipment and exercises
   
3. **Training Programs**
   - Program templates and active programs
   - Days, routines, sets, reps, progression schemes
   
4. **Workout History**
   - Historical tracking of all completed workouts
   - Performance metrics and notes
   
5. **Users & Profiles**
   - Authentication and user management
   - Personal settings and preferences

### 2.2 User Interface Components

1. **Gym Management UI**
   - Add/edit exercises to user's gym
   - Configure equipment availability
   - Define progression types

2. **Program Builder UI**
   - Create and edit training programs
   - Assign exercises from user's gym
   - Configure days, sets, reps, intensity

3. **Workout Execution UI**
   - "At the gym" interface
   - Real-time workout tracking
   - Timer and rest period management

4. **Progress Reporting UI**
   - Per-exercise progress charts
   - Volume and intensity tracking
   - Historical comparisons

5. **Calendar & Scheduling UI**
   - Program scheduling
   - Workout shifting and rescheduling
   - Rest day management

6. **Goals Tracking UI**
   - Personal goal setting
   - Progress toward goals
   - Milestone tracking

### 2.3 Multi-User Features
- Multiple users per installation
- Personal gym configurations
- Shared gym support
- Admin user management interface

---

## 3. Requirements Confirmed

### 3.1 Authentication & Security ✓
- [x] **Email verification:** Not required
- [x] **Password reset:** Admin-only (no user self-service)
- [x] **User roles:** Two roles - Admin and User
- [x] **Social login:** Not needed - username/password only

### 3.2 Data Model Details ✓
- [x] **Exercise categories:** Multiple categories including upper body, lower body, cardio, and more
- [x] **Workout tracking granularity:** Full detail - weight, reps, tempo, rest time, RPE, notes
- [x] **Body metrics:** Yes - weight, body fat %, measurements in user profile
- [x] **Program periodization:** Yes - support different week structures, day structures, and body patterns

### 3.3 Progressive Overload ✓
- [x] **Progression schemes:** User-configurable per lift (weight added, plate count, time, incline, etc.)
- [x] **Weight suggestions:** No auto-suggestions - show previous workout data instead
- [x] **User feedback:** After each lift, user records feeling (doable/heavy/light/good)
- [x] **Deload weeks:** Manual program option, not automatic

### 3.4 Mobile & Offline ✓
- [x] **PWA features:** Not needed
- [x] **Offline capability:** Not needed - always online
- [x] **App type:** Responsive web app only

### 3.5 Deployment ✓
- [x] **Hosting:** Digital Ocean VPS (Ubuntu Server)
- [x] **Docker:** Not required
- [x] **User load:** Small (just a few concurrent users)
- [x] **Development timeline:** Aggressive - substantial work today

### 3.6 Reporting & Analytics ✓
- [x] **Charts required:** Volume over time, progressive overload tracking, 1RM progression
- [x] **Export:** Not needed
- [x] **Workout sharing:** Not needed

---

## 4. Development Phases (All MVP)

### Phase 1: Foundation & Setup
- Flask project structure
- SQLite database setup with migrations
- User authentication system (admin/user roles)
- Admin user management interface
- Base templates with CoreUI/Bootstrap 5
- NGINX + Gunicorn configuration

### Phase 2: Exercise & Gym Management
- Master exercise database (starts empty)
- Exercise CRUD with ownership tracking
- User-configurable exercise categories
- Admin can edit all exercises, users only their own
- User gym configuration (equipment and plate inventory)
- Exercise assignment to user gyms
- Progression type configuration per gym exercise (plates, weight, time, percentage)

### Phase 3: Program Builder
- Program creation and templates
- Program sharing between users
- Program duplication feature
- Admin shared program templates
- Week structure configuration (can vary by week)
- Day structure configuration
- User-defined body patterns (save and reuse)
- Exercise assignment to program days
- Sets, reps, lift time, rest time configuration
- Deload week options

### Phase 4: Workout Execution
- "At the gym" mobile-optimized UI (bottom nav)
- Scheduled workout sessions
- Freestyle/adhoc workout mode
- Missed workout handling (skip/reschedule/move to today)
- Real-time set/rep tracking
- Timer for rest periods
- Performance feedback input (heavy/light/good/doable)
- Previous workout data display
- RPE and notes entry
- Lift time and rest time tracking

### Phase 5: Tracking & History
- Workout history logging
- Historical data viewing per exercise
- Body metrics tracking in profile (weight, body fat %, measurements)
- Personal goals tracking system

### Phase 6: Reporting & Calendar
- Calendar view for scheduled workouts
- Workout shifting and rescheduling
- Volume over time charts
- Progressive overload tracking charts
- 1RM progression charts

### Phase 7: Production Deployment
- Ubuntu server setup on Digital Ocean
- NGINX reverse proxy configuration
- Gunicorn service setup
- Security hardening
- Backup strategy
- Final testing

---

## 5. Detailed Technical Specifications

### 5.1 Database Schema (Draft)

#### Tables Overview:
1. **users** - User accounts, authentication, roles (admin/user)
2. **user_profiles** - Extended user data including body metrics
3. **master_exercises** - Universal exercise database (user-created, ownership tracked)
4. **exercise_categories** - User-configurable category taxonomy
5. **user_gyms** - User or shared gym configurations
6. **gym_equipment** - Available plates and equipment per gym
7. **gym_exercises** - Exercises available in specific gyms
8. **exercise_progression_config** - Progression settings per gym exercise (plate types, numerical, time, percentage)
9. **body_patterns** - User-defined, reusable body pattern templates
10. **programs** - Training program templates and instances (can be shared)
11. **program_weeks** - Week structures within programs (can vary by week)
12. **program_days** - Day structures within weeks
13. **program_exercises** - Exercises assigned to program days with lift time and rest time
14. **workout_sessions** - Individual workout instances (scheduled or freestyle)
15. **workout_sets** - Set-by-set tracking data (weight, reps, tempo, rest, RPE, notes, feeling)
16. **goals** - Personal goal tracking
17. **body_metric_history** - Historical body measurements

### 5.2 Key Features Detail

#### Exercise Progression Types:
- Weight plates (with specific plate sizes tracked per gym)
- Numerical weight (just enter weight value)
- Time-based (duration increase)
- Percentage-based
- Incline/resistance level
- Distance-based
- User-defined custom metrics

#### Performance Feedback Options:
- "Too Heavy" - struggled
- "Heavy" - challenging but doable
- "Good" - just right
- "Light" - could do more
- "Too Light" - easy

#### Body Metrics Tracked:
- Body weight
- Body fat percentage
- Measurements (chest, waist, arms, legs, etc.)
- Progress photos (future consideration)

#### Workout Types:
- **Scheduled:** Part of a program, follows calendar
- **Freestyle/Adhoc:** Pick exercises on the fly, not part of program
- **Missed handling:** Prompt to skip, reschedule, or move to today

#### Program Features:
- User-created and admin-created (shared templates)
- Can be duplicated for variations
- Can be shared between users
- Support true periodization (different exercises per week)
- User-defined body patterns (saved and reusable)

---

## 6. Additional Requirements Confirmed

### 6.1 Exercise Database ✓
- [x] **Master database seeding:** Start empty - no pre-seeded exercises
- [x] **User exercise creation:** Users can add exercises to master database
- [x] **Exercise ownership:** Track who created each exercise
- [x] **Edit permissions:** Admins can edit any exercise, users can only edit their own
- [x] **Category structure:** User-configurable for both programs and lifts (Push/Pull/Legs, Compound/Isolation, equipment-based, etc.)

### 6.2 Program Structure ✓
- [x] **True periodization:** Programs can have different exercises in different weeks
- [x] **Body patterns:** User-defined labels that can be saved and reused (no enforced rotation)
- [x] **Program duplication:** Users can duplicate programs to create variations
- [x] **Program sharing:** Users can share programs between each other

### 6.3 Workout Execution ✓
- [x] **Missed workouts:** Prompt user to skip, reschedule, or move to today
- [x] **Freestyle workouts:** Users can do adhoc workouts, picking lifts as they go
- [x] **Quick templates:** Not by default - users can share their own programs instead

### 6.4 Progressive Overload ✓
- [x] **Gym equipment:** Track available plate sizes and equipment per gym
- [x] **Overload configuration:** When adding lift to gym, specify type (weight plates with specific sizes, numerical weight, time, percentage, etc.)
- [x] **Volume calculation:** Auto-calculate total volume (sets × reps × weight) for reports
- [x] **Tempo format:** Optional field - just lift time and rest time (not complex tempo notation)

### 6.5 UI/UX Preferences ✓
- [x] **Rendering approach:** Server-side with Jinja templates + progressive JavaScript enhancement
- [x] **Navigation:** Bottom nav bar for mobile, sidebar for desktop
- [x] **Framework:** CoreUI Free / Bootstrap 5

### 6.6 Admin Features ✓
- [x] **Data access:** Admin can view all user workouts and data for support
- [x] **Shared templates:** Admin can create shared program templates
- [x] **User management:** Create, delete, reset passwords for users

---

---

## 7. Final Clarifications Needed

### 7.1 Technical Details
- [ ] What Python version? (3.10, 3.11, 3.12?)
- [ ] Database migrations tool? (Flask-Migrate/Alembic recommended)
- [ ] How to create initial admin user? (CLI command, seed script, first-run setup page?)
- [ ] Session management? (Flask-Login recommended, session timeout duration?)

### 7.2 Validation & Rules
- [ ] Min/max values for sets and reps? (e.g., 1-100 sets, 1-500 reps)
- [ ] Exercise name length limits?
- [ ] Program name length limits?
- [ ] Required vs optional fields for exercises?

### 7.3 Search & Filtering
- [ ] Should exercise lists be searchable/filterable?
- [ ] How to handle large lists of exercises in dropdowns?
- [ ] Pagination for workout history?

### 7.4 Program Sharing
- [ ] When a user receives a shared program, is it read-only or can they customize it?
- [ ] If customizable, does it create a copy or modify the original?
- [ ] Can admin programs be edited by users or only copied?

### 7.5 Units & Measurements
- [ ] Weight units preference (lbs, kg, or user choice)?
- [ ] Distance units (miles, km, meters)?
- [ ] Should users be able to set their preferred units?

### 7.6 Additional Features
- [ ] Should there be a dashboard/home page? What should it show?
- [ ] Notifications for scheduled workouts?
- [ ] Rest day tracking in calendar?

---

## 8. Next Immediate Steps

1. Answer final clarifying questions above
2. Create detailed database schema document with all fields and relationships
3. Set up Flask project structure
4. Configure development environment on Digital Ocean VPS
5. Implement Phase 1 (Foundation & Setup)
6. Begin iterative development of remaining phases

