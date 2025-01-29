-- Ensure the toggle_history database exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = 'toggle_history') THEN
        CREATE DATABASE toggle_history;
    END IF;
END $$;

-- Connect to the toggle_history database
\c toggle_history

-- Create the toggle_actions table if it doesn't exist
CREATE TABLE IF NOT EXISTS toggle_actions (
    id SERIAL PRIMARY KEY,
    action VARCHAR(10) NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS comments (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    comment TEXT NOT NULL,
    ip_address VARCHAR(45)
);
