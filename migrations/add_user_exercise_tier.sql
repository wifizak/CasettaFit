-- Migration: Add user_exercise_tiers table
-- Date: 2026-01-07
-- Description: Allows users to assign personal tier rankings (S, A, B, C, D, F) to exercises

CREATE TABLE IF NOT EXISTS user_exercise_tiers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    exercise_id INTEGER NOT NULL,
    tier VARCHAR(1) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (exercise_id) REFERENCES master_exercises(id) ON DELETE CASCADE,
    CONSTRAINT unique_user_exercise_tier UNIQUE (user_id, exercise_id),
    CHECK (tier IN ('S', 'A', 'B', 'C', 'D', 'F'))
);

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_user_exercise_tiers_user_id ON user_exercise_tiers(user_id);
CREATE INDEX IF NOT EXISTS idx_user_exercise_tiers_exercise_id ON user_exercise_tiers(exercise_id);
CREATE INDEX IF NOT EXISTS idx_user_exercise_tiers_tier ON user_exercise_tiers(tier);
