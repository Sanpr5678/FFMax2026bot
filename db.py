CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    uid TEXT NOT NULL, password TEXT, region TEXT, jwt TEXT,
    owner_id INTEGER, created_at INTEGER NOT NULL
);