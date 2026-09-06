PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS contacts (
    id                TEXT PRIMARY KEY,
    name              TEXT NOT NULL,
    phone_raw         TEXT NOT NULL,
    phone_e164        TEXT NOT NULL,
    email             TEXT,
    extra_json        TEXT,
    source_file       TEXT,
    is_valid          INTEGER NOT NULL DEFAULT 1,
    validation_error  TEXT,
    created_at        TEXT NOT NULL,
    updated_at        TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_contacts_phone_e164 ON contacts(phone_e164);
CREATE INDEX IF NOT EXISTS idx_contacts_is_valid ON contacts(is_valid);
CREATE INDEX IF NOT EXISTS idx_contacts_name ON contacts(name);

CREATE TABLE IF NOT EXISTS templates (
    id            TEXT PRIMARY KEY,
    name          TEXT NOT NULL UNIQUE,
    body          TEXT NOT NULL,
    created_at    TEXT NOT NULL,
    updated_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS devices (
    id                  TEXT PRIMARY KEY,
    device_name         TEXT NOT NULL,
    last_ip             TEXT,
    pairing_token_ref   TEXT NOT NULL,
    cert_fingerprint    TEXT,
    phone_number        TEXT,
    is_paired           INTEGER NOT NULL DEFAULT 1,
    last_connected_at   TEXT,
    created_at          TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS campaigns (
    id                TEXT PRIMARY KEY,
    name              TEXT NOT NULL,
    campaign_type     TEXT NOT NULL DEFAULT 'SMS',
    template_id       TEXT REFERENCES templates(id) ON DELETE SET NULL,
    message_body      TEXT NOT NULL,
    device_id         TEXT REFERENCES devices(id),
    status            TEXT NOT NULL DEFAULT 'DRAFT',
    auto_paused       INTEGER NOT NULL DEFAULT 0,
    pause_reason      TEXT,
    total_count       INTEGER NOT NULL DEFAULT 0,
    sent_count        INTEGER NOT NULL DEFAULT 0,
    failed_count      INTEGER NOT NULL DEFAULT 0,
    rate_limit_ms     INTEGER NOT NULL DEFAULT 2000,
    daily_limit       INTEGER NOT NULL DEFAULT 100,
    ring_duration_sec INTEGER NOT NULL DEFAULT 15,
    audio_path        TEXT,
    created_at        TEXT NOT NULL,
    updated_at        TEXT NOT NULL,
    completed_at      TEXT
);

CREATE TABLE IF NOT EXISTS messages (
    id                  TEXT PRIMARY KEY,
    campaign_id         TEXT NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    contact_id          TEXT NOT NULL REFERENCES contacts(id),
    phone_e164          TEXT NOT NULL,
    rendered_text       TEXT NOT NULL,
    status              TEXT NOT NULL DEFAULT 'PENDING',
    error               TEXT,
    attempt_count       INTEGER NOT NULL DEFAULT 0,
    dispatched_at       TEXT,
    sent_at             TEXT,
    synced_to_desktop   INTEGER NOT NULL DEFAULT 0,
    created_at          TEXT NOT NULL,
    updated_at          TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_messages_campaign_status ON messages(campaign_id, status);
CREATE INDEX IF NOT EXISTS idx_messages_status ON messages(status);
CREATE UNIQUE INDEX IF NOT EXISTS idx_messages_campaign_contact ON messages(campaign_id, contact_id);
