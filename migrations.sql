-- Nukus-Mangit Bot: PostgreSQL Migration Script v2
-- Ishlatish: psql -U bot_user -d nukus_mangit_db -f migrations.sql

-- ===================== ASOSIY JADVALLAR =====================

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

-- ===================== YANGI JADVALLAR v2 =====================

CREATE TABLE IF NOT EXISTS admins (
    id          SERIAL PRIMARY KEY,
    user_id     BIGINT NOT NULL UNIQUE REFERENCES users(user_id),
    role        VARCHAR(20) NOT NULL DEFAULT 'admin',
    added_by    BIGINT REFERENCES users(user_id),
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS bot_settings (
    key         VARCHAR(100) PRIMARY KEY,
    value       TEXT NOT NULL,
    description VARCHAR(255),
    updated_by  BIGINT REFERENCES users(user_id),
    updated_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS system_logs (
    id          SERIAL PRIMARY KEY,
    user_id     BIGINT REFERENCES users(user_id),
    action      VARCHAR(100) NOT NULL,
    details     TEXT,
    created_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS complaints (
    id              SERIAL PRIMARY KEY,
    from_user_id    BIGINT NOT NULL REFERENCES users(user_id),
    against_user_id BIGINT NOT NULL REFERENCES users(user_id),
    ann_id          BIGINT REFERENCES announcements(id),
    text            TEXT NOT NULL,
    status          VARCHAR(20) NOT NULL DEFAULT 'open',
    reviewed_by     BIGINT REFERENCES users(user_id),
    created_at      TIMESTAMP NOT NULL DEFAULT NOW()
);

-- ===================== INDEKSLAR =====================

CREATE INDEX IF NOT EXISTS idx_announcements_user_id ON announcements(user_id);
CREATE INDEX IF NOT EXISTS idx_announcements_status  ON announcements(status);
CREATE INDEX IF NOT EXISTS idx_announcements_created ON announcements(created_at);
CREATE INDEX IF NOT EXISTS idx_ratings_driver_id     ON ratings(driver_id);
CREATE INDEX IF NOT EXISTS idx_admins_user_id        ON admins(user_id);
CREATE INDEX IF NOT EXISTS idx_admins_role           ON admins(role);
CREATE INDEX IF NOT EXISTS idx_system_logs_created   ON system_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_complaints_status     ON complaints(status);
CREATE INDEX IF NOT EXISTS idx_complaints_against    ON complaints(against_user_id);

-- ===================== DEFAULT SOZLAMALAR =====================

INSERT INTO bot_settings (key, value, description) VALUES
    ('welcome_message',    'Nukus-Mangit Taksi Hamrohi botiga xush kelibsiz!', 'Boshlangich xabar'),
    ('max_active_anns',    '1',    'Bir foydalanuvchi uchun max faol elon'),
    ('ann_expire_hours',   '24',   'Elon muddati soat'),
    ('driver_check_min',   '1',    'Haydovchiga sorov daqiqa'),
    ('passenger_check_min','30',   'Yolovchiga sorov daqiqa'),
    ('bot_active',         'true', 'Bot faolmi')
ON CONFLICT (key) DO NOTHING;
