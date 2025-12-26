-- Enable foreign keys (SQLite requirement)
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL CHECK(length(username) >= 3),
    password_hash TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL CHECK(email LIKE '%@%.%'),
    full_name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'doctor' CHECK(role IN ('doctor', 'admin', 'student', 'researcher')),
    institution TEXT,
    license_number TEXT,
    specialty TEXT,
    phone TEXT,
    country TEXT DEFAULT 'US',
    language TEXT DEFAULT 'en',
    timezone TEXT DEFAULT 'UTC',
    avatar_url TEXT,
    bio TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    last_activity TIMESTAMP,
    login_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT 1,
    is_verified BOOLEAN DEFAULT 0,
    must_accept_disclaimer BOOLEAN DEFAULT 1,
    preferences TEXT,
    notification_settings TEXT
);


CREATE TABLE IF NOT EXISTS consultations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    session_id TEXT NOT NULL,
    query TEXT NOT NULL CHECK(length(query) > 0),
    query_language TEXT DEFAULT 'en',
    symptoms_detected TEXT,
    symptom_count INTEGER DEFAULT 0,
    response TEXT NOT NULL,
    differential_diagnosis TEXT,
    top_diagnosis TEXT NOT NULL,
    top_probability REAL,
    confidence_score REAL CHECK(confidence_score BETWEEN 0 AND 1),
    confidence_level TEXT CHECK(confidence_level IN ('HIGH', 'MODERATE', 'LOW', 'VERY LOW')),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    duration_ms INTEGER,
    consultation_type TEXT DEFAULT 'diagnostic' CHECK(consultation_type IN ('diagnostic', 'follow_up', 'review', 'research')),
    is_urgent BOOLEAN DEFAULT 0,
    is_critical BOOLEAN DEFAULT 0,
    urgency_score INTEGER DEFAULT 0,
    is_bookmarked BOOLEAN DEFAULT 0,
    is_shared BOOLEAN DEFAULT 0,
    tags TEXT,
    notes TEXT,
    follow_up_date TIMESTAMP,
    status TEXT DEFAULT 'completed' CHECK(status IN ('completed', 'in_progress', 'reviewed', 'archived')),
    ip_address TEXT,
    user_agent TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    username TEXT,
    action TEXT NOT NULL,
    action_category TEXT,
    resource_type TEXT,
    resource_id INTEGER,
    details TEXT,
    severity TEXT DEFAULT 'info' CHECK(severity IN ('debug', 'info', 'warning', 'error', 'critical')),
    ip_address TEXT,
    user_agent TEXT,
    request_method TEXT,
    request_path TEXT,
    response_code INTEGER,
    execution_time_ms INTEGER,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    session_id TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);


CREATE TABLE IF NOT EXISTS disclaimer_acceptances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    version TEXT NOT NULL DEFAULT '2.0',
    accepted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address TEXT,
    user_agent TEXT,
    language TEXT DEFAULT 'en',
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS system_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    metric_name TEXT NOT NULL,
    metric_value REAL,
    metric_unit TEXT,
    metric_category TEXT,
    metadata TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    aggregation_period TEXT,
    node_id TEXT
);


CREATE TABLE IF NOT EXISTS favorites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    consultation_id INTEGER NOT NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (consultation_id) REFERENCES consultations(id) ON DELETE CASCADE,
    UNIQUE(user_id, consultation_id)
);


CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    consultation_id INTEGER,
    rating INTEGER CHECK(rating BETWEEN 1 AND 5),
    accuracy_rating INTEGER CHECK(accuracy_rating BETWEEN 1 AND 5),
    usefulness_rating INTEGER CHECK(usefulness_rating BETWEEN 1 AND 5),
    comment TEXT,
    actual_diagnosis TEXT,            -- What it actually was
    feedback_type TEXT DEFAULT 'general' CHECK(feedback_type IN ('general', 'accuracy', 'bug', 'feature')),
    status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'reviewed', 'resolved')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMP,
    reviewed_by INTEGER,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (consultation_id) REFERENCES consultations(id) ON DELETE SET NULL,
    FOREIGN KEY (reviewed_by) REFERENCES users(id) ON DELETE SET NULL
);


CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    notification_type TEXT DEFAULT 'info' CHECK(notification_type IN ('info', 'warning', 'success', 'error')),
    is_read BOOLEAN DEFAULT 0,
    link TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    read_at TIMESTAMP,
    expires_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS user_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    session_id TEXT UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    ip_address TEXT,
    user_agent TEXT,
    is_active BOOLEAN DEFAULT 1,
    device_type TEXT,
    browser TEXT,
    os TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);


CREATE TABLE IF NOT EXISTS diagnosis_corrections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    consultation_id INTEGER NOT NULL,
    predicted_diagnosis TEXT NOT NULL,
    actual_diagnosis TEXT NOT NULL,
    corrected_by INTEGER NOT NULL,
    correction_notes TEXT,
    confidence_was REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (consultation_id) REFERENCES consultations(id) ON DELETE CASCADE,
    FOREIGN KEY (corrected_by) REFERENCES users(id) ON DELETE CASCADE
);


CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active);
CREATE INDEX IF NOT EXISTS idx_users_last_login ON users(last_login DESC);

CREATE INDEX IF NOT EXISTS idx_consultations_user ON consultations(user_id);
CREATE INDEX IF NOT EXISTS idx_consultations_timestamp ON consultations(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_consultations_user_timestamp ON consultations(user_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_consultations_diagnosis ON consultations(top_diagnosis);
CREATE INDEX IF NOT EXISTS idx_consultations_urgent ON consultations(is_urgent) WHERE is_urgent = 1;
CREATE INDEX IF NOT EXISTS idx_consultations_critical ON consultations(is_critical) WHERE is_critical = 1;
CREATE INDEX IF NOT EXISTS idx_consultations_bookmarked ON consultations(user_id, is_bookmarked) WHERE is_bookmarked = 1;
CREATE INDEX IF NOT EXISTS idx_consultations_status ON consultations(status);

CREATE INDEX IF NOT EXISTS idx_audit_user ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_action ON audit_log(action);
CREATE INDEX IF NOT EXISTS idx_audit_severity ON audit_log(severity);
CREATE INDEX IF NOT EXISTS idx_audit_user_action ON audit_log(user_id, action, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_favorites_user ON favorites(user_id);
CREATE INDEX IF NOT EXISTS idx_favorites_consultation ON favorites(consultation_id);

CREATE INDEX IF NOT EXISTS idx_feedback_user ON feedback(user_id);
CREATE INDEX IF NOT EXISTS idx_feedback_consultation ON feedback(consultation_id);
CREATE INDEX IF NOT EXISTS idx_feedback_status ON feedback(status);

CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_unread ON notifications(user_id, is_read) WHERE is_read = 0;

CREATE INDEX IF NOT EXISTS idx_sessions_user ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_session_id ON user_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_sessions_active ON user_sessions(is_active) WHERE is_active = 1;


CREATE VIEW IF NOT EXISTS v_user_statistics AS
SELECT
    u.id,
    u.username,
    u.full_name,
    COUNT(DISTINCT c.id) as total_consultations,
    COUNT(DISTINCT CASE WHEN c.timestamp >= datetime('now', '-7 days') THEN c.id END) as consultations_last_7_days,
    COUNT(DISTINCT CASE WHEN c.timestamp >= datetime('now', '-30 days') THEN c.id END) as consultations_last_30_days,
    COUNT(DISTINCT CASE WHEN c.is_urgent = 1 THEN c.id END) as urgent_consultations,
    AVG(c.confidence_score) as avg_confidence,
    MAX(c.timestamp) as last_consultation,
    u.created_at as member_since,
    u.last_login
FROM users u
LEFT JOIN consultations c ON u.id = c.user_id
GROUP BY u.id;

CREATE VIEW IF NOT EXISTS v_popular_diagnoses AS
SELECT
    top_diagnosis,
    COUNT(*) as frequency,
    AVG(confidence_score) as avg_confidence,
    COUNT(DISTINCT user_id) as unique_users,
    COUNT(CASE WHEN is_urgent = 1 THEN 1 END) as urgent_count,
    MAX(timestamp) as last_diagnosed
FROM consultations
GROUP BY top_diagnosis
ORDER BY frequency DESC;

CREATE VIEW IF NOT EXISTS v_system_activity AS
SELECT
    DATE(timestamp) as date,
    COUNT(*) as total_consultations,
    COUNT(DISTINCT user_id) as active_users,
    AVG(duration_ms) as avg_duration_ms,
    COUNT(CASE WHEN is_urgent = 1 THEN 1 END) as urgent_cases,
    AVG(confidence_score) as avg_confidence
FROM consultations
GROUP BY DATE(timestamp)
ORDER BY date DESC;


CREATE TRIGGER IF NOT EXISTS update_user_timestamp
AFTER UPDATE ON users
FOR EACH ROW
BEGIN
    UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
END;

CREATE TRIGGER IF NOT EXISTS update_user_activity
AFTER INSERT ON consultations
FOR EACH ROW
BEGIN
    UPDATE users SET last_activity = CURRENT_TIMESTAMP WHERE id = NEW.user_id;
END;

CREATE TRIGGER IF NOT EXISTS increment_login_count
AFTER UPDATE OF last_login ON users
FOR EACH ROW
WHEN NEW.last_login > OLD.last_login
BEGIN
    UPDATE users SET login_count = login_count + 1 WHERE id = OLD.id;
END;

CREATE TRIGGER IF NOT EXISTS archive_expired_sessions
AFTER INSERT ON user_sessions
FOR EACH ROW
BEGIN
    UPDATE user_sessions
    SET is_active = 0
    WHERE user_id = NEW.user_id
    AND id != NEW.id
    AND expires_at < CURRENT_TIMESTAMP;
END;


INSERT OR IGNORE INTO users (
    id, username, password_hash, email, full_name, role, institution,
    is_active, must_accept_disclaimer, is_verified
) VALUES (
    1,
    'admin',
    'scrypt:32768:8:1$jOKE9vYGWH4xgYLR$c8f9c0e4e8b5d8a9c5f3e7b2d6a4f8e3c9b7d5a2e6f4c8b3d7a5e9f2c6b4d8a7e5c3f9b2d6a8e4c7f5b3d9a6e2c8f4b7d5a3e9c6f2b8d4a7e5c3f9b6d2a8e4c7f5b3d9a6e2c8f4b7d5a3e9c6f2b8',
    'admin@cdss.local',
    'System Administrator',
    'admin',
    'CDSS System',
    1,
    0,
    1
);


ALTER TABLE consultations ADD COLUMN vitals_data TEXT;

ALTER TABLE consultations ADD COLUMN risk_scores_data TEXT;


CREATE TABLE IF NOT EXISTS consultations_v2 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    session_id TEXT NOT NULL,
    query TEXT NOT NULL CHECK(length(query) > 0),
    symptoms_detected TEXT,
    symptom_count INTEGER DEFAULT 0,
    response TEXT NOT NULL,
    differential_diagnosis TEXT,
    top_diagnosis TEXT NOT NULL,
    top_probability REAL,
    confidence_score REAL CHECK(confidence_score BETWEEN 0 AND 1),
    confidence_level TEXT CHECK(confidence_level IN ('HIGH', 'MODERATE', 'LOW', 'VERY LOW')),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    duration_ms INTEGER,
    is_urgent BOOLEAN DEFAULT 0,
    is_critical BOOLEAN DEFAULT 0,
    urgency_score INTEGER DEFAULT 0,
    vitals_data TEXT,              -- NEW: JSON vitals analysis
    risk_scores_data TEXT,         -- NEW: JSON risk scores
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);


CREATE INDEX IF NOT EXISTS idx_consultations_v2_user ON consultations_v2(user_id);
CREATE INDEX IF NOT EXISTS idx_consultations_v2_timestamp ON consultations_v2(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_consultations_v2_critical ON consultations_v2(is_critical) WHERE is_critical = 1;
