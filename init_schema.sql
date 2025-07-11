CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    phone_number TEXT NOT NULL,
    verification_code TEXT NOT NULL,
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    tokens_balance INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'UTC')
);

CREATE TABLE IF NOT EXISTS tokens_log (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    change INTEGER NOT NULL,
    source TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT (NOW() AT TIME ZONE 'UTC')
);
