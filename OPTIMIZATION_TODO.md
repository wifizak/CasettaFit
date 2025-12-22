# CasettaFit Optimization & Review TODO

## Database Optimization

### Indexes & Query Performance
- [ ] Review all query patterns and add missing indexes
  - [ ] Check `WorkoutSet` queries by `workout_session_id` and `exercise_id`
  - [ ] Check `ScheduledDay` queries by `user_id` and `calendar_date`
  - [ ] Check `BodyMetricHistory` queries by `user_id` and `recorded_at`
  - [ ] Review `ProgramExercise` queries with joins
- [ ] Analyze N+1 query problems
  - [ ] Check all template loops that access relationships
  - [ ] Add eager loading where needed (joinedload, selectinload)
- [ ] Review database indexes already defined in models
  - [ ] Ensure composite indexes are in correct order (most selective first)

### Data Integrity
- [ ] Add foreign key constraints validation
- [ ] Review cascade delete behaviors
  - [ ] Ensure orphaned records are properly cleaned up
  - [ ] Verify cascade='all, delete-orphan' is correct on all relationships
- [ ] Add database-level unique constraints where needed
- [ ] Review nullable vs non-nullable fields for data consistency

### Schema Review
- [ ] Check for redundant data storage
- [ ] Review if computed fields should be stored or calculated
- [ ] Ensure proper use of relationship back_populates vs backref

---

## Flask Routes Optimization

### Query Efficiency
- [ ] **Dashboard** (`main.index`)
  - [ ] Review all queries - currently loads multiple relationships
  - [ ] Consider aggregation at database level
  - [ ] Cache recent workout data
- [ ] **Calendar** (`calendar.index`)
  - [ ] Optimize scheduled days query with date range
  - [ ] Eager load program_day and program relationships
- [ ] **History** (`history.index`)
  - [ ] Review program history API endpoint
  - [ ] Optimize exercise history queries with pagination
- [ ] **Reports** (`reports.index`)
  - [ ] Heavy aggregation queries - consider caching
  - [ ] Review top exercises query performance
  - [ ] Optimize progressive overload calculations
- [ ] **Workout Execution** (`workout.execute`)
  - [ ] Check for N+1 when loading program structure
  - [ ] Optimize exercise history lookups

### Route Organization
- [ ] Review route naming consistency
- [ ] Check for duplicate logic across routes
- [ ] Ensure proper use of blueprints
- [ ] Review error handling consistency

### Authentication & Security
- [ ] Verify all routes have proper @login_required decorator
- [ ] Check admin routes have @admin_required
- [ ] Review permission checks (user can only access own data)
- [ ] Verify CSRF protection on all forms
- [ ] Check file upload security (size limits, file type validation)

### Form Handling
- [ ] Review form validation rules
- [ ] Check for inconsistent error messages
- [ ] Ensure all forms have proper CSRF tokens
- [ ] Review file upload forms for security

---

## Template (HTML/JS) Optimization

### Page Load Performance
- [ ] **Base Template**
  - [ ] Check if CoreUI CSS/JS can be minified or bundled
  - [ ] Review custom CSS for redundancy
  - [ ] Optimize avatar display logic
- [ ] **Exercise Library**
  - [ ] Review search/filter JavaScript efficiency
  - [ ] Check if autocomplete loads too much data at once
  - [ ] Consider pagination for large lists
- [ ] **Equipment Library**
  - [ ] Same as exercise library - review filtering
  - [ ] Check manufacturer/model autocomplete performance
- [ ] **Calendar View**
  - [ ] Review if loading entire month at once is efficient
  - [ ] Check drag-and-drop performance
- [ ] **Workout Execution**
  - [ ] Review set tracking JavaScript for efficiency
  - [ ] Check if auto-save functionality works smoothly
  - [ ] Optimize history modal loading

### JavaScript Organization
- [ ] Review inline JavaScript vs separate files
- [ ] Check for duplicate JavaScript functions across templates
- [ ] Consider creating shared JS utilities file
- [ ] Review fetch API error handling consistency

### User Experience
- [ ] Check loading indicators on all AJAX requests
- [ ] Verify form submission feedback (success/error messages)
- [ ] Test mobile responsiveness on all pages
- [ ] Review mobile bottom navigation completeness

### Forms & Validation
- [ ] Client-side validation consistency
- [ ] Check placeholder text helpfulness
- [ ] Review form field organization
- [ ] Test autocomplete functionality across browsers

---

## Code Quality & Maintainability

### Python Code
- [ ] Review function/method naming conventions
- [ ] Check for code duplication (DRY principle)
- [ ] Add docstrings to complex functions
- [ ] Review error handling (try/except blocks)
- [ ] Type hints for better IDE support

### Models
- [ ] Review relationship definitions for clarity
- [ ] Check __repr__ methods are useful for debugging
- [ ] Ensure model property methods are efficient
- [ ] Review if any business logic should be in models vs routes

### Forms
- [ ] Check for duplicate form field definitions
- [ ] Review validation logic consistency
- [ ] Consider form inheritance for similar forms

### Templates
- [ ] Review template inheritance structure
- [ ] Check for duplicate template blocks
- [ ] Consider creating reusable template macros
- [ ] Review consistent use of CoreUI classes

---

## Feature Completeness & Bug Fixes

### Missing Functionality
- [ ] **Program Editing**
  - [ ] Test if changing `days_per_week` updates existing structure
  - [ ] Verify duration changes don't break scheduled instances
- [ ] **Equipment Management**
  - [ ] Test equipment deletion with exercises using it
  - [ ] Verify gym-equipment associations are cleaned up properly
- [ ] **Exercise Management**
  - [ ] Test exercise deletion with workout history
  - [ ] Verify YouTube URL validation
- [ ] **Goals System**
  - [ ] Test with no profile data
  - [ ] Verify BMI calculation if added
  - [ ] Test chart rendering with missing data

### Known Issues to Check
- [ ] Program instance completion calculation (currently manual)
- [ ] Workout streak calculation accuracy
- [ ] Time zone handling for scheduled dates
- [ ] Profile picture upload size limits
- [ ] File cleanup when users/items deleted

### Testing Checklist
- [ ] Test all forms with invalid data
- [ ] Test permissions (non-admin trying admin routes)
- [ ] Test with multiple users simultaneously
- [ ] Test cascade deletes thoroughly
- [ ] Test file uploads with various formats/sizes

---

## Performance Monitoring

### Add Monitoring
- [ ] Consider adding query logging in development
- [ ] Add timing logs for slow routes
- [ ] Monitor database connection pool usage
- [ ] Track file upload sizes and cleanup

### Optimization Priorities
1. **High Priority** - Routes used most frequently (dashboard, calendar, workout execution)
2. **Medium Priority** - Reports and analytics (can have slight delay)
3. **Low Priority** - Admin routes (used less frequently)

---

## Documentation Needs

### For Developers
- [ ] Document database schema relationships
- [ ] Add comments to complex query logic
- [ ] Document API endpoints (if any)
- [ ] Create setup instructions for new developers

### For Users
- [ ] Consider adding help tooltips
- [ ] Add user guide for key features
- [ ] Document RPE system explanation
- [ ] Add FAQ for common questions

---

## Future Considerations

### Scalability
- [ ] Consider if SQLite will scale (vs PostgreSQL)
- [ ] Review if static file serving should move to CDN
- [ ] Consider caching strategy (Redis?)
- [ ] Review if background jobs needed (Celery?)

### Features to Consider
- [ ] Export workout data (CSV, PDF)
- [ ] Import workout data
- [ ] Exercise demonstration videos/GIFs
- [ ] Social features (share programs, compare stats)
- [ ] Mobile app considerations
- [ ] REST API for third-party integrations

---

## Priority Order

### Phase 1: Critical (Do First)
1. Database query optimization (N+1 problems)
2. Security review (permissions, file uploads)
3. Bug fixes in core features

### Phase 2: Important (Do Second)  
1. Template performance optimization
2. Code organization and DRY improvements
3. User experience polish

### Phase 3: Nice to Have (Do Later)
1. Documentation improvements
2. Additional monitoring
3. Future feature planning

---

## Notes
- Start with database optimization as it has the most impact
- Test changes in development before deploying
- Keep track of performance improvements (before/after metrics)
- Consider user feedback for prioritization
