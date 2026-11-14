-- MemoryOS & The Quiet Advisor Unified SQLite Schema
-- Automatically loaded by src/memoryos/quiet_advisor_db.py and bootstrap.py

CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    active INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS memoryos_inference_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    session_id TEXT,
    timestamp TEXT NOT NULL,
    model_id TEXT NOT NULL,
    context_tokens_provided INTEGER DEFAULT 0,
    context_tokens_used INTEGER DEFAULT 0,
    time_to_first_token_ms REAL DEFAULT 0,
    total_latency_ms REAL DEFAULT 0,
    tokens_per_second REAL DEFAULT 0,
    gpu_id TEXT,
    gpu_utilization_percent REAL DEFAULT 0,
    gpu_temperature_celsius REAL DEFAULT 0,
    gpu_memory_used_mb INTEGER DEFAULT 0,
    output_quality_score REAL,
    error_flag INTEGER DEFAULT 0,
    error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_inference_user_time
    ON memoryos_inference_log(user_id, timestamp);

CREATE TABLE IF NOT EXISTS quiet_advisor_cards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    detector_type TEXT NOT NULL,
    insight_rank REAL DEFAULT 0,
    title TEXT,
    subtitle TEXT,
    description TEXT,
    metric_1 TEXT,
    metric_2 TEXT,
    metric_3 TEXT,
    recommended_action TEXT,
    action_value TEXT,
    time_savings_seconds INTEGER DEFAULT 0,
    quality_improvement_percent REAL DEFAULT 0,
    suggested_experiments TEXT,
    user_dismissed INTEGER DEFAULT 0,
    user_archived INTEGER DEFAULT 0,
    user_actioned INTEGER DEFAULT 0,
    created_at TEXT,
    expires_at TEXT
);

CREATE INDEX IF NOT EXISTS idx_cards_user_active
    ON quiet_advisor_cards(user_id, user_dismissed, user_archived);

CREATE TABLE IF NOT EXISTS quiet_advisor_card_actions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    card_id TEXT NOT NULL,
    action_type TEXT NOT NULL,
    action_result TEXT,
    created_at TEXT
);

CREATE TABLE IF NOT EXISTS quiet_advisor_user_preferences (
    user_id TEXT PRIMARY KEY,
    card_type_preferences TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS kv_store (
    key VARCHAR PRIMARY KEY,
    value VARCHAR,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
