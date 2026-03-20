-- Nukus-Mangit Bot: PostgreSQL Migration Script
-- Ishlatish: psql -U bot_user -d nukus_mangit_db -f migrations.sql

CREATE TABLE IF NOT EXISTS users (
    user_id     BIGINT PRIMARY KEY,
    full_name   VARCHAR(100) NOT NULL,
    phone       VARCHAR(20),
    role        VARCHAR(20),
    is_banned   BOOLEAN NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS announcements (
    id                SERIAL PRIMARY KEY,
    user_id           BIGINT NOT NULL REFERENCES users(user_id),
    direction         VARCHAR(20) NOT NULL,
    passengers_count  SMALLINT NOT NULL,
    price             VARCHAR(50) NOT NULL,
    note              TEXT,
    location_lat      FLOAT,
    location_lon      FLOAT,
    channel_msg_id    BIGINT,
    status            VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at        TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ratings (
    id            SERIAL PRIMARY KEY,
    driver_id     BIGINT NOT NULL REFERENCES users(user_id),
    passenger_id  BIGINT NOT NULL REFERENCES users(user_id),
    score         SMALLINT NOT NULL CHECK (score BETWEEN 1 AND 5),
    comment       TEXT,
    created_at    TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indekslar
CREATE INDEX IF NOT EXISTS idx_announcements_user_id ON announcements(user_id);
CREATE INDEX IF NOT EXISTS idx_announcements_status ON announcements(status);
CREATE INDEX IF NOT EXISTS idx_announcements_created_at ON announcements(created_at);
CREATE INDEX IF NOT EXISTS idx_ratings_driver_id ON ratings(driver_id);
