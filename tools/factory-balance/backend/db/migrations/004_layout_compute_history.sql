CREATE TABLE IF NOT EXISTS layout_compute_history (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    save_key        TEXT,
    env_key         TEXT,
    catalog_mode    TEXT NOT NULL DEFAULT 'progress',
    supply_mode     TEXT NOT NULL DEFAULT 'raw',
    target_summary  TEXT NOT NULL,
    target_count    INTEGER NOT NULL DEFAULT 0,
    node_count      INTEGER NOT NULL DEFAULT 0,
    edge_count      INTEGER NOT NULL DEFAULT 0,
    tap_count       INTEGER NOT NULL DEFAULT 0,
    request_json    TEXT NOT NULL,
    response_json   TEXT NOT NULL,
    created_at      TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_layout_history_created ON layout_compute_history(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_layout_history_save ON layout_compute_history(save_key);
