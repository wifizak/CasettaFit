# Cascade Delete Behavior Analysis

## Overview
This document analyzes all cascade delete behaviors in the CasettaFit application to ensure data integrity and proper cleanup when parent records are deleted.

---

## 1. User Deletion Cascade

### Current Behavior:
✅ **UserProfile** - `cascade='all, delete-orphan'` (Line 24)
- When User is deleted → UserProfile is deleted
- **Status:** CORRECT

### Missing Cascades (No explicit cascade defined):
⚠️ **BodyMetricHistory** - ForeignKey('users.id') at Line 75
- No cascade defined on User model
- **Expected:** Should delete when user is deleted
- **Action:** Add relationship to User model

⚠️ **UserGoal** - ForeignKey('users.id') at Line 106
- No cascade defined on User model
- **Expected:** Should delete when user is deleted
- **Action:** Add relationship to User model

⚠️ **MasterExercise** - ForeignKey('users.id', nullable=True) at Line 204
- No cascade defined on User model
- User-created exercises
- **Expected:** Should SET NULL or prevent deletion if exercises exist
- **Action:** Add relationship to User model

⚠️ **UserGym** - ForeignKey('users.id') at Line 226
- No cascade defined on User model
- **Expected:** Should delete when user is deleted
- **Action:** Add relationship to User model

⚠️ **ProgramInstance** - ForeignKey('users.id') at Line 598
- No cascade defined on User model
- **Expected:** Should delete when user is deleted
- **Action:** Add relationship to User model

⚠️ **WorkoutSession** - ForeignKey('users.id') at Line 639
- No cascade defined on User model
- **Expected:** Should delete when user is deleted
- **Action:** Add relationship to User model

⚠️ **ScheduledDay** - ForeignKey('users.id') at Line 699
- No cascade defined on User model (has user_id but no direct relationship from User)
- **Expected:** Should delete when user is deleted
- **Action:** Add relationship to User model

---

## 2. Program Deletion Cascade

### Current Behavior:
✅ **ProgramWeek** - `cascade='all, delete-orphan'` (Line 392)
- When Program deleted → All weeks deleted
- **Status:** CORRECT

✅ **ProgramDay** - `cascade='all, delete-orphan'` (Line 426)
- When ProgramWeek deleted → All days deleted
- **Status:** CORRECT

✅ **ProgramSeries** - `cascade='all, delete-orphan'` (Line 449)
- When ProgramDay deleted → All series deleted
- **Status:** CORRECT

✅ **ProgramExercise** - `cascade='all, delete-orphan'` (Line 472)
- When ProgramSeries deleted → All exercises deleted
- **Status:** CORRECT

✅ **ProgramShare** - `cascade='all, delete-orphan'` (Line 393)
- When Program deleted → All shares deleted
- **Status:** CORRECT

### Potential Issue:
⚠️ **ProgramInstance** - Has ForeignKey to Program
- What happens when Program is deleted but instances exist?
- **Current:** Likely raises IntegrityError (FK constraint)
- **Options:**
  1. Prevent deletion if instances exist (safest)
  2. CASCADE delete (loses workout history)
  3. SET NULL (breaks referential integrity)
- **Recommendation:** Prevent deletion or add soft delete flag

⚠️ **ScheduledDay** - Has ForeignKey to Program
- Similar issue to ProgramInstance
- **Recommendation:** Prevent deletion if scheduled days exist

---

## 3. Gym Deletion Cascade

### Current Behavior:
✅ **GymEquipment** - `cascade='all, delete-orphan'` (Line 234)
- When UserGym deleted → Equipment deleted
- **Status:** CORRECT

✅ **GymExercise** - `cascade='all, delete-orphan'` (Line 235)
- When UserGym deleted → Exercises deleted
- **Status:** CORRECT

### Potential Issues:
⚠️ **EquipmentVariation** has ForeignKey to GymEquipment
✅ Already handled via cascade from GymEquipment (Line 280)
- **Status:** CORRECT

⚠️ **ProgramInstance.gym_id** - ForeignKey to UserGym (nullable=True)
- What happens when gym is deleted?
- **Current:** Likely SET NULL behavior
- **Recommendation:** SET NULL is appropriate (workout can continue without gym)

⚠️ **ScheduledDay.gym_id** - ForeignKey to UserGym (nullable=True)
- What happens when gym is deleted?
- **Current:** Likely SET NULL behavior
- **Recommendation:** SET NULL is appropriate

⚠️ **WorkoutSession.gym_id** - ForeignKey to UserGym (nullable=True)
- What happens when gym is deleted?
- **Current:** Likely SET NULL behavior
- **Recommendation:** SET NULL is appropriate (historical record)

---

## 4. Exercise Deletion Cascade

### Potential Issues:
⚠️ **ProgramExercise.exercise_id** - ForeignKey to MasterExercise
- What happens when MasterExercise is deleted?
- **Current:** Likely raises IntegrityError
- **Recommendation:** Prevent deletion if exercise is used in programs

⚠️ **WorkoutSet.exercise_id** - ForeignKey to MasterExercise
- What happens when MasterExercise is deleted?
- **Current:** Likely raises IntegrityError
- **Recommendation:** Prevent deletion if exercise has workout history

---

## 5. ProgramInstance Deletion Cascade

### Current Behavior:
✅ **ScheduledDay** - `cascade='all, delete-orphan'` (Line 608)
- When ProgramInstance deleted → Scheduled days deleted
- **Status:** CORRECT

✅ **InstanceExerciseWeight** - `cascade='all, delete-orphan'` (Line 609)
- When ProgramInstance deleted → Custom weights deleted
- **Status:** CORRECT

---

## 6. WorkoutSession Deletion Cascade

### Current Behavior:
✅ **WorkoutSet** - `cascade='all, delete-orphan'` (Line 652)
- When WorkoutSession deleted → All sets deleted
- **Status:** CORRECT

---

## Recommendations Summary

### CRITICAL - Add Missing User Cascades:
1. Add relationships to User model for:
   - BodyMetricHistory (cascade delete)
   - UserGoal (cascade delete)
   - UserGym (cascade delete)
   - ProgramInstance (cascade delete)
   - WorkoutSession (cascade delete)
   - ScheduledDay (cascade delete)
   - MasterExercise (SET NULL or prevent deletion)

### HIGH - Prevent Dangerous Deletions:
1. Prevent Program deletion if:
   - ProgramInstances exist
   - ScheduledDays exist
   
2. Prevent MasterExercise deletion if:
   - Used in ProgramExercise
   - Used in WorkoutSet

### MEDIUM - Verify SET NULL Behaviors:
1. Confirm gym_id columns properly handle SET NULL:
   - ProgramInstance.gym_id
   - ScheduledDay.gym_id
   - WorkoutSession.gym_id

### Testing Required:
- Test User deletion (should cascade properly after fixes)
- Test Program deletion with active instances (should be prevented)
- Test Gym deletion (should SET NULL references)
- Test Exercise deletion with usage (should be prevented)

---

## Implementation Priority

1. **IMMEDIATE:** Add User model relationships (data loss risk!)
2. **HIGH:** Add deletion prevention for Program/Exercise
3. **MEDIUM:** Add explicit ondelete='SET NULL' for gym_id foreign keys
4. **LOW:** Add soft delete flags for Programs/Exercises (future enhancement)
