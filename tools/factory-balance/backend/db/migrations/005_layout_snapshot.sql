DROP TABLE IF EXISTS layout_compute_history;
DROP TABLE IF EXISTS layout_snapshot;
CREATE TABLE layout_snapshot (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    layout_key          TEXT NOT NULL UNIQUE,
    save_key            TEXT,
    env_key             TEXT,
    catalog_mode        TEXT NOT NULL DEFAULT 'progress',
    supply_mode         TEXT NOT NULL DEFAULT 'raw',
    target_summary      TEXT NOT NULL,
    target_count        INTEGER NOT NULL DEFAULT 0,
    node_count          INTEGER NOT NULL DEFAULT 0,
    edge_count          INTEGER NOT NULL DEFAULT 0,
    tap_count           INTEGER NOT NULL DEFAULT 0,
    request_json        TEXT NOT NULL,
    response_json       TEXT NOT NULL,
    user_positions_json TEXT NOT NULL DEFAULT '{}',
    created_at          TEXT NOT NULL,
    updated_at          TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_layout_snapshot_updated ON layout_snapshot(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_layout_snapshot_save ON layout_snapshot(save_key);
