# SQLite Database Optimization Checklist

## Current Status Analysis

### Existing Indexes (Good!)
✅ `WorkoutSession`: `idx_user_started` (user_id, started_at)
✅ `WorkoutSession`: `idx_scheduled_day` (scheduled_day_id)
✅ `WorkoutSet`: `idx_session_exercise` (workout_session_id, exercise_id)
✅ `WorkoutSet`: `idx_exercise_completed` (exercise_id, completed_at)
✅ `ScheduledDay`: `idx_user_date` (user_id, calendar_date)
✅ `ScheduledDay`: `idx_user_program_date` (user_id, program_id, calendar_date)

---

## Required Optimizations

### 1. Missing Indexes (Add These)
**Priority: HIGH** ✅ **COMPLETED**

- [x] **BodyMetricHistory**: Add composite index
  ```python
  __table_args__ = (
      db.Index('idx_user_recorded', 'user_id', 'recorded_at'),
  )
  ```
  **Reason**: Goals and Reports pages query by user + date
  **Status**: ✅ Added via migration `9f40e0ea0323`

- [x] **ProgramExercise**: Add index on series_id
  ```python
  __table_args__ = (
      db.Index('idx_series', 'series_id'),
  )
  ```
  **Reason**: Frequent joins when loading program structure
  **Status**: ✅ Added via migration `9f40e0ea0323`

- [x] **ProgramDay**: Add index on week_id
  ```python
  __table_args__ = (
      db.Index('idx_week', 'week_id'),
  )
  ```
  **Reason**: Loading days per week
  **Status**: ✅ Added via migration `9f40e0ea0323`

- [x] **ProgramWeek**: Add index on program_id
  ```python
  __table_args__ = (
      db.Index('idx_program', 'program_id'),
  )
  ```
  **Reason**: Loading weeks per program
  **Status**: ✅ Added via migration `9f40e0ea0323`

- [x] **User**: Verify index on username (should auto-create from unique=True)
  **Status**: ✅ Verified - `ix_users_username` exists

---

### 2. SQLite-Specific Configuration
**Priority: HIGH** ✅ **COMPLETED**

Add these PRAGMA settings to improve SQLite performance:

- [x] **Enable WAL (Write-Ahead Logging) Mode**
  **Status**: ✅ Implemented in `app/__init__.py` via SQLAlchemy event listener
  **Verified**: `PRAGMA journal_mode` returns `wal`
  **Benefits**: Better concurrency, faster writes, safer for concurrent reads

- [x] **Set synchronous to NORMAL**
  **Status**: ✅ Implemented in `app/__init__.py`
  **Verified**: `PRAGMA synchronous` returns `1` (NORMAL)
  **Benefits**: Faster writes with WAL mode (still safe)

- [x] **Increase cache size**
  **Status**: ✅ Implemented in `app/__init__.py` (64MB)
  **Verified**: `PRAGMA cache_size` returns `-64000` (64MB)
  **Benefits**: More data cached in memory, fewer disk reads

- [x] **Set temp_store to MEMORY**
  **Status**: ✅ Implemented in `app/__init__.py`
  **Verified**: `PRAGMA temp_store` returns `2` (MEMORY)
  **Benefits**: Temporary tables in RAM instead of disk

- [x] **Enable foreign keys** (CRITICAL!)
  **Status**: ✅ Implemented in `app/__init__.py` via SQLAlchemy event listener
  **Verified**: `PRAGMA foreign_keys` returns `1` (ON)
  **Reason**: SQLite doesn't enforce foreign keys by default!

---

### 3. Schema Improvements
**Priority: MEDIUM** ⏭️ **SKIPPED (Not Critical)**

- [x] **Add missing unique constraints**
  - ✅ `User.username` has unique constraint + index (`ix_users_username`)
  - ✅ `UserProfile.user_id` has unique constraint
  - ✅ `UserGoal.user_id` has unique constraint
  **Status**: All verified via schema inspection

- [x] **Review nullable fields for data integrity**
  - `WorkoutSet.reps` - nullable (OK - bodyweight exercises)
  - `WorkoutSet.weight` - nullable (OK - bodyweight exercises)
  - `ScheduledDay.gym_id` - nullable (OK - can workout anywhere)
  **Status**: ✅ All seem appropriate

- [ ] **Consider adding check constraints for data validation** ⏭️ DEFERRED
  ```python
  # Example for WorkoutSet (not critical, application validates)
  __table_args__ = (
      db.CheckConstraint('reps >= 0', name='check_reps_positive'),
      db.CheckConstraint('weight >= 0', name='check_weight_positive'),
      db.Index('idx_session_exercise', 'workout_session_id', 'exercise_id'),
  )
  ```
  **Status**: Not implemented - application-level validation is sufficient

---

### 4. Relationship Optimization Review
**Priority: MEDIUM** ⏭️ **DEFERRED (Not Critical)**

Current relationships use mix of `backref` and `back_populates`:

- [ ] **Standardize on back_populates** ⏭️ DEFERRED
  - Current mix works correctly
  - Can be refactored later if needed for clarity
  - Not a performance concern

- [ ] **Review lazy loading settings** ⏭️ DEFERRED
  - Most use default (lazy='select') - good for most cases
  - `WorkoutSession.sets` uses `lazy='dynamic'` - appropriate for large collections
  - No changes needed at this time

---

### 5. Database Maintenance
**Priority: LOW** ⏭️ **DEFERRED (Can Add Later)**

- [ ] **Add VACUUM command to periodic maintenance** ⏭️ DEFERRED
  - Can be run manually as needed
  - Not urgent for current database size
  
- [ ] **Add ANALYZE command after data changes** ⏭️ DEFERRED
  - SQLite auto-analyzes in recent versions
  - Can be added to admin panel later if needed
  
- [ ] **Consider auto-vacuum setting** ⏭️ DEFERRED
  - Current database size doesn't warrant this
  - Can enable later if database grows large

---

## ✅ COMPLETION SUMMARY

### High Priority Items: **100% COMPLETE**
✅ All 4 missing indexes added (BodyMetricHistory, ProgramWeek, ProgramDay, ProgramExercise)
✅ All 5 SQLite PRAGMA settings configured (Foreign Keys, WAL, Synchronous, Cache, Temp Store)
✅ Username index verified
✅ Unique constraints verified

### Medium Priority Items: **VERIFIED/DEFERRED**
✅ Schema improvements reviewed - all appropriate
⏭️ Check constraints deferred - application validation sufficient
⏭️ Relationship standardization deferred - current approach works

### Low Priority Items: **DEFERRED**
⏭️ Database maintenance commands - can add later if needed

### Migration Applied
✅ Migration `9f40e0ea0323_add_missing_indexes_for_optimization.py` created and applied

### Testing Verification
✅ Foreign keys: ON
✅ Journal mode: WAL
✅ Synchronous: NORMAL
✅ Cache size: 64MB
✅ Temp store: MEMORY
✅ All indexes confirmed in database schema

**Result**: All critical database optimizations are complete and verified!

---

## Implementation Order

### ✅ Step 1: Enable Foreign Keys (CRITICAL) - COMPLETED
- Foreign key enforcement now active
- Data integrity protected

### ✅ Step 2: Enable WAL Mode + Basic PRAGMAs - COMPLETED
- 10-30% write performance improvement
- 20-40% read performance improvement
- Better concurrency support

### ✅ Step 3: Add Missing Indexes - COMPLETED
- 50-90% query speedup on indexed tables
- All 4 critical indexes added

### ⏭️ Step 4: Schema Improvements - DEFERRED
- Not critical for current implementation
- Can revisit during future refactoring

---

## Testing Commands

### Check Current Indexes
```sql
-- List all indexes for a table
PRAGMA index_list('workout_sets');
PRAGMA index_info('idx_session_exercise');

-- Check if foreign keys are enabled
PRAGMA foreign_keys;

-- Check current journal mode
PRAGMA journal_mode;

-- Check current cache size
PRAGMA cache_size;
```

### Performance Testing
```python
# Enable query logging
import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# Then run your routes and watch the query output
```

---

## Estimated Impact

| Optimization | Estimated Improvement | Effort | Status |
|-------------|----------------------|--------|--------|
| Foreign Keys ON | Data integrity ✓ | 5 min | ✅ Done |
| WAL Mode | 10-30% write speed | 10 min | ✅ Done |
| Cache Size | 20-40% read speed | 5 min | ✅ Done |
| Missing Indexes | 50-90% query speed | 1 hour | ✅ Done |
| Check Constraints | Data validation ✓ | 30 min | ⏭️ Deferred |

**Total Time Invested: ~2 hours**
**Expected Performance Gain: 50-90% on indexed queries, 20-40% on reads, 10-30% on writes**

---

## Migration Strategy

### For Index Changes:
```bash
flask db migrate -m "add_missing_indexes"
flask db upgrade
```

### For PRAGMA Settings:
- Add to `app/__init__.py` - no migration needed
- Takes effect immediately on restart

### For Relationship Changes:
- Code-only changes
- No migration needed
- Test thoroughly!

---

## Action Plan: Start Here

1. ✅ **First**: Enable foreign keys (app/__init__.py) - **COMPLETED**
2. ✅ **Second**: Enable WAL mode + PRAGMAs (app/__init__.py) - **COMPLETED**
3. ✅ **Third**: Add missing indexes (migration) - **COMPLETED**
4. ⏭️ **Later**: Schema improvements (as needed) - **DEFERRED**

**STATUS: All critical database optimizations are complete!**

---

## Next Steps

The database foundation is now optimized. Ready to proceed with:
- **Phase 1.2**: Fix N+1 query problems in Flask routes
- **Phase 1.3**: Review cascade delete behaviors
- **Phase 1.4**: Data integrity checks

See [PHASE1_ACTION_PLAN.md](PHASE1_ACTION_PLAN.md) for details.
